import logging
from datetime import UTC, datetime, timedelta

import httpx
from pydantic import BaseModel

from app.models import NewsItem

logger = logging.getLogger(__name__)

FINNHUB_NEWS_URL = "https://finnhub.io/api/v1/company-news"
FINNHUB_PROFILE_URL = "https://finnhub.io/api/v1/stock/profile2"


class NewsServiceError(Exception):
    """Raised when Finnhub cannot be reached or returns an unexpected payload."""


class CompanyProfile(BaseModel):
    name: str | None = None
    logo_url: str | None = None


def _parse_published_at(timestamp: int | None) -> datetime | None:
    if timestamp is None:
        return None
    try:
        return datetime.fromtimestamp(timestamp, tz=UTC)
    except (OverflowError, OSError, ValueError):
        return None


def parse_related_symbols(raw: object) -> list[str]:
    """Parse Finnhub's comma-separated `related` ticker field into unique symbols."""
    if not isinstance(raw, str) or not raw.strip():
        return []

    symbols: list[str] = []
    seen: set[str] = set()
    for part in raw.replace(";", ",").split(","):
        symbol = part.strip().upper()
        if not symbol or symbol in seen:
            continue
        cleaned = symbol.replace(".", "").replace("-", "")
        if len(symbol) > 12 or not cleaned.isalnum():
            continue
        seen.add(symbol)
        symbols.append(symbol)
    return symbols


def normalize_finnhub_article(raw: dict) -> NewsItem | None:
    title = (raw.get("headline") or "").strip()
    url = (raw.get("url") or "").strip()
    if not title or not url:
        return None

    source = (raw.get("source") or "Unknown").strip() or "Unknown"
    snippet = (raw.get("summary") or None)
    if isinstance(snippet, str):
        snippet = snippet.strip() or None

    return NewsItem(
        title=title,
        url=url,
        source=source,
        published_at=_parse_published_at(raw.get("datetime")),
        snippet=snippet,
        related_symbols=parse_related_symbols(raw.get("related")),
    )


def normalize_finnhub_profile(raw: dict) -> CompanyProfile:
    name = raw.get("name")
    logo = raw.get("logo")
    return CompanyProfile(
        name=name.strip() if isinstance(name, str) and name.strip() else None,
        logo_url=logo.strip() if isinstance(logo, str) and logo.strip() else None,
    )


class NewsService:
    def __init__(self, api_key: str, client: httpx.AsyncClient | None = None) -> None:
        self._api_key = api_key
        self._client = client
        self._owns_client = client is None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=20.0)
        return self._client

    async def aclose(self) -> None:
        if self._owns_client and self._client is not None:
            await self._client.aclose()
            self._client = None

    async def fetch_company_profile(self, symbol: str) -> CompanyProfile | None:
        """Fetch company name/logo. Returns None on failure so summaries still work."""
        params = {"symbol": symbol, "token": self._api_key}
        client = await self._get_client()
        try:
            response = await client.get(FINNHUB_PROFILE_URL, params=params)
            response.raise_for_status()
            payload = response.json()
        except httpx.HTTPError:
            logger.warning("Finnhub profile request failed for %s", symbol, exc_info=True)
            return None

        if not isinstance(payload, dict) or not payload:
            logger.info("No Finnhub profile for %s", symbol)
            return None

        profile = normalize_finnhub_profile(payload)
        if profile.name is None and profile.logo_url is None:
            return None
        return profile

    async def fetch_company_news(self, symbol: str, *, limit: int = 8) -> list[NewsItem]:
        """Fetch and normalize recent company news for a symbol.

        Returns an empty list when Finnhub has no articles (caller should surface a clear empty state).
        Raises NewsServiceError on transport/API failures.
        """
        today = datetime.now(tz=UTC).date()
        from_iso = (today - timedelta(days=7)).isoformat()
        to_iso = today.isoformat()

        params = {
            "symbol": symbol,
            "from": from_iso,
            "to": to_iso,
            "token": self._api_key,
        }

        client = await self._get_client()
        try:
            response = await client.get(FINNHUB_NEWS_URL, params=params)
            response.raise_for_status()
            payload = response.json()
        except httpx.HTTPError as exc:
            logger.exception("Finnhub request failed for %s", symbol)
            raise NewsServiceError(f"Failed to fetch news for {symbol}") from exc

        if not isinstance(payload, list):
            logger.error("Unexpected Finnhub payload type for %s: %s", symbol, type(payload))
            raise NewsServiceError(f"Unexpected news response for {symbol}")

        items: list[NewsItem] = []
        for raw in payload:
            if not isinstance(raw, dict):
                continue
            item = normalize_finnhub_article(raw)
            if item is not None:
                items.append(item)
            if len(items) >= limit:
                break

        logger.info("Fetched %s news items for %s", len(items), symbol)
        return items
