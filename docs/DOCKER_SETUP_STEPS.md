# DairyPro Docker Setup

This document records the Docker setup for running DairyPro on the local
computer and testing it from an iPhone on the same Wi-Fi network.

## 1. Prerequisites

- Docker Engine with Docker Compose v2
- A working internet connection for downloading Docker images and packages
- The computer and iPhone connected to the same Wi-Fi network

Check Docker:

```bash
docker --version
docker compose version
```

## 2. Configure the environment

Run these commands from the repository root:

```bash
cd /home/xanders/Documents/Plus_Docker/Project
cp backend/.env.example backend/.env
cp .env.example .env
```

The backend `.env` must contain a unique `DAIRYPRO_SECRET_KEY`. The current
local file has one configured already. Keep this file private and do not
commit it.

For iPhone testing, the root `.env` uses the computer's current LAN address:

```env
VITE_API_URL=http://192.168.8.171:8000
```

The backend CORS allow-list includes the Docker frontend origin and the LAN
origin:

```env
DAIRYPRO_CORS_ORIGINS=http://localhost,http://127.0.0.1,http://192.168.8.171,http://localhost:5173,http://127.0.0.1:5173
```

If the computer receives a different LAN address later, update both the
`VITE_API_URL` value and the matching CORS origin, then rebuild the frontend.

## 3. Build and start Docker

```bash
docker compose up --build -d
```

The `-d` option leaves the services running in the background. To watch logs:

```bash
docker compose logs -f
```

## 4. Verify the services

Check container status:

```bash
docker compose ps
```

Check the backend:

```bash
curl http://localhost:8000/api/health
```

Expected response:

```json
{"status":"ok"}
```

Open the desktop application at <http://localhost> and the API documentation
at <http://localhost:8000/docs>.

## 5. Open it on an iPhone

1. Connect the iPhone to the same Wi-Fi as the Docker computer.
2. Open `http://192.168.8.171` in Safari.
3. Register the first account; it becomes the administrator account.

The Docker host firewall must allow inbound TCP traffic on ports `80` and
`8000`. Do not use `localhost` on the iPhone because it refers to the phone
itself.

## 6. Stop and restart

Stop the services while preserving application data:

```bash
docker compose down
```

Restart without rebuilding:

```bash
docker compose up -d
```

Use `docker compose down -v` only when intentionally deleting the named
SQLite and application-data volumes.

## 7. Data and production notes

The default deployment uses SQLite in the `dairypro_data` named volume and
uploads/email logs in `dairypro_var`. These volumes survive normal container
recreation.

The LAN URL is for testing. A production deployment should use a domain,
HTTPS, a reverse proxy such as Caddy, and a production SMTP provider. HTTPS
is also required for reliable PWA/offline functionality on iPhone.