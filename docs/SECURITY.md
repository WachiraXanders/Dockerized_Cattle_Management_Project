# DairyPro — Security Documentation

## 1. Authentication

- Passwords are hashed with **PBKDF2-HMAC-SHA256**, 100,000 iterations,
  a unique random salt per user (`backend/app/security.py`). Plaintext
  passwords are never stored or logged.
- Sessions are **stateless JWTs** (HS256), default 7-day expiry
  (`DAIRYPRO_TOKEN_EXPIRE_DAYS`). Logout is client-side only (the token is
  discarded) — there is no server-side revocation list, so a leaked token
  remains valid until it expires.
- The JWT signing secret (`DAIRYPRO_SECRET_KEY`) defaults to a placeholder
  value in `.env.example`. **This must be changed to a long random string
  before any non-local deployment** — anyone who knows the default could
  forge valid tokens.

## 2. Authorization

- Four roles: `admin`, `manager`, `staff`, `viewer` (see the SRS §3 for
  the full matrix).
- **Enforced in two places, by design:**
  1. **Frontend** (`src/lib/permissions.js`): hides navigation items and
     disables actions the current role can't perform. This is a UX
     convenience, not a security boundary.
  2. **Backend** (`routers/entities.py`, `deps.require_role`): the actual
     security boundary. Write access to `Settings`, `MilkPrice`, and
     `CategorySettings` is rejected server-side (`403`) for non-admin/
     manager roles regardless of what the frontend sends. User management
     endpoints (`invite`/update role/delete) require `admin` via the
     `require_role` dependency.
- **Known gap**: most entity types (Cattle, MilkProduction, HealthRecord,
  etc.) do not have per-entity server-side write restrictions beyond
  "any authenticated user can write" — the `staff`/`viewer` distinction
  for these is currently UI-only. A `viewer`-role user who crafts a raw
  API request could create/edit/delete records the UI would prevent them
  from touching. Closing this gap (server-side write checks per entity
  per role, not just for the three admin-write entities) is a recommended
  hardening item before exposing this to untrusted staff.

## 3. Data access model

All authenticated users can **read** all farm records — there is no
per-user row-level isolation (see the Architecture doc's Data Ownership
Model section for the rationale). This is appropriate for a single farm's
internal team but means the deployment is not multi-tenant-safe: never
point two different farms' frontends at the same backend instance.

## 4. Transport security

The application does not terminate TLS itself — `uvicorn`/`gunicorn` is
expected to run behind a TLS-terminating reverse proxy (nginx, Caddy, a
managed platform's load balancer) in any non-local deployment. CORS
origins are restricted via `DAIRYPRO_CORS_ORIGINS` (defaults to
`localhost` only).

## 5. Secrets management

| Secret | Where it lives | Notes |
|---|---|---|
| `DAIRYPRO_SECRET_KEY` | Backend `.env` | JWT signing key — rotate periodically; rotating invalidates all existing sessions |
| `ANTHROPIC_API_KEY` | Backend `.env` | Optional; enables LLM-backed insights |
| `SMTP_*` | Backend `.env` | Optional; enables real outbound email |
| Database file | `backend/dairypro.db` (SQLite) | Contains all farm data including password hashes — back it up securely and never commit it to version control |

No secrets are ever sent to the frontend; the frontend only ever holds the
short-lived JWT for the logged-in user.

## 6. Input validation

- FastAPI/Pydantic validate request shapes at the API boundary (e.g. email
  format on register/login; password minimum length is enforced
  client-side at 6 characters — not currently re-validated server-side,
  a gap worth closing).
- The generic entities endpoint accepts arbitrary JSON for an entity's
  `data` field — there is no server-side schema validation per entity
  type. Malformed or unexpected fields are stored as-is; this is a
  direct consequence of the schema-less design (see the Architecture
  doc's Known Trade-offs section) and means data integrity relies on the
  frontend forms behaving correctly, not on the API rejecting bad input.

## 7. Never-store data classes

Per this project's data-handling policy, the following are never
persisted by design, regardless of what a user might submit: government
ID numbers, payment card/bank account numbers, and other categories of
sensitive personal data unrelated to farm operations. The application's
own entity schemas (see Database Design) do not include fields for these,
so this is enforced by omission rather than active filtering.

## 8. Known vulnerabilities / hardening backlog

1. No password-reset flow — an admin must manually intervene (Settings ->
   Users) if a user forgets their password; there is no "forgot password"
   email flow.
2. No rate limiting on `/api/auth/login` — brute-force protection is not
   implemented.
3. No server-side password complexity/length re-validation.
4. No per-entity role enforcement beyond the three admin-write entities
   (see §2 above).
5. No audit trail of who changed what beyond `created_by_id` on the
   original record — updates do not record who made the change or a
   history of prior values.
6. No CSRF concern in the traditional sense (the API is token-based, not
   cookie-session-based), but confirm any reverse-proxy configuration
   doesn't inadvertently enable cookie-based auth without CSRF protection
   if that's ever added.
7. Default JWT secret and default admin-invite email templates should be
   reviewed before production use.

## 9. Incident response

Not yet formalized. At minimum, on suspected credential compromise:
rotate `DAIRYPRO_SECRET_KEY` (invalidates all sessions immediately),
force-reset the affected user's password via direct database update or
the Settings -> Users flow, and review `page_views`/application logs for
suspicious activity (note: `page_views` currently only logs page
navigation, not entity-level access, so forensic value is limited).
