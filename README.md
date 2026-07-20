# Stock Pulse

Stock Pulse generates a concise, trader-oriented news summary for a given stock ticker. The Angular client sends a symbol to a FastAPI backend, which pulls recent company news from Finnhub, summarizes it with OpenAI, and returns structured text plus source links.

## Features

- Look up a ticker (e.g. `AAPL`) from a responsive single-page UI
- Fetch recent company news via Finnhub (last 7 days)
- Load company name and logo in parallel from Finnhub company profile
- Produce a short summary and bullet points with OpenAI (`gpt-4o-mini` by default)
- Show summary, key points, company identity, and clickable source articles
- Surface related tickers from each article (`related_symbols`) as chips on sources
- Quick-suggestion tickers and auto-uppercase symbol input
- Cache repeated requests in memory with a configurable TTL (`cached` flag in the response)

## Stack

| Layer | Technology |
| --- | --- |
| Frontend | Angular 19 (standalone), Angular Material, RxJS, Jest |
| Backend | FastAPI, Pydantic v2, httpx, uvicorn |
| External APIs | Finnhub (company news + profile), OpenAI (summarization) |
| Testing | pytest (backend), Jest (frontend) |

## Architecture

```text
Browser (Angular)
    │  GET /api/stocks/{symbol}/summary
    ▼
FastAPI
    ├─ validate & normalize symbol
    ├─ TTL cache lookup
    ├─ Finnhub company news  ─┐
    ├─ Finnhub company profile ┘ (parallel)
    ├─ OpenAI JSON summary
    └─ response: company_name, logo_url, summary, bullets, sources
```

API keys stay on the server. News and profile are fetched concurrently; a missing profile does not block the summary. The model is instructed not to invent facts; if there is no news or an upstream call fails, the API returns an explicit error instead of fabricated content.

## Prerequisites

- Python 3.11+
- Node.js 20+
- [OpenAI API key](https://platform.openai.com/api-keys)
- [Finnhub API key](https://finnhub.io/register) (free tier is sufficient)

## Configuration

Copy `backend/.env.example` to `backend/.env` and set:

| Variable | Required | Default | Description |
| --- | --- | --- | --- |
| `OPENAI_API_KEY` | yes | — | OpenAI credentials |
| `FINNHUB_API_KEY` | yes | — | Finnhub credentials |
| `OPENAI_MODEL` | no | `gpt-4o-mini` | Chat model used for summaries |
| `CACHE_TTL_SECONDS` | no | `300` | In-memory cache lifetime |
| `CORS_ORIGINS` | no | `http://localhost:4200` | Allowed frontend origins (comma-separated) |
| `LOG_LEVEL` | no | `INFO` | Application log level |

## Setup

### Backend

```bash
python -m venv .venv
# Windows
.\.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate

pip install -r backend/requirements.txt
# Windows
copy backend\.env.example backend\.env
# macOS / Linux
# cp backend/.env.example backend/.env
```

Start the API from the `backend` directory so `.env` is loaded correctly:

```bash
cd backend
uvicorn app.main:app --reload --port 8000
```

- API: http://localhost:8000  
- OpenAPI docs: http://localhost:8000/docs  

### Frontend

```bash
cd frontend
npm install
npm start
```

App: http://localhost:4200

## API

### `GET /health`

```json
{ "status": "ok" }
```

### `GET /api/stocks/{symbol}/summary`

Returns an AI summary for the given ticker.

**Success (`200`)**

```json
{
  "symbol": "AAPL",
  "company_name": "Apple Inc",
  "logo_url": "https://static2.finnhub.io/file/publicdatany/finnhubimage/stock_logo/AAPL.svg",
  "summary": "...",
  "bullets": ["...", "..."],
  "sources": [
    {
      "title": "...",
      "url": "https://...",
      "source": "...",
      "published_at": "2026-07-20T12:00:00Z",
      "related_symbols": ["AAPL", "MSFT"]
    }
  ],
  "generated_at": "2026-07-20T12:05:00Z",
  "cached": false
}
```

**Errors**

| Status | When |
| --- | --- |
| `400` | Invalid symbol |
| `404` | No recent news for the symbol |
| `502` | Finnhub or OpenAI upstream failure |

## Project layout

```text
backend/
  app/
    api/           Route handlers
    services/      Finnhub news/profile + OpenAI summary
    cache.py       In-memory TTL cache
    config.py      pydantic-settings env config
    models.py      Request/response schemas
    main.py        App factory & lifespan
  tests/           pytest suite (mocked externals)
frontend/
  src/app/         Angular UI, HTTP service, models
  src/environments API base URL (dev/prod)
```

## Design decisions

| Choice | Rationale |
| --- | --- |
| Angular + FastAPI | Typed SPA and async Python API with OpenAPI docs and clear separation of UI vs. orchestration |
| Finnhub as the news source | Stable REST API; avoids brittle HTML scraping |
| Finnhub profile for logo/name | Company identity is not in the news payload; profile2 is the dedicated source |
| Soft-fail on profile | Logo/name enrich the UI; missing profile still returns a full summary |
| `related_symbols` on sources | Finnhub `related` field surfaces co-mentioned tickers without extra calls |
| Server-side OpenAI calls | Keeps API keys off the client |
| Explicit empty/error responses | Never invent headlines when news is missing or providers fail |
| In-memory TTL cache | Low latency for repeated local lookups without external infrastructure |
| Responsive single-page UI | Brand-led hero, suggestion chips, and fluid layout across breakpoints |
| pydantic-settings | Typed configuration with `.env` loading |
| stdlib logging | Sufficient observability for a single-process service (logs go to the uvicorn terminal) |
| pytest + Jest with mocks | Fast, deterministic tests without live API calls |

## Tests

External providers are mocked; no live Finnhub or OpenAI calls are required.

### Backend

```bash
.\.venv\Scripts\python -m pytest backend/tests -q
```

Coverage includes symbol validation, Finnhub news/profile normalization (including `related_symbols`), prompt/JSON parsing, happy path, cache hits, empty news (`404`), and upstream failures (`502`).

### Frontend

```bash
cd frontend
npm test
```

Covers the HTTP service URL construction and component loading, error, and summary states (logo identity and source ticker chips).

## Roadmap

Possible production hardening steps:

- Shared cache (e.g. Redis) across multiple API instances
- Async workers for watchlists or high-traffic tickers
- Persistent store for audit trails and prompt evaluation
- Metrics for latency, cache hit rate, and token usage
- Containerized deploy (Docker) to preferred cloud runtime
