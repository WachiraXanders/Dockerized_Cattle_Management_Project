# DairyPro — Maintenance & Operations Guide

Audience: whoever is responsible for keeping a running DairyPro instance
healthy after deployment.

## 1. Routine maintenance

| Task | Frequency | How |
|---|---|---|
| Database backup | Daily (or per your data-loss tolerance) | Copy `backend/dairypro.db` (or run your Postgres backup tool if migrated) |
| Dependency updates | Periodically | `pip list --outdated` / `npm outdated`; review changelogs before bumping, especially FastAPI/SQLAlchemy/React major versions |
| Log review | Weekly, or after any incident | Check your process manager's captured stdout/stderr, and `backend/var/sent_emails.log` if SMTP isn't configured |
| Disk usage check | Periodically | `backend/var/uploads` and the SQLite file both grow unboundedly with no automatic cleanup |
| Secret rotation | Per your security policy | Rotating `DAIRYPRO_SECRET_KEY` invalidates all active sessions — plan for users needing to log in again |

## 2. Health checks

- `GET /api/health` returns `{"status": "ok"}` — suitable for a basic
  uptime/liveness probe.
- There is no separate readiness probe distinguishing "process is up" from
  "database is reachable" — a failing database connection will surface as
  errors on the first real request rather than a dedicated health-check
  failure.

## 3. Common operational tasks

### Reset a user's password
There is no self-service flow yet. As an admin:
1. Go to Settings → Users and remove the user, then re-invite them, or
2. Directly update the `password_hash` column via a database console using
   the same hashing scheme as `backend/app/security.py::hash_password`
   (not recommended unless you're comfortable with this — prefer option 1).

### Promote/demote a user's role
Settings → Users → change their role in the dropdown. Takes effect on
their next request (JWTs don't carry role, so no re-login is needed).

### Recover from a bad data entry
Most entities can be edited or deleted directly from their page. For
entities that cascade elsewhere (e.g. a milk record that auto-created a
Transaction), deleting the original record does not delete the
auto-created transaction — clean that up manually in Finance if needed
(see the SRS's Milk Production section and the known limitation noted
there).

### Clear the offline sync queue
If a user's browser has stuck offline-queue entries that keep failing to
sync (e.g. because the referenced cow was deleted before they came back
online), the cleanest fix today is clearing that browser's IndexedDB for
the site (devtools → Application → IndexedDB → delete the `dairypro_offline`
database) — there's no in-app "clear failed items" control yet.

### Re-run the demo/seed data
See the Deployment Guide's seeding section. Only use this against a
non-production database.

## 4. Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| `ModuleNotFoundError: email_validator` on backend startup | Missing optional Pydantic dependency | `pip install email-validator` (already pinned in `requirements.txt` going forward) |
| Frontend can't reach the API (network errors) | `VITE_API_URL` misconfigured or CORS rejecting the origin | Check `.env`, and `DAIRYPRO_CORS_ORIGINS` on the backend |
| "AI insights are not configured" | `ANTHROPIC_API_KEY` unset | Expected behavior without a key — set it if you want this feature |
| Emails not arriving | SMTP not configured | Check `backend/var/sent_emails.log` — if entries appear there, SMTP simply isn't set up; configure `SMTP_*` env vars |
| Milk income showing as 0 for a month | No `MilkPrice` set for that month | Set it in Finance → Milk Prices or Milk Production → Set Price |
| A `staff`/`viewer` user can do something they shouldn't | Server-side write checks only cover `Settings`/`MilkPrice`/`CategorySettings` today | See the Security doc's Authorization section — known gap, not a bug |
| Duplicate expense transactions after clicking "Sync Costs Now" twice | Should not happen — sync is deduplicated by reference tag | Check the transactions' `reference` field; if genuinely duplicated, file it as a bug |

## 5. Scaling triggers — when to act

- **Slow list pages / large payloads**: once any entity's row count grows
  into the tens of thousands, the lack of server-side pagination (see the
  Architecture doc's Known Trade-offs) will start to show. Add pagination
  to `routers/entities.py` before this becomes a user-facing problem.
- **Write contention / "database is locked" errors**: SQLite is
  single-writer. Migrate to Postgres (one connection-string change) once
  you have concurrent multi-user write load causing lock contention.
- **Growing `backend/var/uploads`**: no automatic cleanup exists; add a
  retention policy or move to object storage if upload volume grows.

## 6. Extending the system

- **New entity type**: add it to `ENTITY_TYPES` (and `ADMIN_WRITE_ENTITIES`
  if it needs restricted writes) in `backend/app/routers/entities.py`, add
  it to `ENTITY_NAMES` in `frontend/src/api/entities.js`, and build a page
  or extend an existing one — no database migration needed.
- **New role or permission**: edit `frontend/src/lib/permissions.js`
  (`PAGE_ACCESS`, `SETTINGS_TAB_ACCESS`, `PERMISSION_MATRIX`) and add
  corresponding server-side checks if the new permission needs to be a
  real security boundary, not just a UI convenience (see the Security
  doc's Authorization section).
