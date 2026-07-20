from datetime import datetime

from pydantic import BaseModel, Field, field_validator


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
    generated_at: datetime
    cached: bool = False


class ErrorResponse(BaseModel):
    detail: str


def normalize_symbol(symbol: str) -> str:
    cleaned = symbol.strip().upper()
    if not cleaned or len(cleaned) > 12 or not cleaned.replace(".", "").replace("-", "").isalnum():
        raise ValueError("Invalid stock symbol")
    return cleaned


class SymbolPath(BaseModel):
    symbol: str

    @field_validator("symbol")
    @classmethod
    def validate_symbol(cls, value: str) -> str:
        return normalize_symbol(value)
