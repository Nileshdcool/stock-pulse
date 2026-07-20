import asyncio
import logging
from datetime import UTC, datetime

from fastapi import APIRouter, HTTPException, Request

from app.models import SourceLink, SummaryResponse, normalize_symbol
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
        400: {"description": "Invalid symbol"},
        404: {"description": "No news found"},
        502: {"description": "Upstream news or AI failure"},
    },
)
async def stock_summary(symbol: str, request: Request) -> SummaryResponse:
    try:
        normalized = normalize_symbol(symbol)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    cache = request.app.state.cache
    cache_key = f"summary:{normalized}"
    cached = cache.get(cache_key)
    if cached is not None:
        return cached.model_copy(update={"cached": True})

    news_service = request.app.state.news_service
    summary_service = request.app.state.summary_service

    try:
        news, profile = await asyncio.gather(
            news_service.fetch_company_news(normalized),
            news_service.fetch_company_profile(normalized),
        )
    except NewsServiceError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    if not news:
        raise HTTPException(
            status_code=404,
            detail=f"No recent news found for {normalized}. Try another symbol.",
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
        generated_at=datetime.now(tz=UTC),
        cached=False,
    )
    cache.set(cache_key, response)
    logger.info("Generated summary for %s (%s sources)", normalized, len(news))
    return response
