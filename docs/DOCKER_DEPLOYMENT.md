# DairyPro — Docker Deployment Guide

## 1. What's included

| File | Purpose |
|---|---|
| `backend/Dockerfile` | Python 3.11-slim image running the FastAPI app via `uvicorn` |
| `frontend/Dockerfile` | Multi-stage: `node:20-alpine` builds the static assets, `nginx:1.27-alpine` serves them |
| `frontend/nginx.conf` | SPA routing fallback, gzip, correct no-cache headers for `sw.js`/`manifest.json` so PWA updates actually propagate |
| `docker-compose.yml` | Orchestrates both containers, with named volumes for persistent data and an optional (commented-out) Postgres service |
| `backend/.dockerignore`, `frontend/.dockerignore` | Keep build contexts small and avoid baking secrets/`node_modules`/`venv` into images |
| `.env.example` (repo root) | The one variable `docker-compose` itself needs (`VITE_API_URL`, for the frontend build) |

Two supporting code changes were made to actually back the Postgres option
this guide offers (rather than just documenting something that would
break): `backend/app/database.py` now honors a `DATABASE_URL` env var if
set, and `backend/app/routers/entities.py`'s sort logic is now
dialect-aware (SQLite's `json_extract` vs. Postgres's
`json_extract_path_text`) — sorting by a JSON field now works on either
database, not just SQLite.

## 2. Prerequisites

- Docker Engine 24+ and Docker Compose v2 (`docker compose`, not the
  older standalone `docker-compose` — the compose file uses the modern
  schema with no `version:` key, which recent Compose versions expect).

## 3. Quick start (SQLite, single machine)

```bash
git clone <your-repo-url> dairypro && cd dairypro

cp backend/.env.example backend/.env
# edit backend/.env — at minimum, set DAIRYPRO_SECRET_KEY to a long random string

cp .env.example .env
# edit .env — set VITE_API_URL to how the browser will reach the backend
# (for a same-machine try-it-out, http://localhost:8000 is fine)

docker compose up --build
```

- Frontend: `http://localhost`
- Backend API + docs: `http://localhost:8000/docs`

Register the first account through the frontend — it automatically
becomes `admin`. Stop with Ctrl+C; restart later with
`docker compose up` (no `--build` needed unless code changed).

## 4. Understanding VITE_API_URL in Docker

This is the single most common thing people get wrong with this setup:
**`VITE_API_URL` is baked into the frontend's JavaScript at build time**,
not read at container start. It must be a URL the browser can reach —
not the Docker-internal service name.

- Wrong: `VITE_API_URL=http://backend:8000` — this only resolves inside
  the Docker network; a browser on your laptop has no idea what "backend"
  means.
- Right (local trial): `VITE_API_URL=http://localhost:8000`.
- Right (production): `VITE_API_URL=https://api.yourfarm.com`, once the
  backend has a real public URL (§6).

If you change `VITE_API_URL`, you must rebuild the frontend image:
```bash
docker compose build frontend
docker compose up -d frontend
```

## 5. Data persistence

Two named volumes carry all durable state across container
restarts/recreations:

| Volume | Mounted at | Contains |
|---|---|---|
| `dairypro_data` | `/app/data` (backend) | The SQLite database file (`dairypro.db`), if you're not using Postgres |
| `dairypro_var` | `/app/var` (backend) | Uploaded files and the fallback email log (`sent_emails.log`) when SMTP isn't configured |

Backup:
```bash
docker run --rm -v dairypro_data:/data -v $(pwd):/backup alpine \
  tar czf /backup/dairypro-data-backup.tar.gz -C /data .
```
Restore: extract that tarball back into a fresh `dairypro_data` volume
the same way, in reverse.

## 6. Running it on a real server (production)

The compose setup above serves the frontend over plain HTTP on port 80 and
the backend on port 8000 — fine for local trial, not sufficient for
production. You need HTTPS, both because credentials shouldn't travel
over plain HTTP and because PWA installability and offline logging
require it (see the Mobile Deployment guide's prerequisites section).

The simplest way to add HTTPS to this compose setup is a reverse proxy
that handles certificates automatically. Caddy is the least-config
option:

```yaml
# add to docker-compose.yml
  caddy:
    image: caddy:2-alpine
    restart: unless-stopped
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./Caddyfile:/etc/caddy/Caddyfile
      - caddy_data:/data
    depends_on:
      - backend
      - frontend

volumes:
  caddy_data:
```

```
# Caddyfile
yourfarm.com {
    reverse_proxy /api/* backend:8000
    reverse_proxy frontend:80
}
```

Then remove the `ports:` mappings from the `backend` and `frontend`
services (Caddy talks to them over the internal Docker network instead),
point your domain's DNS at the server, and rebuild the frontend with
`VITE_API_URL=https://yourfarm.com` (since `/api/*` is now proxied on the
same domain). Caddy obtains and renews a Let's Encrypt certificate
automatically — no manual certbot steps.

If you'd rather use Traefik or nginx-proxy + certbot, the same principle
applies: put the TLS-terminating proxy in front of both containers over
the internal Docker network, and stop publishing their ports directly.

## 7. Switching to Postgres

1. Uncomment the `postgres` service and the `dairypro_postgres` volume in
   `docker-compose.yml`.
2. In `backend/.env`, set:
   ```
   DATABASE_URL=postgresql://dairypro:dairypro@postgres:5432/dairypro
   ```
   (change the username/password to match what you set on the `postgres`
   service, and don't reuse the example credentials in production).
3. `docker compose up --build` — the backend now writes to Postgres
   instead of the SQLite file. The `dairypro_data` volume is simply
   unused in this mode (safe to leave mounted or remove it).

This is a one-way move for existing data — there is no built-in
SQLite-to-Postgres migration tool. If you have existing SQLite data you
need in Postgres, export/import it manually (e.g. via a small script
that reads the SQLite `records`/`users` tables and re-inserts them) before
cutting over.

## 8. Updating a running deployment

```bash
git pull
docker compose build
docker compose up -d
```
Both containers restart with the new code; named volumes (and therefore
your data) are untouched. There is no automated database migration tool
(see the Database Design doc's migration notes) — schema-shape changes to
logical entities need none (they're just JSON), but changes to the
`users`/`page_views` tables would need manual handling.

## 9. Logs and troubleshooting

```bash
docker compose logs -f backend
docker compose logs -f frontend
docker compose ps        # check both containers report "healthy"
```

| Symptom | Likely cause |
|---|---|
| Frontend loads but every request fails | `VITE_API_URL` wasn't rebuilt into the frontend image, or doesn't match the backend's actual public URL (§4) |
| `docker compose up` fails on the backend healthcheck | Check `docker compose logs backend` — commonly a missing/invalid `DAIRYPRO_SECRET_KEY` or a `DATABASE_URL` typo |
| Data disappeared after `docker compose down` | You ran `docker compose down -v`, which deletes named volumes — use `docker compose down` (no `-v`) to stop containers while keeping data |
| Can't install as a PWA / offline logging doesn't work | You're accessing it over plain HTTP — see §6, HTTPS is required |

## 10. Building images without Compose

If you just want the images themselves (e.g. to push to a registry):

```bash
docker build -t dairypro-backend ./backend
docker build -t dairypro-frontend --build-arg VITE_API_URL=https://api.yourfarm.com ./frontend
```
