import asyncio
import logging
from datetime import UTC, datetime

from fastapi import APIRouter, HTTPException, Query, Request

from app.models import (
    DEFAULT_PERIOD,
    NewsPeriod,
    SourceLink,
    SummaryResponse,
    normalize_period,
    normalize_symbol,
    period_days,
    period_news_limit,
)
from app.services.news import NewsServiceError
from app.services.summary import SummaryServiceError

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@router.get(
    "/api/stocks/{symbol}/summary",
    response_model=SummaryResponse,
    responses={
        400: {"description": "Invalid symbol or period"},
        404: {"description": "No news found"},
        502: {"description": "Upstream news or AI failure"},
    },
)
async def stock_summary(
    symbol: str,
    request: Request,
    period: str = Query(
        default=DEFAULT_PERIOD,
        description="News lookback window: 1d, 7d, or 30d",
    ),
) -> SummaryResponse:
    try:
        normalized = normalize_symbol(symbol)
        normalized_period: NewsPeriod = normalize_period(period)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    cache = request.app.state.cache
    cache_key = f"summary:{normalized}:{normalized_period}"
    cached = cache.get(cache_key)
    if cached is not None:
        return cached.model_copy(update={"cached": True})

    news_service = request.app.state.news_service
    summary_service = request.app.state.summary_service
    days = period_days(normalized_period)
    limit = period_news_limit(normalized_period)

    try:
        news, profile = await asyncio.gather(
            news_service.fetch_company_news(normalized, days=days, limit=limit),
            news_service.fetch_company_profile(normalized),
        )
    except NewsServiceError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    if not news:
        raise HTTPException(
            status_code=404,
            detail=(
                f"No news found for {normalized} in the last {normalized_period}. "
                "Try a longer period or another symbol."
            ),
        )

    try:
        summary_text, bullets = await summary_service.summarize(normalized, news)
    except SummaryServiceError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    response = SummaryResponse(
        symbol=normalized,
        company_name=profile.name if profile else None,
        logo_url=profile.logo_url if profile else None,
        summary=summary_text,
        bullets=bullets,
        sources=[
            SourceLink(
                title=item.title,
                url=item.url,
                source=item.source,
                published_at=item.published_at,
                related_symbols=item.related_symbols,
            )
            for item in news
        ],
        period=normalized_period,
        generated_at=datetime.now(tz=UTC),
        cached=False,
    )
    cache.set(cache_key, response)
    logger.info(
        "Generated summary for %s period=%s (%s sources)",
        normalized,
        normalized_period,
        len(news),
    )
    return response
