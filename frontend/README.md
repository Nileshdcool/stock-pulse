# Stock Pulse — Frontend

This is the Angular 19 client for Stock Pulse. You type a ticker, it calls the FastAPI backend, and the page shows an AI news summary with company details and source links.

If you’re looking for backend setup, env vars, or the full API contract, head over to the [root README](../README.md).

## Stack

| Piece     | Choice                                              |
| --------- | --------------------------------------------------- |
| Framework | Angular 19 (standalone components)                  |
| UI        | Angular Material (form field, button, spinner)      |
| Forms     | Reactive Forms                                      |
| HTTP      | `HttpClient` via `StockSummaryService`              |
| Tests     | Jest + `jest-preset-angular`                        |
| Typography| Space Grotesk + IBM Plex Sans                       |

## Prerequisites

- Node.js 20+
- Backend running at the URL in `src/environments/environment.ts` (default `http://localhost:8000`)

## Getting started

```bash
cd frontend
npm install
npm start
```

Then open [http://localhost:4200](http://localhost:4200).

| Script            | Command                        |
| ----------------- | ------------------------------ |
| Dev server        | `npm start` (`ng serve`)       |
| Production build  | `npm run build`                |
| Unit tests        | `npm test`                     |

## Demo

The root [README](../README.md#demo) embeds an animated walkthrough of the UI (`docs/screenshots/demo.gif`, plus `demo.mp4`).

## What you’ll see in the UI

- A brand-led hero with ticker search (auto-uppercase + validation)
- Period toggle: 1 day / 7 days / 30 days (re-fetches when a result is already shown)
- Quick suggestions: AAPL, MSFT, TSLA, NVDA
- Loading and error states wired to the API
- A result view with company logo/name (when available), period badge, summary, key points, and sources
- Related-ticker chips per source from `related_symbols` (falls back to the symbol you searched)
- A “cached” badge when the backend returns `cached: true`

The layout is responsive — search stacks on smaller screens, and spacing/type use fluid `clamp()` values so it doesn’t feel cramped.

## Project layout

```text
src/app/
  app.component.*              Page shell, form, result rendering
  models/summary.ts            API response types
  services/
    stock-summary.service.ts   GET /api/stocks/{symbol}/summary
src/environments/
  environment.ts               Dev API base URL
  environment.prod.ts          Prod API base URL
```

## Pointing at the API

Edit `apiBaseUrl` in the environment files to match your backend. CORS on the API side must allow the Angular origin (default `http://localhost:4200`).

## Tests

```bash
npm test
```

These cover HTTP URL construction and the component’s loading, error, and summary states — including logo and related-ticker rendering.

## A few notes

- API keys never live in the frontend. Finnhub and OpenAI calls always go through the backend.
- The cache badge reflects the **server** in-memory cache, not browser storage. Restart the API or wait for `CACHE_TTL_SECONDS` to clear it.
