# DairyPro — Software Requirements Specification (SRS)

## 1. Introduction

### 1.1 Purpose
This document specifies the functional and non-functional requirements of
DairyPro, a self-hosted dairy farm management web application.

### 1.2 Intended audience
Developers maintaining or extending the system, and technically-minded
stakeholders evaluating its capabilities.

### 1.3 Definitions
- **Entity**: a record type stored by the backend (e.g. Cattle, MilkProduction).
- **Role**: one of `admin`, `manager`, `staff`, `viewer`.
- **Farm-wide data**: records visible to every authenticated user regardless
  of who created them (see [Architecture §5](./ARCHITECTURE.md#5-data-ownership-model)).

## 2. Overall description

DairyPro is a two-tier web application: a FastAPI backend exposing a REST
API over a SQLite (or Postgres-compatible) database, and a React single-page
frontend. See the [Architecture document](./ARCHITECTURE.md) for the full
technical picture.

## 3. User roles and permissions

| Role | Description |
|---|---|
| `admin` | Full access to every module, including Settings, user management, and farm-wide configuration (currency, categories). The first person to register becomes admin automatically. |
| `manager` | Full operational access (Cattle, Milk, Health, Breeding, Inventory, Tasks, Finance, Vendors, Reports, Predictive Analytics) but not Settings/user administration. |
| `staff` | Day-to-day data entry (Cattle, Milk, Health, Breeding, Inventory, Tasks) without Finance, Vendors, Reports, or Predictive Analytics access. |
| `viewer` | Read-only access to Dashboard, Cattle, Milk Production, Health Records, Breeding, Inventory, and Tasks. |

The authoritative, field-level matrix is rendered live in the app at
**Settings → Role Matrix** (`src/lib/permissions.js`).

## 4. Functional requirements

Each requirement is tagged `FR-<module>-<n>`.

### 4.1 Authentication & Users
- **FR-AUTH-1**: Users register with email/password; the first registrant
  becomes `admin`, subsequent registrants default to `staff`.
- **FR-AUTH-2**: Users log in with email/password and receive a JWT
  (7-day expiry by default).
- **FR-AUTH-3**: Admins can invite users by email and assign a role; invited
  users activate their account by registering with the invited email.
- **FR-AUTH-4**: Admins can change any user's role or remove a user.

### 4.2 Cattle
- **FR-CATTLE-1**: Create, view, edit, delete cattle records (tag number,
  name, breed, gender, status, DOB, weight, acquisition info, group, lineage).
- **FR-CATTLE-2**: View a detailed cattle profile with tabs for Overview,
  Breeding, Health, and Production history.

### 4.3 Milk Production
- **FR-MILK-1**: Log milk yield for one cow across Morning/Afternoon/Evening
  sessions in a single form submission; only sessions with a quantity are saved.
- **FR-MILK-2**: Edit or delete an individual session record.
- **FR-MILK-3**: View a daily-totals summary aggregated per cow per day.
- **FR-MILK-4**: Set a price-per-liter for any month; if a price exists for
  the record's month, saving a milk record automatically creates a
  corresponding Income transaction using **net liters** (quantity minus
  milk used by calves).
- **FR-MILK-5**: Warn the user visibly if no price is set for the current
  month, since this silently zeroes out milk income everywhere else in the app.

### 4.4 Health Records
- **FR-HEALTH-1**: Create, view, edit, delete health records per animal
  (type, diagnosis, treatment, medication, cost, follow-up date, status).
- **FR-HEALTH-2**: Unresolved records with a future follow-up date surface
  on the Dashboard's Upcoming Events.

### 4.5 Breeding
- **FR-BREED-1**: Create, view, edit, delete breeding records (breeding
  date, type, sire info, pregnancy status, expected/actual calving,
  outcome, calf gender).
- **FR-BREED-2**: Expected calving date auto-calculates as 283 days after
  the breeding date.
- **FR-BREED-3**: When a breeding record is newly marked with a
  `Successful` calving outcome, the dam's `lactation_number` increments,
  her status is set to `Active`, and a pre-filled calf-registration form
  opens automatically.
- **FR-BREED-4**: A calendar view (heatmap) shows expected and actual
  calvings by day, plus an upcoming-60-days list.
- **FR-BREED-5**: An analytics view shows pregnancy success rate by sire
  breed and by season.

### 4.6 Inventory
- **FR-INV-1**: Create, view, edit, delete inventory items (category,
  package size, computed total kg, reorder level, cost, supplier).
- **FR-INV-2**: Record stock adjustments (Purchase/Consumption/Waste/
  Transfer/Adjustment); every adjustment updates the item's on-hand
  quantity and is logged to an audit trail.
- **FR-INV-3**: Log group feed consumption (linked to a cattle group) and
  individual-cow feed ratios; both deduct stock and log an audit entry.
- **FR-INV-4**: Auto-generate a shopping list for low-stock Feed items,
  with priority tiers (Critical/High/Medium) based on stock ratio, and
  email the farm's manager address for Critical items.
- **FR-INV-5**: Support recurring feeding schedules that automatically
  generate daily feed-ratio entries and stock deductions for as long as the
  schedule is active.

### 4.7 Tasks
- **FR-TASK-1**: Create, view, edit, delete tasks (category, assignee, due
  date, priority, status, recurrence).

### 4.8 Finance
- **FR-FIN-1**: Record income/expense transactions manually.
- **FR-FIN-2**: Auto-sync inventory purchase costs and health-record costs
  into expense transactions, deduplicated by a reference tag so re-running
  the sync never double-creates.
- **FR-FIN-3**: Show category breakdown, a profit & loss statement by
  month, a cash-flow view, and a scenario-based financial forecast
  (base/bull/bear/custom).
- **FR-FIN-4**: The summary income figure is **recomputed** from milk
  records × monthly price (excluding the `Milk Sales` transaction category)
  rather than trusted from the auto-created transactions, so a later price
  correction is always reflected (see [Architecture — Financial
  Reconciliation](./ARCHITECTURE.md#financial-reconciliation)).

### 4.9 Vendors
- **FR-VENDOR-1**: Create, view, edit, delete vendor records (category,
  contact, payment terms).
- **FR-VENDOR-2**: Compute and display each vendor's outstanding balance
  from unpaid credit-term transactions and credit-term inventory purchases.

### 4.10 Reports
- **FR-REPORT-1**: Provide filterable, exportable (CSV/PDF) reports for
  Milk Production, Feed Consumption, Inventory, Financial, Health, and a
  composite KPI report, plus a breeding events calendar.

### 4.11 Predictive Analytics
- **FR-PRED-1**: Provide an AI-generated insights panel (low-yield cattle,
  recurring health issues, general recommendations) and a 3-month milk
  forecast, both backed by an LLM call when `ANTHROPIC_API_KEY` is
  configured, with a clear fallback message when it is not.

### 4.12 Dashboard
- **FR-DASH-1**: Show today's and this-month's key metrics (milk, income,
  expenditure, profit, active cattle, pending tasks, low-stock items)
  without writing any data itself.
- **FR-DASH-2**: Detect milk yield drops of 20% or more versus a cow's
  trailing 7-day average and surface a dismissible alert.
- **FR-DASH-3**: Surface pregnancy alerts (30 days or fewer to expected
  calving) and a loss alert when the current month's profit is negative.

### 4.13 Settings
- **FR-SET-1**: Manage farm profile and currency.
- **FR-SET-2**: Manage custom categories for inventory and finance,
  alongside fixed defaults.
- **FR-SET-3**: Manage users and their roles (admin only).
- **FR-SET-4**: Display the live role-permission matrix.

### 4.14 Offline support
- **FR-OFFLINE-1**: When offline, the user can log milk or health entries
  via a "Quick Log" sheet; entries are queued locally (IndexedDB) and
  synced automatically once connectivity returns.
- **FR-OFFLINE-2**: A persistent indicator shows offline status and any
  pending-sync count, with a manual "Sync now" action.

## 5. Non-functional requirements

- **NFR-1 (Security)**: Passwords are hashed (PBKDF2-HMAC-SHA256, salted);
  JWTs are signed with a configurable secret; role checks are enforced
  server-side, not only in the UI.
- **NFR-2 (Usability)**: Forms give inline validation and clear error
  messages; empty states explain what to do next rather than showing a
  bare "no data" message.
- **NFR-3 (Availability)**: The two highest-value field-entry workflows
  (milk, health logging) remain usable without a network connection.
- **NFR-4 (Portability)**: The backend runs against SQLite by default and
  is swappable to any SQLAlchemy-supported database via one connection
  string.
- **NFR-5 (Theming)**: The UI supports light and dark themes, with dark as
  the default brand identity, persisted per browser.
- **NFR-6 (Auditability)**: Every stock change is recorded as a
  `StockAdjustment` regardless of which feature triggered it (manual
  adjustment, consumption log, feed ratio, scheduled feed, or task
  completion), so the adjustment history is always complete.

## 6. External interface requirements

- **API**: REST/JSON over HTTPS; see [API Documentation](./API_DOCUMENTATION.md).
- **Email**: outbound SMTP if configured, otherwise logged locally
  (see [Deployment Guide](./DEPLOYMENT_GUIDE.md)).
- **AI**: optional Anthropic Messages API call for LLM-backed insights.

## 7. Out of scope / known limitations

- No native mobile app (the web UI is responsive but not packaged natively).
- No multi-tenant / multi-farm support — one deployment serves one farm's
  data (see [Architecture — Data Ownership Model](./ARCHITECTURE.md#5-data-ownership-model)
  for the specific farm-wide-visibility trade-off this implies).
- No payment processing.
- No drag-and-drop kanban board for tasks.
- Offline support covers milk and health quick-entry only; other modules
  require connectivity.
- No password-reset email flow yet (an admin must reset via Settings →
  Users, or the user re-registers before ever logging in).
