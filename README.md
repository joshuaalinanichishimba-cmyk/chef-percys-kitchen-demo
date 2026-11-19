# Chèf Percy’s Kitchen

Chèf Percy’s Kitchen is a food ordering, catering and kitchen operations system for Percy Chanda’s business at L237, CBU Campus, Kitwe, Zambia. Prices are in Zambian kwacha.

## What it does

| Area | Features |
| --- | --- |
| Customer site | Browse food and menu prices, submit pickup or Yango delivery requests, track orders, request catering, check quotes, and buy or download published recipes and cookbooks. |
| Business dashboard | Edit the menu, set daily order limits, manage orders and catering bookings, and record payments after checking that they were received. Publish recipe or cookbook PDFs and issue protected download codes. |
| Kitchen board | See confirmed meals, start preparation and mark tickets ready. Uses separate staff credentials. |

Owner and kitchen routes require separate credentials. The customer site does not expose contact details submitted with orders or inquiries to other customers. Payment records are checked manually by the owner. Live merchant collection is pending provider configuration.

## Run it on Windows

From the repository root, double-click **Start Chèf Percy.cmd**. The launcher uses the configured local PostgreSQL database, applies migrations, and opens the customer menu and owner dashboard in the browser. Keep the launcher open. Use the credentials printed in its window to access the owner or kitchen tools.

| Local page | Address |
| --- | --- |
| Customer menu | http://127.0.0.1:8000/#/menu |
| Business dashboard | http://127.0.0.1:8000/owner |
| Kitchen board | http://127.0.0.1:8000/kitchen |

The app uses Vue 3, TypeScript, Vite, FastAPI, SQLAlchemy, Alembic, and PostgreSQL. Source and build output live in `kitchen-app/`. See the [setup and operations guide](kitchen-app/README.md) for prerequisites, migrations, roles, API details and hosting.

The root `index.html` is the original [static GitHub Pages demo](https://joshuaalinanichishimba-cmyk.github.io/chef-percys-kitchen-demo/). Run the application locally or deploy FastAPI and PostgreSQL to use the current ordering and business tools.
