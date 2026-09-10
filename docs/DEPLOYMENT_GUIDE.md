# DairyPro — Deployment Guide

## 1. Prerequisites

- Python 3.10+
- Node.js 18+ and npm
- (Optional) an SMTP account for real outbound email
- (Optional) an Anthropic API key for LLM-backed insights

## 2. Local development

### 2.1 Backend
```bash
cd backend
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env             # edit as needed — see §4
uvicorn app.main:app --reload --port 8000
```
The first person to register through the frontend becomes `admin`.
Interactive API docs are available at `http://localhost:8000/docs`.

### 2.2 Frontend
```bash
cd frontend
npm install
cp .env.example .env             # VITE_API_URL, defaults to http://localhost:8000
npm run dev
```
Open `http://localhost:5173`.

## 3. Environment variables

### Backend (`backend/.env`)
| Variable | Default | Notes |
|---|---|---|
| `DAIRYPRO_SECRET_KEY` | placeholder | Change before any non-local deployment — see the Security doc |
| `DAIRYPRO_TOKEN_EXPIRE_DAYS` | `7` | JWT lifetime |
| `DAIRYPRO_CORS_ORIGINS` | `http://localhost:5173,http://127.0.0.1:5173` | Comma-separated allow-list |
| `DAIRYPRO_DB_PATH` | `./dairypro.db` | SQLite file path; irrelevant if you swap the connection string for another database |
| `ANTHROPIC_API_KEY` | unset | Enables AI insights; without it, the app falls back to a clear "not configured" message |
| `ANTHROPIC_MODEL` | `claude-sonnet-4-5` | |
| `SMTP_HOST` / `SMTP_PORT` / `SMTP_USER` / `SMTP_PASSWORD` / `SMTP_FROM` / `SMTP_TLS` | unset | Without these, email is logged to `backend/var/sent_emails.log` instead of sent |

### Frontend (`frontend/.env`)
| Variable | Default | Notes |
|---|---|---|
| `VITE_API_URL` | `http://localhost:8000` | Must point at your deployed backend for a production build |

## 4. Production deployment

### 4.1 Backend
Run as any ASGI application:
```bash
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000
# or, for multiple workers behind a process manager:
gunicorn app.main:app -k uvicorn.workers.UvicornWorker -w 4 -b 0.0.0.0:8000
```
Put a TLS-terminating reverse proxy (nginx, Caddy, or your platform's load
balancer) in front of it — the app itself does not terminate TLS. Set
`DAIRYPRO_CORS_ORIGINS` to your actual frontend origin(s).

**Database**: SQLite works out of the box with zero configuration. For
concurrent multi-user production use, switch to Postgres by changing
`SQLALCHEMY_DATABASE_URL` in `backend/app/database.py` (or making it
read from an environment variable) — no other code changes are required
since the generic entity store uses only standard SQLAlchemy/JSON
operations.

### 4.2 Frontend
```bash
cd frontend
npm run build      # outputs to frontend/dist
```
Deploy `frontend/dist` to any static host (Vercel, Netlify, Cloudflare
Pages, S3+CloudFront, etc.), with `VITE_API_URL` set to your backend's
public URL at build time (Vite inlines env vars into the build).

### 4.3 Recommended platform pairings
- Backend: a small VM, Render, Railway, or Fly.io.
- Frontend: Vercel, Netlify, or Cloudflare Pages.

## 5. Seeding test data

`backend/seed_demo_data.py` populates a running backend via its own API
with a large, cross-referenced dataset (cattle, groups, vendors,
inventory, months of milk prices/production, health and breeding records,
stock adjustments, tasks, transactions, and more):

```bash
cd backend
source venv/bin/activate
python seed_demo_data.py --email admin@farm.com --password test1234
# roughly double every entity's volume:
python seed_demo_data.py --email admin@farm.com --password test1234 --scale 2.0
```

It is not idempotent — running it twice duplicates records — so use a
fresh database file (delete `dairypro.db` and restart the backend) or a
different `--email` to reset between runs.

## 6. Backups

The entire application state lives in one SQLite file
(`backend/dairypro.db` by default). Back it up with a simple file copy on
a schedule appropriate to your farm's data-entry volume — there is no
built-in backup tooling. If you migrate to Postgres, use its standard
backup tooling (`pg_dump`, managed-platform snapshots) instead.

## 7. Monitoring / logs

- Application logs: whatever your process manager/platform captures from
  `uvicorn`'s stdout/stderr.
- Email fallback log: `backend/var/sent_emails.log` (only populated when
  SMTP isn't configured).
- No structured application-level logging or external monitoring
  integration is currently wired in — see the Security doc's Incident
  Response section for the current (limited) forensic surface.

## 8. Rollback

There is no automated release/rollback tooling. Roll back by redeploying
the previous backend/frontend build artifacts; since there is no formal
database migration tool, a schema-incompatible rollback would require
manual data reconciliation — in practice, changes to the generic `Record`
store rarely require this since entity shapes are just JSON.
