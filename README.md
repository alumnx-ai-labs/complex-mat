# complex-mat

A Meeting Action Tracker: a Vite + React frontend and a FastAPI backend.

## Project layout

- [`frontend/`](frontend) — Vite + React app.
- [`backend/`](backend) — FastAPI app (SQLite via SQLAlchemy).
- [`frontend/e2e/`](frontend/e2e) — Playwright end-to-end tests. See [e2e-test-scenarios.md](frontend/e2e/e2e-test-scenarios.md) for what each test covers.

## Running the backend locally

```bash
cd backend
python -m venv .venv && source .venv/bin/activate   # first time only
pip install -r requirements.txt
cp .env.example .env                                # adjust values as needed
python -m app.seed                                   # creates tables + default Admin
python -m uvicorn app.main:app --reload --port 8000
```

The backend also seeds itself automatically on startup (`app.main` runs `seed()` on the FastAPI `startup` event), so `python -m app.seed` is optional — but running it explicitly first is a fast way to confirm the DB path/env vars are correct.

Default seeded Admin (from `.env.example`): `john@example.com` / `ChangeMe123!`. The API docs are at `http://localhost:8000/docs`.

## Running the frontend locally

```bash
cd frontend
npm install
npm run dev   # http://localhost:5173
```

The frontend calls the backend at `VITE_API_BASE_URL` (falls back to `http://localhost:8000` if unset). Set it in `frontend/.env` for a non-default backend location.

## Deployed environments

- **Frontend**: deployed to Vercel. `frontend/vercel.json` rewrites all paths to `index.html` so client-side routing (`/login`, `/calendar`, etc.) works — without it, Vercel 404s on any route but `/`.
- **Backend**: deployed to Render (or similar). It needs:
  - `CORS_ORIGINS` set to include the deployed frontend's origin (comma-separated for multiple), e.g. `https://your-app.vercel.app,http://localhost:5173`.
  - `VITE_API_BASE_URL` set on the **frontend's** Vercel project to point at this backend's URL, baked in at build time.
  - Free-tier hosts (e.g. Render) can cold-start in tens of seconds after idling — expect the first request after a while to be slow.

## End-to-end tests

End-to-end tests live in [`frontend/e2e`](frontend/e2e) and run with [Playwright](https://playwright.dev/). See [e2e-test-scenarios.md](frontend/e2e/e2e-test-scenarios.md) for a readable list of what's covered.

### Running against local frontend + backend

```bash
cd frontend
npx playwright test            # headless
npx playwright test --headed   # see the browser
npx playwright test e2e/auth.spec.ts   # run a single file
```

`playwright.config.ts`'s `webServer` entries boot the frontend (`localhost:5173`) and a freshly seeded backend (`localhost:8000`) for you automatically — no manual setup needed for this mode.

### Running against a deployed environment

Point the suite at a deployed frontend URL instead of localhost with `PLAYWRIGHT_BASE_URL`. If the target is a Vercel preview deployment behind Deployment Protection, also pass a bypass token (Vercel Project Settings → Deployment Protection → Protection Bypass for Automation) via `VERCEL_PROTECTION_BYPASS`:

```bash
cd frontend
PLAYWRIGHT_BASE_URL=your-deployment.vercel.app \
E2E_ADMIN_MAIL_ID=<admin email that exists on that environment> \
E2E_ADMIN_PASSWORD=<its password> \
VERCEL_PROTECTION_BYPASS=<bypass token> \
npx playwright test --headed
```

When `PLAYWRIGHT_BASE_URL` is set:
- the local `webServer` processes are skipped (nothing is started on localhost),
- the assertion timeout is extended (20s instead of 5s) to absorb backend cold starts on free-tier hosts,
- the admin credentials must be a real, valid account on whatever backend that deployment is wired to — not the local test-seed defaults, unless that deployment happens to share the same seed data.
