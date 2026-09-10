# DairyPro — Project Proposal

## 1. Background

Small and mid-sized dairy farms typically track herd, health, breeding, feed,
inventory, and financial records across paper logs, spreadsheets, or a mix of
disconnected tools. This makes it hard to answer basic operational questions
quickly — "which cows are due to calve this month?", "are we profitable this
month?", "which feed items need reordering?" — without manually
cross-referencing several sources.

DairyPro was originally built on a low-code platform (Base44) and has since
been rebuilt as a standalone, self-hosted full-stack application (FastAPI +
React) so the farm owns its data and infrastructure outright, with no
dependency on a third-party platform.

## 2. Problem statement

Farm operators need a single system that:

- Records day-to-day operational data (milk yield, health events, breeding,
  feed/inventory movements, tasks) with minimal friction.
- Automatically derives the financial and operational picture from that data
  (income, expenditure, profit, stock alerts, yield trends) rather than
  requiring duplicate manual entry.
- Supports multiple staff with different levels of access (owner/admin,
  farm manager, general staff, read-only viewer).
- Works acceptably even with an unreliable internet connection.

## 3. Objectives

1. Provide full CRUD data entry for the core farm entities: cattle, milk
   production, health records, breeding records, inventory, tasks,
   transactions, and vendors.
2. Automatically link related data — e.g., a successful calving updates the
   cow's lactation count and prompts calf registration; milk sales
   auto-generate ledger transactions; low stock auto-generates a shopping
   list with email alerts.
3. Provide role-based access control across four roles.
4. Provide dashboards, reports, and AI-assisted analytics (milk forecasting,
   health risk scoring, breeding recommendations) computed from the farm's
   own data.
5. Support basic offline data entry for the two most realistic
   field-connectivity scenarios (milk logging, health logging), syncing
   automatically once back online.
6. Be deployable by the farm on infrastructure it controls (self-hosted
   FastAPI backend + static frontend), rather than depending on Base44.

## 4. Scope

**In scope:** the modules listed in the [Software Requirements
Specification](./SRS.md) — Cattle, Milk Production, Health, Breeding,
Inventory, Tasks, Finance, Vendors, Reports, Predictive Analytics, Settings,
and authentication/authorization.

**Out of scope for the current version** (see [SRS §7](./SRS.md#7-out-of-scope--known-limitations)
for the full list): drag-and-drop kanban boards, a native mobile app,
multi-farm/multi-tenant support, payment processing, and a fully offline-capable
experience across every module (only milk and health quick-entry are
offline-capable today).

## 5. Stakeholders

| Role | Interest |
|---|---|
| Farm owner / admin | Full visibility and control; financial accuracy; staff management |
| Farm manager | Day-to-day oversight of herd, health, breeding, inventory, and finance |
| Farm staff | Fast, low-friction data entry (milk, health, tasks, feed) |
| Veterinarian / consultant (viewer role) | Read-only visibility into health and breeding records |
| Developer / maintainer | A codebase that is straightforward to extend and self-host |

## 6. Success criteria

- All modules in scope are usable end-to-end (create, read, update, delete)
  through the web UI.
- Role-based access is enforced both in the UI (hidden/disabled controls)
  and the API (rejected requests), not just cosmetically in the frontend.
- Financial figures shown on the Dashboard, Finance page, and Reports agree
  with each other for the same period (see the reconciliation rules in the
  [Architecture doc](./ARCHITECTURE.md#financial-reconciliation)).
- The system can be stood up from a clean checkout using only the
  instructions in the [Deployment Guide](./DEPLOYMENT_GUIDE.md).

## 7. High-level timeline (as actually delivered)

This project was delivered iteratively rather than against a fixed
waterfall schedule:

1. Migration assessment of the original Base44 application (entity schemas,
   page inventory).
2. Backend rebuild: FastAPI + SQLite, JWT auth, generic entity store.
3. Frontend rebuild: React + Vite, page-by-page, reusing the original
   shadcn/ui component library.
4. Feature parity passes: breeding automations, inventory/finance
   interlinking, milk multi-session entry, offline logging.
5. Design system pass: unified visual identity, shared UI components,
   accessibility and empty-state improvements.
6. Documentation (this set).

## 8. Budget / resourcing note

This is a self-hosted, open-source-style deliverable with no licensing
costs beyond standard hosting (a small VM or PaaS instance for the backend,
static hosting for the frontend) and an optional Anthropic API key for the
AI-assisted insights feature.
