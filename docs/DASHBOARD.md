# TraderLab observability console

The user moved the read-only dashboard ahead of native validation and Demo execution. It consumes evidence from the strategy engine; it never implements entry rules or controls orders.

## Delivered application

`web/` is a Next.js16.3.8 / React19.3.0 TypeScript application deployable as a Vercel project with Root Directory `web`. Locally:

```powershell
Set-Location D:\Github\TraderLab\web
npm ci
npm run dev
```

The UI uses Persian RTL text, self-hosted Vazirmatn/IBM Plex Mono, an interactive TradingView Lightweight Charts candle chart, confirmed detection/annotated zone overlays, event inspection, setup plans, closed paper PnL, exit reasons and replay by event count. Live detection metrics never imply executed broker trades.

Three sources are explicit:

1. Canonical synthetic paper fixture. The journal events are copied from the canonical-A replay output. Additional sixty M1 OHLC bars are fabricated display context, not market data, detection evidence or an input to the strategy backtest.
2. Local imported JSONL. Parsed in the browser only; file provenance is unverified. Import does not upload to Vercel. Decimal price conversion occurs only for chart display; financial calculations remain the strategy engine's responsibility.
3. Protected cloud runs, declared native or paper by the authenticated publisher. This is an asserted source identity, not independent proof of a real broker account.

Future Big Candle confirmations appear only when their confirmation event is visible. Native unknown UTC timestamps stay null and are labeled; no broker offset is inferred. BOS/OB boundaries remain missing or sourced annotations as in the canonical spec. The dashboard does not construct them.

## Live architecture

MT5 writes JSONL with file sharing enabled. A separate Python stdlib publisher tails complete rows and POSTs at most100 rows /200KB batches to `/api/ingest`. Its own key is only read from `TRADERLAB_INGEST_KEY`. Retries are byte-equivalent event batches; the server's PostgreSQL transaction locks the run, requires a contiguous sequence and refuses changed retries or identity reuse. Acknowledged offsets/last-line hashes are checkpointed atomically. Truncation or rewriting at the checkpoint stops publishing. The EA is never blocked on an HTTP request.

PostgreSQL tables retain raw payloads, source timestamps and receipt timestamps. Data is not stored in a Vercel function filesystem or request-global memory. The browser polls every3 seconds; only one polling loop per selected run operates, hidden tabs pause requests, and fetches are aborted when changing source/run. Publisher heartbeats every10 seconds update connectivity separately from event freshness. Missing tick traffic is not misrepresented as an active strategy.

## Cloud setup

1. Create or claim a Vercel project. For Git deployment, connect this repository and set Root Directory=`web`, framework=`Next.js`, build=`npm run build`, Node22+.
2. Provision Neon PostgreSQL from Vercel Marketplace (or Neon console). Copy its connection string to server-only `DATABASE_URL`.
3. Set independently generated `TRADERLAB_INGEST_KEY` and `TRADERLAB_SESSION_SECRET` (minimum32 characters each), plus `TRADERLAB_VIEWER_PASSWORD` (minimum12). None may be `NEXT_PUBLIC_*`.
4. Copy `web/.env.example` to `.env.local` locally, populate it without committing it, and run `npm run db:setup`. Alternatively run `web/db/schema.sql` in the Neon SQL Editor. The script uses a single transaction for schema statements; no production data is dropped.
5. Redeploy after environment changes. The console's connection dialog shows missing configuration; no simulated run is substituted for a failed cloud request.

The `/guide` page contains the same operator steps. Public access exposes only the synthetic sample, local imports and boolean configuration readiness. Live run/event APIs independently validate an8-hour HMAC HttpOnly session. Password changes invalidate sessions. Login attempts are capped at5 per15-minute IP-key bucket in PostgreSQL; source origins are checked on session mutations. Logout clears credentials and displayed live state. The ingest API uses its separate bearer key; it cannot place orders. Do not share the ingest key with viewer clients.

## Start the local publisher

Set the environment ingest key on the Windows machine running MT5. From the project root, substitute an actual terminal file and deployment origin:

```powershell
python tools/publish_events.py --file "C:/actual-terminal/MQL5/Files/TraderLab-run01.jsonl" --url "https://your-dashboard.vercel.app" --run "demo-20261005-01" --bot "mt5-demo-01" --label "Demo capture 01" --source native --symbol XAUUSD --checkpoint "work/publisher/demo-20261005-01.json"
```

A new capture always gets a new run ID and checkpoint. A fixed replay journal may use `--source paper --once`; it is labeled paper in the UI. Capture cannot start here until the native EA is compiled and running. Unknown native UTC is preserved for diagnostic viewing; the historical replay importer still refuses it.

## Current limits and verification boundaries

Native EA compilation/execution and historical market backtesting remain unverified. Cloud ingestion, SQL installation and real live transport require a configured PostgreSQL database and actual native capture; source/build checks do not establish these. The website contains no order endpoint or native execution implementation.

The UI reads the latest30 runs, downloads events in1000-row pages, and retains the first20,000 events of a run in the browser. On reaching the cap it explicitly freezes that view and warns; later events remain in the database. This is a short-run observability release. Longer runs need server-side aggregation and a selectable historical window before using it for continuous monitoring. Journal filters display the last500 matching rows; export downloads all rows loaded into the current browser dataset. No database retention/deletion policy is introduced.

PnL is the sum of explicit PAPER_EXIT net results. It is not balance, unrealized PnL, broker equity or win rate. Daily state comes only from logged reset/exit fields. Native diagnostic-only captures intentionally show unavailable trade metrics. The dashboard also does not certify the strategy's financial performance.

## Primary references

- [Next.js installation and application routing](https://nextjs.org/docs/app/getting-started/installation)
- [Vercel Marketplace storage](https://vercel.com/docs/marketplace-storage)
- [Neon serverless driver](https://neon.com/docs/serverless/serverless-driver)
- [TradingView Lightweight Charts attribution and API](https://tradingview.github.io/lightweight-charts/docs)
