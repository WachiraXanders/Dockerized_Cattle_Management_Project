# Docker Fixes Applied

This file records the problems found while bringing the project up with
Docker Compose and the fixes applied.

## 1. Missing npm lockfile

### Error

```text
The `npm ci` command can only install with an existing package-lock.json
```

### Cause

The frontend contained `package.json` but no `package-lock.json`. `npm ci`
requires a lockfile and will not resolve dependencies from `package.json`
alone.

### Fix

Changed `frontend/Dockerfile` from:

```dockerfile
RUN npm ci
```

to:

```dockerfile
RUN npm install
```

This allows the current repository to build without a committed lockfile.

## 2. Slow package downloads

### Error

Pip timed out while downloading packages from `pypi.org` and
`files.pythonhosted.org`.

### Cause

The dependency definitions were valid, but the network connection was slow or
intermittent. The build eventually succeeded after retrying.

### Resolution

Retry the build when the connection is stable. No application dependency was
removed to hide the problem.

## 3. Docker Hub connection failures

### Errors

```text
TLS handshake timeout
failed to fetch anonymous token
lookup auth.docker.io ... i/o timeout
```

### Cause

Docker could not consistently reach Docker Hub to download `python:3.11-slim`,
`node:20-alpine`, and `nginx:1.27-alpine`.

### Resolution

Retry image pulls/builds after network or DNS connectivity is restored:

```bash
docker pull python:3.11-slim
docker compose build
```

The host-side `curl` check reaching Docker Hub confirmed that the endpoint
was available when the network was functioning.

## 4. Fixed container-name conflicts

### Error

```text
Conflict. The container name "/dairypro-backend" is already in use
```

The same conflict then appeared for `/dairypro-frontend`.

### Cause

Old containers from another DairyPro Compose project were still running with
the same explicit container names.

### Fix

Removed only the stale containers:

```bash
docker rm -f dairypro-backend dairypro-frontend
```

The named data volumes were not removed. The current project then recreated
both containers successfully.

## 5. LAN access configuration

### Problem

The frontend was built with `VITE_API_URL=http://localhost:8000`. That works
on the Docker computer but makes an iPhone call the API on the iPhone itself.

### Fix

Configured the current LAN address in the root `.env`:

```env
VITE_API_URL=http://192.168.123.44:8000
```

Added `http://192.168.123.44` to backend CORS and rebuilt the frontend image.

## 6. Final verification

The following checks succeeded:

```bash
curl http://localhost:8000/api/health
curl -I http://localhost/
```

The backend returned `{"status":"ok"}` and Nginx returned HTTP `200 OK`.