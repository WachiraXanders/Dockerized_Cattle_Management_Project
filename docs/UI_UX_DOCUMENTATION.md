# DairyPro — UI/UX Documentation

## 1. Design language

DairyPro's visual identity is **Obsidian/Deep Forest/Emerald/Gold/Ivory/
Slate** — a premium, dark-first palette meant to read as "sophisticated
agricultural technology" rather than a generic admin template. See
`frontend/src/index.css` for the exact HSL token values.

| Token | Hex | Used for |
|---|---|---|
| Obsidian | `#0B0F14` | Primary dark background |
| Deep Forest | `#123524` | Elevated dark surfaces, accents |
| Emerald | `#22C55E` | Primary actions, active nav, positive metrics |
| Soft Ivory | `#F8FAFC` | Light-theme background, dark-theme text |
| Muted Slate | `#94A3B8` | Secondary/muted text |
| Gold | `#D4A017` | Financial highlights, premium/status accents |

Dark is the **default** theme (brand identity); light is a refined ivory
alternative. Both are user-toggleable from the sidebar and persist per
browser (`localStorage`).

Typography: **Inter**, loaded via Google Fonts, with system-ui fallback.

Border radius: a single `--radius` CSS variable (16px) drives every
`rounded-lg`/`rounded-md` utility app-wide via the Tailwind config.

## 2. Navigation structure

The sidebar (`Layout.jsx`) is grouped:

```
Overview       Dashboard
Livestock      Cattle - Health - Breeding - Milk Production
Operations     Inventory - Tasks - Suppliers
Business       Finance - Reports - Predictive Analytics
System         Settings
```

Each group's items are filtered per the current user's role
(`canAccessPage` in `src/lib/permissions.js`) — a `staff` user, for
example, never sees Finance/Reports/Predictive Analytics/Settings links
at all, rather than seeing them disabled.

Active nav item: a subtle `bg-sidebar-accent` tint plus a 2px emerald
indicator bar on the left edge — not a solid colored block.

On mobile (under 768px), the sidebar collapses to a slide-out drawer
triggered from a top header bar.

## 3. Reusable component library

`src/components/shared/`:

| Component | Purpose |
|---|---|
| `PageHeader` | Title + optional icon/subtitle + right-aligned actions slot. Used at the top of every page. |
| `KpiCard` | Value/label/icon/optional trend indicator, with a semantic `tone` (emerald/gold/rose/blue/slate). Replaces duplicated ad-hoc stat cards. |
| `StatusBadge` | Looks up a status word (case-insensitive) in a shared map and renders it in one of four semantic colors — good/warn/bad/neutral. Displays exactly the text passed to it; it is not a relabeling component. |
| `EmptyState` | Icon + title + description + optional action button, with a subtle contour-line brand motif in the background. Used wherever a list/table has no data. |
| `ErrorState` | Human-readable failure message + retry button; raw error text (if shown at all) renders small and separate from the headline. |
| `LoadingSkeleton` (`TableSkeleton`, `CardSkeleton`) | Shimmer placeholders instead of a blank screen or bare spinner while data loads. |
| `OfflineSync` / `OfflineEntrySheet` | Global offline-status indicator and the offline quick-entry form (see Architecture §3.4). |

`src/components/EntityCrudPage.jsx` is the shared list+form+delete
scaffold used by Cattle, Tasks, Vendors, and Finance's Transactions tab —
a page becomes a `columns`/`fields` configuration rather than a hand-built
CRUD screen.

## 4. Status color semantics

| Color | Meaning |
|---|---|
| Emerald (good) | Active, resolved, completed, confirmed, successful, in stock |
| Gold (warn) | Pending, ongoing, monitoring, in progress, low stock |
| Red/destructive (bad) | Overdue, critical, high priority, out of stock, outstanding balance |
| Slate (neutral) | Inactive, sold, deceased, dismissed, cancelled |

## 5. Cattle profile

`CattleDetails.jsx` — a slide-out panel opened by clicking a cow's name —
organizes information into tabs rather than a flat field dump:

- **Overview**: identification, DOB, weight, acquisition, lineage, notes.
- **Breeding**: current pregnancy alert (if any), last calving summary,
  breeding history list.
- **Health**: recent health records with status badges.
- **Production**: 30-day total/average, recent session-level records.

## 6. Forms

All forms use the shadcn `ui/` primitives (`Input`, `Select`, `Label`,
`Textarea`, `Checkbox`) for consistent height, focus rings, and spacing.
Multi-section forms (e.g. Breeding record: pregnancy status block, calving
information block) are visually grouped with a light background tint
rather than a flat list of fields. The Milk Production entry form
specifically supports logging Morning/Afternoon/Evening in one submission,
with per-session sub-sections.

## 7. Error states

Raw technical errors (Axios error objects, stack traces) are never shown
to the user. `ErrorState` renders a plain-language headline
("We couldn't load this data"), a description, and a retry button;
technical detail, if present, renders separately and small.

## 8. Empty states

Never a bare "No data." — `EmptyState` always pairs a headline with a
description of what's missing and, where there's a clear next step, an
action button (e.g. "Add Cattle"). Currently wired into `EntityCrudPage`
and `MilkProduction.jsx`; extending this to the remaining custom pages
(Inventory, Reports, Breeding, Health, Settings) is tracked as follow-up
work.

## 9. Loading states

`TableSkeleton`/`CardSkeleton` shimmer placeholders replace blank screens
during data fetch on pages using `EntityCrudPage`; other pages currently
use a centered spinner (`Loader2` from lucide-react) as a lighter-weight
fallback.

## 10. Responsive behavior

- Sidebar collapses to a slide-out drawer below the `md` breakpoint.
- KPI/stat grids collapse from 4-5 columns to 2 columns on small screens.
- Tables scroll horizontally on narrow viewports rather than reflowing
  into cards (a possible future improvement).
- The Login page's hero panel (left 40%) hides entirely below `lg`,
  replaced by the same background behind the centered card.

## 11. Accessibility

Current state: shadcn's `ui/` primitives (Button, Input, Dialog, etc.)
provide baseline keyboard navigation and visible focus rings out of the
box. `Label`/`Input` pairs use `htmlFor`/`id` associations. A full audit
(icon-only button `aria-label`s, color-contrast verification in both
themes, screen-reader testing) has not yet been performed — see the
Test Plan's accessibility section for the planned checklist.

## 12. Micro-interactions

Button/link hover states, dialog/sheet enter-exit transitions, and
dropdown transitions all come from the underlying shadcn/Radix primitives
(built-in, restrained — no custom bounce/glow effects added). No
additional custom animation pass has been layered on top.
