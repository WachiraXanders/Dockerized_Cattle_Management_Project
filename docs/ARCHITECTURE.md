# DairyPro — System Architecture Document

## 1. Overview

```
┌─────────────────────┐        HTTPS/JSON        ┌──────────────────────────┐
│   React Frontend     │ ───────────────────────▶ │   FastAPI Backend        │
│   (Vite + Tailwind)  │ ◀─────────────────────── │   (Python 3, Uvicorn)    │
└─────────────────────┘                           └────────────┬─────────────┘
                                                                 │ SQLAlchemy
                                                                 ▼
                                                    ┌──────────────────────────┐
                                                    │   SQLite (default) /     │
                                                    │   any SQLAlchemy DB      │
                                                    └──────────────────────────┘
```

The frontend never talks to the database directly — every read/write goes
through the FastAPI REST API. There is no server-rendering; the frontend is
a fully client-side single-page app.

## 2. Backend architecture

### 2.1 Layout
```
backend/
  app/
    main.py            FastAPI app, CORS, startup seeding
    database.py         SQLAlchemy engine/session
    models.py            User, Record, PageView ORM models
    security.py          Password hashing, JWT issuing/verification
    deps.py               get_db, get_current_user, require_role
    integrations.py     Email + LLM integration helpers
    routers/
      auth.py             /api/auth/*
      users.py             /api/users/*
      entities.py          /api/entities/{type}* (generic CRUD)
      integrations.py    /api/integrations/*
      analytics.py         /api/analytics/*
  seed_demo_data.py     Standalone script: seeds a running instance via the API
```

### 2.2 The generic entity store
Rather than one SQL table per business entity (Cattle, MilkProduction,
HealthRecord, ...), all 19 entities share one table:

```python
class Record(Base):
    id: str            # uuid4 hex
    entity_type: str    # "Cattle", "MilkProduction", ...
    data: JSON           # the entity's actual fields
    created_by_id: str
    created_by_email: str
    created_date: datetime
    updated_date: datetime
```

`GET/POST/PUT/DELETE /api/entities/{entity_type}[/{id}]` is one generic
router that validates `entity_type` against an allow-list and otherwise
treats every entity uniformly (list with sort/limit, get, create, update
via dict-merge, delete).

**Why this design**: DairyPro's data originated from a schema-less
Base44 entity store. Recreating that with one Python/SQLAlchemy model per
entity would have meant 19 near-duplicate CRUD implementations. The
generic store trades strict column-level typing for a single, well-tested
code path, at the cost of weaker database-level constraints (see
[§7 Trade-offs](#7-known-trade-offs)).

The `User` entity is the one exception — it has its own table (`users`)
because it needs password hashing, uniqueness on email, and role logic
that doesn't fit the generic JSON-blob model.

### 2.3 Authentication
- Passwords: PBKDF2-HMAC-SHA256, per-user random salt (`security.py`).
- Tokens: JWT (HS256), 7-day default expiry, `sub` = user id.
- `get_current_user` (a FastAPI dependency) decodes the bearer token on
  every protected request and loads the user from the database.
- `require_role(*roles)` is a dependency factory used to gate admin-only
  endpoints (e.g. inviting users).

### 2.4 Integrations
- **Email** (`integrations.py`): sends via SMTP if `SMTP_HOST` is set;
  otherwise appends to `backend/var/sent_emails.log` so the flow still
  "works" without real credentials configured.
- **LLM** (`integrations.py`): calls the Anthropic Messages API directly
  via `requests` if `ANTHROPIC_API_KEY` is set; otherwise returns a
  `{_ai_unavailable: true, message: ...}` payload the frontend renders as
  a clear fallback state rather than failing silently.

### 2.5 Analytics
`routers/analytics.py` computes milk-yield trend/forecast (linear
regression over monthly totals), per-cow health risk scoring, and
breeding-interval recommendations directly from the stored records —
no LLM required for these. An LLM-enhanced narrative is layered on top
only for the `/api/analytics/ai-insights` endpoint.

## 3. Frontend architecture

### 3.1 Layout
```
frontend/src/
  api/              apiClient (axios), entities client, auth/users/integrations/analytics wrappers
  lib/               AuthContext, ThemeContext, permissions, offlineDb, syncEngine, forecastEngine, vendorUtils
  hooks/             useOfflineEntity, useCategories
  components/
    ui/                shadcn/ui primitives (button, card, dialog, table, ...)
    shared/             PageHeader, KpiCard, StatusBadge, EmptyState, ErrorState, LoadingSkeleton, OfflineSync, ...
    cattle/ breeding/ health/ inventory/ finance/ analytics/ milk/ reports/ settings/
                       feature-specific components
  pages/             one file per route (Dashboard, Cattle, MilkProduction, ...)
  Layout.jsx          Sidebar + mobile nav shell
  App.jsx              Routing, global providers
```

### 3.2 State and data fetching
- **TanStack React Query** owns all server-state caching. Every page
  fetches via `useQuery` keyed by entity name, and mutations
  (`useMutation`) call `queryClient.invalidateQueries` on success so
  affected views refetch — there is no cross-page event bus; consistency
  is achieved by React Query's cache invalidation plus each page
  independently re-deriving its own view of shared data.
- **AuthContext** holds the current user and exposes `login`/`register`/
  `logout`; the JWT itself lives in `localStorage` via `apiClient.js`.
- **ThemeContext** toggles a `dark` class on `<html>` and persists the
  choice; dark ("Obsidian") is the default brand identity.

### 3.3 The generic `EntityCrudPage` component
Several pages (Cattle, Tasks, Vendors, Finance's Transactions tab) are
thin configuration objects (`fields`, `columns`) passed into one shared
`EntityCrudPage` component, which owns the table, search, add/edit dialog,
delete confirmation, loading skeleton, and empty state. Pages with more
bespoke business logic (Breeding, Milk Production, Health Records,
Inventory) are hand-built but still compose the same shared primitives
(`PageHeader`, `KpiCard`, `EmptyState`).

### 3.4 Offline layer
- `offlineDb.js`: a small IndexedDB wrapper with two stores — a sync
  queue and a per-entity cache.
- `syncEngine.js`: replays the queue against the real API in order once
  back online, resolving locally-generated temp IDs to server IDs as
  `create` operations land.
- `useOfflineEntity(entityName)`: a hook mirroring the plain entity
  client's `create`/`update`/`remove` shape, but offline-aware.
- `OfflineSync.jsx` (mounted globally in `App.jsx`): registers the
  service worker, listens for `online`/`offline`, auto-syncs on
  reconnect, and renders the status pill + Quick Log entry point.
- `public/sw.js`: a minimal service worker that only caches static
  GET assets (stale-while-revalidate); it never intercepts `/api/`
  requests — offline data flows through the IndexedDB queue, not the
  service worker cache.

Only the Quick Log sheet (milk + health entries) is currently wired
through `useOfflineEntity`; other pages' forms call the plain API client
directly and will show a normal failed-request error if used offline.

## 4. Data model summary

19 logical entities, each a `Record` row with `entity_type` set
accordingly:

`Cattle`, `CattleGroup`, `MilkProduction`, `HealthRecord`, `BreedingRecord`,
`Inventory`, `ConsumptionRecord`, `StockAdjustment`, `ScheduledFeedRatio`,
`FeedRatio`, `ShoppingList`, `Task`, `Transaction`, `Vendor`,
`CategorySettings`, `MilkPrice`, `MilkYieldAlert`, `DashboardSettings`,
`Settings`.

Plus the dedicated `User` table. See the [Database Design
document](./DATABASE_DESIGN.md) for field-level detail on each entity.

## 5. Data ownership model

Every `Record` has `created_by_id`/`created_by_email`, but **read access
is farm-wide**: any authenticated user can read any record, regardless of
who created it. This is a deliberate departure from the original
per-record row-level-security model (where a user could only see records
they created), because a shared farm dataset is what makes sense
operationally — a farm manager needs to see milk records a staff member
logged, not just their own.

Write access is gated by **role**, not by ownership: certain entities
(`Settings`, `MilkPrice`, `CategorySettings`) require `admin`/`manager` to
create or update, enforced server-side in `routers/entities.py`
(`ADMIN_WRITE_ENTITIES`).

## 6. Financial reconciliation

Three different views compute "milk income" and they are designed to
agree by construction, not by coincidence:

1. **`MilkProduction.jsx`** (the point of entry): when a milk record is
   saved and a price exists for that month, it creates an Income
   transaction using **net liters** (`quantity_liters - milk_used_by_calves`)
   tagged with reference `MILK-{record_id}`.
2. **`Finance.jsx`** and **`Dashboard.jsx`** (the summaries): both
   independently **recompute** milk income as
   `Σ(net liters per month) × price_per_liter_for_that_month`, and
   explicitly **exclude** the `Milk Sales` transaction category from their
   "other income" sum.
3. **P&L Statement / Cash Flow Report**: these read the raw `Transaction`
   rows directly (including the auto-created Milk Sales ones), because
   they need transaction-level detail, not just a summary total.

The recompute-in-summaries approach exists because milk prices can be
corrected retroactively — recomputing from raw records keeps the summary
cards always accurate to the current price, while the auto-created
transactions remain useful for the detailed ledger reports. All three
paths use the same net-liters definition, so they never systematically
diverge.

## 7. Known trade-offs

| Decision | Trade-off accepted |
|---|---|
| Generic `Record` JSON store instead of per-entity tables | Simpler, uniform CRUD code; weaker DB-level type/constraint enforcement; sorting on JSON fields uses SQLite's `json_extract`, which doesn't scale as well as indexed columns |
| Farm-wide read visibility instead of per-user RLS | Matches how a real farm team actually needs to work; means there is no per-user data isolation within one deployment |
| SQLite by default | Zero-config to start; not suited to high-concurrency multi-writer workloads — swap the connection string for Postgres before that becomes a bottleneck |
| One backend serves one farm (no multi-tenancy) | Simpler auth/data model; running multiple farms means multiple deployments |
| Offline support limited to milk/health quick-entry | Bounded engineering scope; covers the two most realistic "no signal in the field" scenarios rather than every module |

## 8. Deployment topology

See the [Deployment Guide](./DEPLOYMENT_GUIDE.md) for concrete steps. In
summary: the backend runs as any ASGI app (`uvicorn`/`gunicorn`) behind
your reverse proxy of choice; the frontend builds to static files
(`npm run build` → `frontend/dist`) served by any static host, configured
with `VITE_API_URL` pointing at the deployed backend.
