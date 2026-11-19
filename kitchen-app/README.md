# Chèf Percy’s Kitchen

Phase 2 adds a database-backed customer menu and a protected owner dashboard to the Vue website and FastAPI/PostgreSQL foundation. The website uses the supplied business details and the Airtel WhatsApp contact shown in the existing demo. WhatsApp links prepare a message for the visitor to send. The website does not require the API to browse or enquire, and uses prices from the confirmed menu poster.

## Website

Use Node.js 22.12+ or 24 and npm.

```sh
cd frontend
npm ci
npm run dev
npm run build
```

Build the root `dist/` directory before starting FastAPI. Serve the customer website and API from the same FastAPI origin so the menu can read the database. Navigation uses hash routes so static hosts can serve all pages without rewrite rules. Photography is in `frontend/public/images`. Public contact details are in `frontend/src/kitchen.ts` and in the database seed. Update both if the business details change.

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

Open `http://127.0.0.1:8000/docs` for the OpenAPI reference. The foundation endpoints are `GET /api/health` for liveness, `GET /api/ready` for database and seed readiness, and `GET /api/business` for public business details. The initial migration creates and seeds the singleton `business_profile` table.

For hosted API use, set a managed PostgreSQL connection URL in the hosting secret store, use HTTPS, run migrations before serving traffic, and configure database backups with a tested restore.

## Verification

The frontend production build runs Vue TypeScript checks. With the local PostgreSQL service up, use `alembic check` to check schema drift and request each API endpoint to smoke-test its response.

## Customer and owner access

- Customers visit `/` and browse `/#/menu`. The public `GET /api/menu` returns visible entries only.
- The owner visits `/owner` directly. There is no owner link in customer navigation. The dashboard and its files and API require HTTP Basic credentials.
- Set `OWNER_PASSWORD` in the backend environment before startup. Use a randomly generated secret of at least 32 characters. The username is `owner`. The dashboard refuses access until the secret is configured. Keep it out of Git, share it only with the owner, and rotate it by changing the secret and restarting the API. Use a private browser window on shared devices and close it when finished. HTTP Basic credentials may be cached by the browser.
- Use HTTPS outside localhost. Store the password and PostgreSQL URL in the host's secret store. Keep the customer and dashboard on the same origin and leave the owner API off cross-origin allowlists.
- Owner menu changes persist in PostgreSQL. Use the visibility checkbox to take an item off the customer menu. The seafood add-on retains the poster's range, and catering prices display as starting prices.

Existing Phase 1 installations should run `alembic upgrade head` to create and seed the 24 menu entries. The migration leaves the business profile intact. Before rolling back the menu migration in a live database, back up the menu because its table will be dropped.

## Phase 3 and Windows launcher

From the repository root, double-click `Start Chèf Percy.cmd` to migrate the local Windows PostgreSQL database, start the app, and open the customer menu. The launcher uses `kitchen-app\backend\.venv` and expects PostgreSQL on port 5432 with a `percy` database and account. Keep the launcher window open. The password it asks for belongs to PostgreSQL. The dashboard username and generated password are shown after the migration.

Customers can add fixed-price items to a cart, request pickup or Yango delivery, and look up the confirmation using its reference. Recent references are saved in the browser. Quote-only items still use WhatsApp. PostgreSQL stores the submitted items and prices as they were at checkout. The owner dashboard lists the 50 newest requests with their contact details. A request is received on submission. Availability, delivery fees and payment are confirmed by Percy. Online payments belong to a later phase.

## Phase 4 and the kitchen

The owner can confirm, cancel, prepare, mark ready and complete order requests from the authenticated owner dashboard. The dashboard can set a daily request limit or leave it blank for unlimited. All submissions count toward the limit, including cancelled requests. The count resets at midnight in Kitwe. Earlier orders start in the received state. Order status changes are recorded with their timestamp and role.

Kitchen staff open `/kitchen` and sign in as `kitchen`, using the separate `KITCHEN_PASSWORD` secret (at least 32 characters). The board refreshes every five seconds. Staff can move confirmed tickets into preparation and mark them ready. They see meal details and pickup or delivery type. Customer names, phone numbers, addresses, menu controls and order limits are available to the owner only. This setup uses one shared kitchen-role credential. The Windows launcher generates both dashboard credentials for that run. Share only the kitchen credential with staff, and run local access on the PC hosting FastAPI. Use HTTPS and managed secrets when hosting outside localhost.

Customers can look up their order reference and refresh its latest status. Confirming an order does not verify payment.
