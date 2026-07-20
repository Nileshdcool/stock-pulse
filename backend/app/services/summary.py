import json
import logging
from typing import Any

from openai import AsyncOpenAI, OpenAIError

from app.models import NewsItem

logger = logging.getLogger(__name__)


class SummaryServiceError(Exception):
    """Raised when OpenAI cannot produce a usable summary."""


SYSTEM_PROMPT = """You are a concise market-news assistant for traders.
Summarize ONLY from the provided headlines and snippets.
Do not invent facts, prices, or sources.
Do not give investment advice or buy/sell recommendations.
Return strict JSON with keys:
- summary: string (2-4 short sentences)
- bullets: array of 3-5 short bullet strings
"""


def build_user_prompt(symbol: str, news: list[NewsItem]) -> str:
    lines = [f"Stock symbol: {symbol}", "Recent news:", ""]
    for index, item in enumerate(news, start=1):
        published = item.published_at.isoformat() if item.published_at else "unknown"
        snippet = item.snippet or ""
        lines.append(f"{index}. [{item.source}] {item.title}")
        lines.append(f"   Published: {published}")
        if snippet:
            lines.append(f"   Snippet: {snippet}")
        lines.append(f"   URL: {item.url}")
        lines.append("")
    lines.append("Produce the JSON summary now.")
    return "\n".join(lines)


def parse_summary_payload(content: str) -> tuple[str, list[str]]:
    try:
        data: Any = json.loads(content)
    except json.JSONDecodeError as exc:
        raise SummaryServiceError("Model returned non-JSON content") from exc

    if not isinstance(data, dict):
        raise SummaryServiceError("Model JSON must be an object")

    summary = data.get("summary")
    bullets = data.get("bullets", [])
    if not isinstance(summary, str) or not summary.strip():
        raise SummaryServiceError("Model JSON missing summary string")
    if not isinstance(bullets, list) or not all(isinstance(b, str) for b in bullets):
        raise SummaryServiceError("Model JSON bullets must be a list of strings")

    return summary.strip(), [b.strip() for b in bullets if b.strip()]


class SummaryService:
    def __init__(
        self,
        api_key: str,
        model: str = "gpt-4o-mini",
        client: AsyncOpenAI | None = None,
    ) -> None:
        self._model = model
        self._client = client or AsyncOpenAI(api_key=api_key)

    async def summarize(self, symbol: str, news: list[NewsItem]) -> tuple[str, list[str]]:
        if not news:
            raise SummaryServiceError("No news available to summarize")

        try:
            response = await self._client.chat.completions.create(
                model=self._model,
                temperature=0.2,
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": build_user_prompt(symbol, news)},
                ],
            )
        except OpenAIError as exc:
            logger.exception("OpenAI request failed for %s", symbol)
            raise SummaryServiceError(f"Failed to generate summary for {symbol}") from exc

        content = response.choices[0].message.content if response.choices else None
        if not content:
            raise SummaryServiceError("Empty response from OpenAI")

        return parse_summary_payload(content)
