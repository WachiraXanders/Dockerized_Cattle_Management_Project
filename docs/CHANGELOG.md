# DairyPro — Changelog

Format: newest first. This project was delivered iteratively rather than
via numbered releases; entries are grouped by the milestone each round of
work represents.

## Milestone 8 — Documentation
- Added the full project documentation set under `docs/` (this file and
  its siblings): Project Proposal, SRS, Architecture, Database Design,
  API Documentation, UI/UX Documentation, Test Plan, Security, Deployment
  Guide, User Manual, Maintenance Guide, this Changelog, and the Final
  Project Report.

## Milestone 7 — Design system unification
- Added: Obsidian/Deep Forest/Emerald/Gold/Ivory/Slate token-based design
  system across the whole frontend (`index.css` CSS variables,
  `tailwind.config.js` radius/color wiring).
- Added: shared components `PageHeader`, `KpiCard`, `StatusBadge`,
  `EmptyState`, `ErrorState`, `LoadingSkeleton`.
- Changed: `Layout.jsx` sidebar regrouped into Overview/Livestock/
  Operations/Business/System with a subtle active-state indicator.
- Changed: `Dashboard.jsx` rebuilt on the new tokens with a time-of-day
  greeting.
- Changed: eliminated three duplicated local `StatCard` implementations
  (Finance, MilkProduction, BreedingAnalytics) in favor of `KpiCard`.
- Changed: converted ad-hoc badge colors (`bg-emerald-100`, `bg-amber-100`,
  etc.) to the semantic token palette across ~17 files.
- Fixed: a scripted color-conversion pass initially produced malformed
  classes (double-opacity suffixes, dropped `hover:` modifiers on dark
  variants) — caught by automated verification and corrected.
- Redesigned: `Login.jsx` — full glassmorphism hero/card layout on the
  new brand palette (previously a plain centered form).
- Added: dark mode (`ThemeContext.jsx`), persisted per browser, dark as
  the default identity.

## Milestone 6 — Offline support
- Added: `offlineDb.js` (IndexedDB queue + cache), `syncEngine.js`,
  `useOfflineEntity` hook, `OfflineSync`/`OfflineEntrySheet` components,
  a minimal service worker (`public/sw.js`).
- Scope: offline logging covers Milk Production and Health Records only.

## Milestone 5 — Milk Production multi-session entry
- Added: `MilkEntryForm.jsx` — log Morning/Afternoon/Evening for one cow
  in a single submission; only sessions with a quantity are saved.
- Changed: `MilkProduction.jsx` rebuilt around the new form, with a Daily
  Summary tab and a visible warning when no price is set for the current month.
- Fixed: consolidated the milk-sale auto-transaction logic into one place
  using net liters consistently (the original two-page implementation had
  an inconsistency between net vs. raw liters).

## Milestone 4 — Inventory/Transaction interlinking
- Fixed: `Inventory.jsx`'s consumption mutation was missing its
  `StockAdjustment` audit-log step.
- Fixed: `ProcessScheduledFeeds.jsx` scheduled deductions weren't creating
  audit-log entries.
- Added: `AutoTransactionSync.jsx` (dedup'd sync of inventory purchase
  and health costs into expense transactions), `CategoryBreakdown.jsx`,
  `ProfitLossStatement.jsx`, `CashFlowReport.jsx`.
- Changed: `Finance.jsx` restructured into Transactions / Category
  Reports / P&L / Cash Flow / Forecast / Milk Prices tabs; summary income
  now recomputed from milk x price, excluding the Milk Sales transaction
  category, to avoid double-counting.
- Added: `FeedRatioDialog.jsx` (individual-cow feed logging).
- Added: computed vendor outstanding-balance display.

## Milestone 3 — Breeding automations
- Added: `BreedingAnalytics.jsx`, `CalvingHeatmapCalendar.jsx`,
  `CattleForm.jsx` (standalone, reusable).
- Added: auto-lactation increment and auto-calf-registration flow when a
  breeding record is marked with a successful calving outcome.

## Milestone 2 — Full source review integration
- Ported/adapted ~40 real source files supplied from the original
  application across several review rounds: Reports sub-components,
  Cattle/Health/Breeding forms, Milk price dialog, vendor utilities,
  Inventory forms/cards, and more — replacing earlier best-effort
  reconstructions with the actual original logic.

## Milestone 1 — Initial full-stack rebuild
- Backend: FastAPI + SQLAlchemy + SQLite, JWT auth, generic entity store
  covering 19 logical entities, role-based write restrictions, email and
  LLM integration helpers, heuristic + optional LLM-backed analytics.
- Frontend: React + Vite rebuild reusing the original shadcn/ui component
  library; pages for Dashboard, Cattle, Milk Production, Health Records,
  Breeding, Inventory, Tasks, Finance, Vendors, Reports, Predictive
  Analytics, Settings.
- Added: `seed_demo_data.py`, a live API-driven seeder for realistic
  test data at configurable scale.

## Known deferred items (not yet done)
- Task-completion auto-deduction of linked inventory.
- Server-side per-entity role enforcement beyond the three admin-write entities.
- Password-reset email flow.
- Automated test suite (see the Test Plan for the planned structure).
- Accessibility audit execution (checklist defined, not yet run).
- Empty/error/skeleton states on the remaining custom pages (Inventory,
  Reports' tabs, Breeding, Health, Settings).
