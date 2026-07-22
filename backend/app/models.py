from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator

NewsPeriod = Literal["1d", "7d", "30d"]

PERIOD_DAYS: dict[NewsPeriod, int] = {
    "1d": 1,
    "7d": 7,
    "30d": 30,
}

# Longer windows keep more articles so sources/summary span the period, not only today.
PERIOD_NEWS_LIMIT: dict[NewsPeriod, int] = {
    "1d": 8,
    "7d": 12,
    "30d": 16,
}

DEFAULT_PERIOD: NewsPeriod = "7d"
ALLOWED_PERIODS = frozenset(PERIOD_DAYS)


class NewsItem(BaseModel):
    title: str
    url: str
    source: str
    published_at: datetime | None = None
    snippet: str | None = None
    related_symbols: list[str] = Field(default_factory=list)


class SourceLink(BaseModel):
    title: str
    url: str
    source: str
    published_at: datetime | None = None
    related_symbols: list[str] = Field(default_factory=list)


class SummaryResponse(BaseModel):
    symbol: str
    company_name: str | None = None
    logo_url: str | None = None
    summary: str
    bullets: list[str] = Field(default_factory=list)
    sources: list[SourceLink] = Field(default_factory=list)
    period: NewsPeriod = DEFAULT_PERIOD
    generated_at: datetime
    cached: bool = False


class ErrorResponse(BaseModel):
    detail: str


def normalize_symbol(symbol: str) -> str:
    cleaned = symbol.strip().upper()
    if not cleaned or len(cleaned) > 12 or not cleaned.replace(".", "").replace("-", "").isalnum():
        raise ValueError("Invalid stock symbol")
    return cleaned


def normalize_period(period: str) -> NewsPeriod:
    cleaned = period.strip().lower()
    if cleaned not in ALLOWED_PERIODS:
        allowed = ", ".join(sorted(ALLOWED_PERIODS))
        raise ValueError(f"Invalid period. Allowed values: {allowed}")
    return cleaned  # type: ignore[return-value]


def period_days(period: NewsPeriod) -> int:
    return PERIOD_DAYS[period]


def period_news_limit(period: NewsPeriod) -> int:
    return PERIOD_NEWS_LIMIT[period]


class SymbolPath(BaseModel):
    symbol: str

    @field_validator("symbol")
    @classmethod
    def validate_symbol(cls, value: str) -> str:
        return normalize_symbol(value)
