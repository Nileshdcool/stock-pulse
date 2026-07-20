# Stock Pulse — Frontend

Angular 19 single-page client for Stock Pulse. Enter a ticker, call the FastAPI backend, and render an AI news summary with company identity and source links.

## Stack

| Piece | Choice |
| --- | --- |
| Framework | Angular 19 (standalone components) |
| UI | Angular Material (form field, button, spinner) |
| Forms | Reactive Forms |
| HTTP | `HttpClient` via `StockSummaryService` |
| Tests | Jest + `jest-preset-angular` |
| Typography | Space Grotesk + IBM Plex Sans |

## Prerequisites

- Node.js 20+
- Backend running at the URL in `src/environments/environment.ts` (default `http://localhost:8000`)

## Setup

```bash
cd frontend
npm install
npm start
```

App: http://localhost:4200

| Script | Command |
| --- | --- |
| Dev server | `npm start` (`ng serve`) |
| Production build | `npm run build` |
| Unit tests | `npm test` |

## What the UI shows

- Brand-led hero and ticker search (auto-uppercase, validation)
- Quick suggestions: AAPL, MSFT, TSLA, NVDA
- Loading and error states from the API
- Result panel: company logo/name (when available), summary, key points, sources
- Ticker chips per source from `related_symbols` (falls back to the searched symbol)
- Cached badge when the backend returns `cached: true`

Layout is responsive: search stacks on small viewports; spacing and type use fluid `clamp()` values.

## Project layout

```text
src/app/
  app.component.*          Page shell, form, result rendering
  models/summary.ts        API response types
  services/
    stock-summary.service.ts   GET /api/stocks/{symbol}/summary
src/environments/
  environment.ts           Dev API base URL
  environment.prod.ts      Prod API base URL
```

## Configuration

Point the client at your API by editing `apiBaseUrl` in the environment files. CORS on the backend must allow the Angular origin (default `http://localhost:4200`).

## Tests

```bash
npm test
```

Covers HTTP URL construction and component loading, error, and summary states (including logo / related-ticker rendering).

## Notes

- API keys never live in the frontend; all Finnhub and OpenAI calls go through the backend.
- The cache badge reflects **server** in-memory cache, not browser storage. Restart the API or wait for `CACHE_TTL_SECONDS` to clear it.
- See the [root README](../README.md) for backend setup, env vars, and the full API contract.
