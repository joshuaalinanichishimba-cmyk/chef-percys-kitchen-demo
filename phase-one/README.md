# Chèf Percy’s Kitchen

Phase 1 includes a Vue website and a separate FastAPI/PostgreSQL foundation. The static website uses the supplied business details and the Airtel WhatsApp contact shown in the existing demo. WhatsApp links prepare a message for the visitor to send. The website does not require the API to browse or enquire, and does not display unconfirmed menu prices.

## Website

Use Node.js 22.12+ or 24 and npm.

```sh
cd frontend
npm ci
npm run dev
npm run build
```

Publish the generated root `dist/` directory. Navigation uses hash routes so static hosts can serve all pages without rewrite rules. Photography is in `frontend/public/images`. Public contact details are in `frontend/src/kitchen.ts` and in the database seed. Update both if the business details change during Phase 1.

## API and database

Use Python 3.11+ and Docker Compose, or an existing PostgreSQL server. The Compose credentials below are for loopback development only.

```sh
docker compose up -d --wait
cd backend
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements.txt
export DATABASE_URL=postgresql+psycopg://percy:percy-local-only@127.0.0.1:55432/percy
alembic upgrade head
uvicorn app.main:app
```

Open `http://127.0.0.1:8000/docs` for the OpenAPI reference. The three read-only endpoints are `GET /api/health` for liveness, `GET /api/ready` for database and seed readiness, and `GET /api/business` for public business details. The initial migration creates and seeds the singleton `business_profile` table. Phase 1 has no protected routes or administrator accounts.

For hosted API use, set a managed PostgreSQL connection URL in the hosting secret store, use HTTPS, run migrations before serving traffic, and configure database backups with a tested restore. The static website deployment contains only `dist/`.

## Verification

The frontend production build runs Vue TypeScript checks. With the local PostgreSQL service up, use `alembic check` to check schema drift and request each API endpoint to smoke-test its response.
