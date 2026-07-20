from datetime import UTC, datetime
from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient

from app.cache import TtlCache
from app.config import Settings
from app.main import create_app
from app.models import NewsItem, SummaryResponse
from app.services.news import CompanyProfile, NewsServiceError
from app.services.summary import SummaryServiceError


@pytest.fixture
def settings() -> Settings:
    return Settings(
        openai_api_key="test-openai",
        finnhub_api_key="test-finnhub",
        openai_model="gpt-4o-mini",
        cache_ttl_seconds=60,
        cors_origins="http://localhost:4200",
        log_level="WARNING",
    )


@pytest.fixture
def sample_news() -> list[NewsItem]:
    return [
        NewsItem(
            title="Apple reports strong iPhone sales",
            url="https://example.com/news/1",
            source="Reuters",
            published_at=datetime(2024, 6, 1, tzinfo=UTC),
            snippet="Sales rose year over year.",
            related_symbols=["AAPL"],
        )
    ]


@pytest.fixture
def client(settings: Settings, sample_news: list[NewsItem]):
    app = create_app(settings)
    news_service = AsyncMock()
    news_service.fetch_company_news = AsyncMock(return_value=sample_news)
    news_service.fetch_company_profile = AsyncMock(
        return_value=CompanyProfile(
            name="Apple Inc",
            logo_url="https://example.com/aapl.png",
        )
    )
    news_service.aclose = AsyncMock()

    summary_service = AsyncMock()
    summary_service.summarize = AsyncMock(
        return_value=("Apple news looks constructive.", ["iPhone sales strong"])
    )

    with TestClient(app) as test_client:
        app.state.news_service = news_service
        app.state.summary_service = summary_service
        app.state.cache = TtlCache[SummaryResponse](ttl_seconds=60)
        yield test_client, news_service, summary_service


def test_health(client) -> None:
    test_client, _, _ = client
    response = test_client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_summary_happy_path(client) -> None:
    test_client, news_service, summary_service = client
    response = test_client.get("/api/stocks/aapl/summary")
    assert response.status_code == 200
    body = response.json()
    assert body["symbol"] == "AAPL"
    assert body["company_name"] == "Apple Inc"
    assert body["logo_url"] == "https://example.com/aapl.png"
    assert body["summary"] == "Apple news looks constructive."
    assert body["bullets"] == ["iPhone sales strong"]
    assert body["cached"] is False
    assert len(body["sources"]) == 1
    assert body["sources"][0]["related_symbols"] == ["AAPL"]
    news_service.fetch_company_news.assert_awaited()
    news_service.fetch_company_profile.assert_awaited()
    summary_service.summarize.assert_awaited()


def test_summary_uses_cache(client) -> None:
    test_client, news_service, summary_service = client
    first = test_client.get("/api/stocks/AAPL/summary")
    second = test_client.get("/api/stocks/AAPL/summary")
    assert first.status_code == 200
    assert second.status_code == 200
    assert second.json()["cached"] is True
    assert news_service.fetch_company_news.await_count == 1
    assert summary_service.summarize.await_count == 1


def test_invalid_symbol(client) -> None:
    test_client, _, _ = client
    response = test_client.get("/api/stocks/BAD%20SYMBOL/summary")
    assert response.status_code == 400


def test_empty_news(client) -> None:
    test_client, news_service, summary_service = client
    news_service.fetch_company_news = AsyncMock(return_value=[])
    response = test_client.get("/api/stocks/AAPL/summary")
    assert response.status_code == 404
    assert "No recent news" in response.json()["detail"]
    summary_service.summarize.assert_not_awaited()


def test_news_upstream_failure(client) -> None:
    test_client, news_service, _ = client
    news_service.fetch_company_news = AsyncMock(side_effect=NewsServiceError("down"))
    response = test_client.get("/api/stocks/AAPL/summary")
    assert response.status_code == 502


def test_openai_failure(client) -> None:
    test_client, _, summary_service = client
    summary_service.summarize = AsyncMock(side_effect=SummaryServiceError("openai down"))
    response = test_client.get("/api/stocks/AAPL/summary")
    assert response.status_code == 502
