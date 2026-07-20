from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router
from app.cache import TtlCache
from app.config import Settings, get_settings
from app.logging_setup import configure_logging
from app.models import SummaryResponse
from app.services.news import NewsService
from app.services.summary import SummaryService


def create_app(settings: Settings | None = None) -> FastAPI:
    app_settings = settings or get_settings()

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        configure_logging(app_settings.log_level)

        news_service = NewsService(api_key=app_settings.finnhub_api_key)
        summary_service = SummaryService(
            api_key=app_settings.openai_api_key,
            model=app_settings.openai_model,
        )
        app.state.settings = app_settings
        app.state.cache = TtlCache[SummaryResponse](ttl_seconds=app_settings.cache_ttl_seconds)
        app.state.news_service = news_service
        app.state.summary_service = summary_service

        try:
            yield
        finally:
            await news_service.aclose()

    application = FastAPI(
        title="Stock Pulse",
        description="AI-generated summary of the latest news for a stock ticker.",
        version="0.1.0",
        lifespan=lifespan,
    )
    application.add_middleware(
        CORSMiddleware,
        allow_origins=app_settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    application.include_router(router)
    return application


# Lazy ASGI app so importing create_app in tests does not require real API keys.
_app: FastAPI | None = None


def __getattr__(name: str) -> FastAPI:
    if name == "app":
        global _app
        if _app is None:
            _app = create_app()
        return _app
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
