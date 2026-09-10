# DairyPro — API Documentation

## 1. Overview

- **Base URL**: `http://localhost:8000` in development (see `VITE_API_URL`).
- **Format**: JSON request/response bodies.
- **Auth**: Bearer JWT in the `Authorization` header for every endpoint
  except `/api/auth/register` and `/api/auth/login`.
- **Interactive docs**: FastAPI auto-generates Swagger UI at `/docs` and
  ReDoc at `/redoc`, and the raw OpenAPI schema at `/openapi.json`, for
  any running instance.

Authenticate in Swagger UI: call `/api/auth/login`, copy `access_token`
from the response, click **Authorize**, paste the token in.

## 2. Authentication — `/api/auth`

### `POST /api/auth/register`
Registers a new user (or activates a previously-invited one). The first
user ever registered becomes `admin`; everyone after defaults to `staff`.

```json
// Request
{ "email": "you@farm.com", "password": "at-least-6-chars", "full_name": "Jane Farmer" }

// Response 200
{
  "access_token": "eyJhbGciOi...",
  "token_type": "bearer",
  "user": { "id": "...", "email": "...", "full_name": "...", "role": "admin", "created_date": "..." }
}
```
`400` if an already-activated account exists with that email.

### `POST /api/auth/login`
```json
// Request
{ "email": "you@farm.com", "password": "..." }
// Response: same shape as register
```
`401` on bad credentials.

### `GET /api/auth/me`
Returns the current user (from the bearer token). `401` if missing/invalid.

### `POST /api/auth/logout`
No-op (JWTs are stateless — the client just discards the token).

## 3. Users — `/api/users` (admin-only for invite/update/delete)

### `GET /api/users`
List all users (any authenticated user can list; used by Settings → Users).

### `POST /api/users/invite`
```json
{ "email": "new@farm.com", "full_name": "New Person", "role": "staff" }
```
Creates a user record with no password (activated later via
`/api/auth/register` using the same email) and sends an invite email.
Requires `admin`.

### `PUT /api/users/{user_id}`
```json
{ "role": "manager" }
```
Requires `admin`.

### `DELETE /api/users/{user_id}`
Requires `admin`.

## 4. Entities — `/api/entities/{entity_type}`

One generic router backs all 19 logical entities (see [Database
Design §2](./DATABASE_DESIGN.md#2-logical-entity-data-dictionary) for the
allowed `entity_type` values and each one's expected fields).

### `GET /api/entities/{entity_type}?sort=-created_date&limit=500`
- `sort`: optional, a field name, prefixed with `-` for descending.
  `created_date` sorts on the real column; any other value sorts via
  `json_extract` on the JSON payload.
- `limit`: optional, default 1000, max 5000.
- Returns an array of the entity's records, each with its `data` fields
  flattened to the top level plus `id`, `created_date`, `updated_date`,
  `created_by_id`, `created_by`.

### `GET /api/entities/{entity_type}/{id}`
Single record. `404` if not found.

### `POST /api/entities/{entity_type}`
Body: a JSON object of the entity's fields (see the data dictionary).
`403` if the entity is admin/manager-write-only (`Settings`, `MilkPrice`,
`CategorySettings`) and the caller isn't `admin`/`manager`.

### `PUT /api/entities/{entity_type}/{id}`
Body: a partial JSON object — fields are merged into the existing record,
not replaced wholesale. Same write-permission rule as `POST`.

### `DELETE /api/entities/{entity_type}/{id}`
`404` if not found.

Every entities endpoint returns `404` for an unrecognized `entity_type`.

## 5. Integrations — `/api/integrations`

### `POST /api/integrations/send-email`
```json
{ "to": "manager@farm.com", "subject": "...", "body": "..." }
```
Sends via SMTP if configured; otherwise logs to
`backend/var/sent_emails.log` and returns `{"status": "logged", ...}`.

### `POST /api/integrations/upload-file` (multipart/form-data, field `file`)
Saves the file under `backend/var/uploads` and returns
`{"file_url": "/api/files/<generated-name>"}`.

### `POST /api/integrations/invoke-llm`
```json
{ "prompt": "...", "response_json_schema": { "type": "object", "properties": {} } }
```
Calls the Anthropic Messages API if `ANTHROPIC_API_KEY` is set and parses
the response as JSON matching the given schema; otherwise returns
`{"_ai_unavailable": true, "message": "..."}`.

### `POST /api/integrations/page-view`
```json
{ "page": "Dashboard" }
```
Fire-and-forget analytics logging; failures are non-fatal on the frontend.

## 6. Analytics — `/api/analytics`

All of these compute directly from stored records — no LLM required
unless noted.

| Endpoint | Method | Description |
|---|---|---|
| `/milk-forecast` | GET | 12-month history + next-month forecast (linear regression), trend label |
| `/health-risk` | GET | Per-cow risk score (0-100) from recent treatment frequency |
| `/breeding-optimizer` | GET | Re-breeding recommendations based on days since last breeding event |
| `/insights` | GET | Combines all three above into one summary payload |
| `/ai-insights` | POST | Same as `/insights` plus an LLM-written narrative (requires `ANTHROPIC_API_KEY`; falls back to the plain summary otherwise) |

## 7. Error format

FastAPI's default error shape:
```json
{ "detail": "Human-readable message" }
```
or, for validation errors, a `detail` array of field-level issues. The
frontend never shows this raw JSON to the user — see
[UI/UX Documentation — Error States](./UI_UX_DOCUMENTATION.md#7-error-states).

## 8. Rate limiting / pagination

Not implemented. `limit` on the entities list endpoint is the only
volume control. See [Architecture §7](./ARCHITECTURE.md#7-known-trade-offs)
for the scaling implications.
