from datetime import UTC, datetime

import pytest

from app.models import NewsItem, normalize_symbol
from app.services.news import normalize_finnhub_article
from app.services.summary import build_user_prompt, parse_summary_payload


def test_normalize_symbol_accepts_valid() -> None:
    assert normalize_symbol(" aapl ") == "AAPL"
    assert normalize_symbol("BRK.B") == "BRK.B"


def test_normalize_symbol_rejects_invalid() -> None:
    with pytest.raises(ValueError):
        normalize_symbol("")
    with pytest.raises(ValueError):
        normalize_symbol("BAD SYMBOL")


def test_normalize_finnhub_article() -> None:
    item = normalize_finnhub_article(
        {
            "headline": "Apple launches product",
            "url": "https://example.com/a",
            "source": "Reuters",
            "datetime": 1_700_000_000,
            "summary": "Details here",
            "related": "AAPL,MSFT,AAPL",
        }
    )
    assert item is not None
    assert item.title == "Apple launches product"
    assert item.source == "Reuters"
    assert item.snippet == "Details here"
    assert item.related_symbols == ["AAPL", "MSFT"]


def test_normalize_finnhub_article_skips_incomplete() -> None:
    assert normalize_finnhub_article({"headline": "", "url": "https://x"}) is None
    assert normalize_finnhub_article({"headline": "Hi", "url": ""}) is None


def test_normalize_finnhub_profile() -> None:
    from app.services.news import normalize_finnhub_profile

    profile = normalize_finnhub_profile(
        {
            "name": " Apple Inc ",
            "logo": " https://example.com/logo.png ",
        }
    )
    assert profile.name == "Apple Inc"
    assert profile.logo_url == "https://example.com/logo.png"


def test_parse_summary_payload() -> None:
    summary, bullets = parse_summary_payload(
        '{"summary": "Markets reacted calmly.", "bullets": ["Point one", "Point two"]}'
    )
    assert summary == "Markets reacted calmly."
    assert bullets == ["Point one", "Point two"]


def test_build_user_prompt_includes_symbol_and_titles() -> None:
    news = [
        NewsItem(
            title="Earnings beat",
            url="https://example.com/1",
            source="WSJ",
            published_at=datetime(2024, 1, 1, tzinfo=UTC),
            snippet="Beat estimates",
        )
    ]
    prompt = build_user_prompt("AAPL", news)
    assert "AAPL" in prompt
    assert "Earnings beat" in prompt
    assert "WSJ" in prompt
