# DairyPro — Test Plan & Test Cases

## 1. Test strategy

DairyPro currently has **no automated test suite** — this document
defines the manual test plan that should be run before any release, and
the structure a future automated suite should follow.

Recommended layering for a future automated suite:
- **Backend unit tests** (pytest): password hashing, JWT issuing/validation,
  the generic entity CRUD router, permission enforcement on
  `ADMIN_WRITE_ENTITIES`.
- **Backend integration tests**: full request/response cycles against a
  test SQLite database (register, login, create/read/update/delete an
  entity, verify role rejection).
- **Frontend component tests** (Vitest + React Testing Library): shared
  components (`KpiCard`, `StatusBadge`, `EmptyState`, `EntityCrudPage`).
- **End-to-end tests** (Playwright/Cypress): the critical user journeys
  in §3 below.

## 2. Test environment

- Backend: `uvicorn app.main:app --reload --port 8000` against a scratch
  SQLite file (not the production `dairypro.db`).
- Frontend: `npm run dev` with `VITE_API_URL` pointing at the scratch backend.
- Seed data: `backend/seed_demo_data.py` (see the Deployment Guide's
  seeding section) for a realistic, large dataset to test against.

## 3. Critical user journeys (manual regression checklist)

| ID | Journey | Steps | Expected result |
|---|---|---|---|
| CJ-01 | First-run registration | Open the app fresh, register | Becomes `admin`; lands on Dashboard |
| CJ-02 | Second user is staff by default | Register a second account | New user has `staff` role |
| CJ-03 | Role-gated navigation | Log in as `staff` | Finance/Reports/Predictive Analytics/Settings do not appear in the sidebar |
| CJ-04 | Role-gated API | As `staff`, call `PUT /api/entities/Settings/{id}` directly | `403` |
| CJ-05 | Cattle CRUD | Add, edit, delete a cattle record | List reflects each change immediately |
| CJ-06 | Milk multi-session entry | Log Milk, fill Morning + Evening only, leave Afternoon blank, submit | Exactly 2 records created, not 3 |
| CJ-07 | Milk auto-transaction | Set a price for the current month, log milk | A Transaction (Income, Milk Sales, reference `MILK-{id}`) is created with net-liters amount |
| CJ-08 | Milk price omitted warning | Ensure no price is set for the current month, open Milk Production | Amber warning banner is visible |
| CJ-09 | Breeding auto-lactation | Edit a breeding record to `calving_outcome = Successful` with an `actual_calving_date` | Dam's `lactation_number` increments; status becomes `Active` |
| CJ-10 | Calf auto-registration | Continue from CJ-09 | Cattle registration form opens pre-filled with dam/sire tag, breed, DOB |
| CJ-11 | Stock adjustment | Adjust inventory item stock (Purchase, +50kg) | Item's `total_quantity_kg` increases by 50; a `StockAdjustment` audit row is created |
| CJ-12 | Consumption logging | Log group feed consumption | Inventory stock decreases; `ConsumptionRecord` and `StockAdjustment` are both created |
| CJ-13 | Shopping list auto-generation | Drop an item's stock below its reorder level, open Inventory - Shopping List | Item appears with a computed priority tier |
| CJ-14 | Critical stock email | Force an item to 25% or less of reorder level, with a Settings manager email set | Email is sent (or logged, if SMTP unset) |
| CJ-15 | Auto-transaction sync | Create a Purchase-type stock adjustment with a cost, and a Health record with a cost, then Finance - Category Reports - Sync Costs Now | Two new Expense transactions appear, tagged `INV-{id}`/`HEALTH-{id}` |
| CJ-16 | Sync de-duplication | Run CJ-15's sync a second time | No duplicate transactions are created |
| CJ-17 | Financial reconciliation | Compare the Dashboard's monthly Income figure to Finance's Total Income for the same month | They match |
| CJ-18 | Vendor outstanding balance | Create a Net-30 vendor, record a non-cash Expense transaction against them | Vendor row shows an "Outstanding" indicator with the correct amount |
| CJ-19 | Milk yield alert | Log a day's milk for a cow at least 20% below its trailing 7-day average (with 3+ prior days of history) | Dashboard shows a dismissible yield-drop alert |
| CJ-20 | Pregnancy alert | Set a breeding record's expected calving date to within 30 days, `pregnancy_status = Confirmed`, `calving_outcome = Pending` | Dashboard shows a pregnancy alert |
| CJ-21 | Offline milk logging | Disable network in devtools, open Quick Log, submit a milk entry | Entry is queued locally; pending-sync indicator shows 1 |
| CJ-22 | Offline sync | Re-enable network | Queued entry is pushed to the server automatically; indicator clears |
| CJ-23 | Theme toggle | Toggle dark/light from the sidebar, reload the page | Theme choice persists |
| CJ-24 | AI insights fallback | With no `ANTHROPIC_API_KEY` set, open Predictive Analytics, Get AI summary | A clear "not configured" message is shown, not an error |
| CJ-25 | Report export | Open any Reports tab, Export CSV / Export PDF | A correctly-formatted file downloads |

## 4. Example detailed test cases

| ID | Test | Preconditions | Steps | Expected Result |
|---|---|---|---|---|
| TC-001 | Login, valid credentials | An activated account exists | Enter correct email/password, Sign in | Redirected to Dashboard; JWT stored |
| TC-002 | Login, invalid password | An activated account exists | Enter correct email, wrong password | Inline error shown; no redirect |
| TC-003 | Register, weak password | None | Enter a 3-character password | Client-side validation blocks submit (min 6) |
| TC-004 | Submit empty cattle form | On Cattle page | Open Add Cattle, submit with no tag number | Validation error on the required field; no request sent |
| TC-005 | Delete confirmation | A record exists | Click delete on a row | A confirmation dialog appears before the record is removed |
| TC-006 | Unauthorized entity write | Logged in as `staff` | `POST /api/entities/Settings` via API client | `403 Insufficient permissions` |
| TC-007 | Unknown entity type | Any authenticated user | `GET /api/entities/NotARealEntity` | `404 Unknown entity` |
| TC-008 | JWT expiry | Token older than `DAIRYPRO_TOKEN_EXPIRE_DAYS` | Call any protected endpoint | `401`; frontend redirects to `/login` |

## 5. Accessibility test checklist (planned, not yet executed)

- [ ] All icon-only buttons have an `aria-label`.
- [ ] Tab order follows visual order on every page.
- [ ] Focus is visible (not suppressed) on every interactive element.
- [ ] Color contrast meets WCAG AA in both light and dark themes for body
      text and status badges.
- [ ] Forms announce validation errors to screen readers (`aria-describedby`
      or equivalent).
- [ ] The app is fully operable via keyboard alone (no mouse-only paths).

## 6. Performance test notes

Not formally benchmarked. Known scaling risk: the generic entities list
endpoint has no server-side pagination, and most pages fetch up to
500-5000 records per query. `backend/seed_demo_data.py` can generate a
multi-thousand-record dataset (`--scale 2.0` or higher) specifically to
stress-test list rendering and identify where pagination becomes
necessary.

## 7. Security test notes

See the Security Documentation for the threat model this should validate
against — in particular, confirming role checks are enforced server-side
(CJ-04/TC-006 above), not just hidden in the UI.
