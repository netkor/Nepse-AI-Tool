# About This Project

Project: Nepse AI Tool

Overview
--------
This repository implements the "Nepse AI Tool" — a stock/market signals, alerts, and watchlist web application focused on the NEPSE market. It contains a Django backend that gathers, processes, and serves stock data and signals, plus a React + Vite frontend for the user-facing UI. The project includes Docker configuration for local deployment and a simple scheduler + Telegram integration for automated alerts.

Purpose
-------
- Provide automated signals and alerts for NEPSE-listed stocks.
- Offer a lightweight web UI to view signals, watchlists, and account features.
- Integrate with Telegram to push real-time alerts to users.

Key Features
------------
- Django backend with modular apps: `accounts`, `alerts`, `signals`, `stocks`, and `signals`.
- React + Vite frontend in `nepse_frontend` with pages for Dashboard, Login, Register, Watchlist, and Signals.
- Data ingestion pipeline and `stocks/data_provider.py` for fetching stock data.
- Scheduled/background jobs via `nepse_backend/scheduler.py` to update prices and run signal generation.
- Telegram integration in `nepse_backend/telegram_service.py` to push alerts.
- Management command `seed_stock_data.py` to pre-populate stock data for development.
- Docker and docker-compose for containerized deployment.

Repository Layout (important paths)
----------------------------------
- `nepse_backend/` — Django project and apps (backend API, scheduler, telegram service).
  - `manage.py` — Django manage utility.
  - `db.sqlite3` — default development DB (SQLite).
  - `nepse_backend/settings.py` — Django settings.
  - `nepse_backend/scheduler.py` — scheduler integration.
  - `nepse_backend/telegram_service.py` — Telegram notification helpers.
  - Apps: `accounts/`, `alerts/`, `signals/`, `stocks/`, `signals/` (each with models, serializers, views).
- `nepse_frontend/` — frontend SPA (React + Vite).
  - `src/` — app source (components, pages, API wrappers, context, hooks).
- `docker-compose.yml` — orchestration for local/dev deployment.

Tech Stack
----------
- Backend: Python, Django REST Framework, SQLite for local development.
- Frontend: React, Vite, Tailwind CSS.
- Deployment: Docker + docker-compose (Dockerfiles present for frontend and backend).
- Integrations: Telegram (bot/service), scheduled tasks (internal scheduler module).

What’s Used (libraries and tools)
--------------------------------
- `requirements.txt` / `requirements_prod.txt` — Python dependencies for the Django backend.
- `package.json` — Node dependencies for the frontend (React, Vite, Tailwind).
- Management commands and Django migrations are included under each app's `migrations/` folder.

How To Run (quick start)
------------------------
For development, two common approaches exist: docker-compose or running services locally.

Docker (recommended):

1. Build and run with docker-compose:

```
docker-compose up --build
```

2. Services exposed depend on `docker-compose.yml` — check ports and env variables there.

Local dev (backend + frontend separately):

Backend (Python/Django):

```
cd nepse_backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

Frontend (React/Vite):

```
cd nepse_frontend
npm install
npm run dev
```

Notes
-----
- Default local DB is SQLite (`nepse_backend/db.sqlite3`) for convenience. Use Postgres or another production DB for deployments.
- Environment variables (e.g., Telegram bot token, Django `SECRET_KEY`, DB URL) should be configured securely in production — avoid committing secrets.

Architecture Overview
---------------------
- The backend exposes a REST API consumed by the frontend's `api` layer (`nepse_frontend/src/api`).
- The `stocks` app is responsible for fetching and storing price data. Signal generation lives under `signals` and `alerts` apps which can run on a schedule.
- The scheduler module in `nepse_backend/scheduler.py` runs periodic tasks; it can be mapped to a cron job, Celery beat, or a process that uses `APScheduler` in production.
- Telegram service centralizes user notifications; it's used by `alerts` and the scheduler to deliver real-time messages.

Potential and Roadmap
---------------------
- Replace SQLite with a production-grade DB (Postgres) and add migration support.
- Add Celery + Redis for robust background processing and scaling.
- Add authentication improvements (JWT, OAuth) and user profiles.
- Add persistence and history for signals, with analytics dashboards.
- Add unit/integration tests and CI pipeline.
- Add continuous deployment via GitHub Actions, and container registry hosting.

Contribution Guide
------------------
- Fork the repo, create a branch for your feature, and open a pull request.
- Run linters and tests before submitting. Keep changes focused and documented.
- If adding new settings or tokens, use environment variables and document them in `README.md` or a `.env.example`.

Development Notes
-----------------
- A seed command exists at `stocks/management/commands/seed_stock_data.py` to populate dev data.
- Check `nepse_backend/urls.py` and `nepse_frontend/src/api/index.js` to see how endpoints are wired.

Contact and Support
-------------------
If you need help setting this up, run the local steps above and open issues describing the problem, or reach out to the repository maintainer.

License
-------
Check `README.md` for licensing information. If none provided, add an appropriate open-source license before publishing.

--
This document summarizes the current repository structure, how to run the project, and suggested next steps to take it from a dev setup to a more production-ready system.
