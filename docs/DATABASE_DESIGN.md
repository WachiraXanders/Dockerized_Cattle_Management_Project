# DairyPro — Database Design

## 1. Physical schema

DairyPro uses **two** physical tables plus one logging table, not 19
separate business tables. See [Architecture §2.2](./ARCHITECTURE.md#22-the-generic-entity-store)
for the rationale.

### 1.1 `users`

| Column | Type | Notes |
|---|---|---|
| `id` | String (PK) | uuid4 hex |
| `email` | String, unique, indexed | lowercased on write |
| `full_name` | String | |
| `password_hash` | String, nullable | null until an invited user activates their account |
| `role` | String | `admin` \| `manager` \| `staff` \| `viewer` |
| `invited` | Boolean | true if created via the invite flow |
| `created_date` | DateTime | |
| `updated_date` | DateTime | |

### 1.2 `records` (the generic entity store)

| Column | Type | Notes |
|---|---|---|
| `id` | String (PK) | uuid4 hex |
| `entity_type` | String, indexed | one of the 19 logical entities (§2) |
| `data` | JSON | the entity's actual fields — see §2 for each entity's shape |
| `created_by_id` | String, indexed | |
| `created_by_email` | String | |
| `created_date` | DateTime, indexed | |
| `updated_date` | DateTime | |

### 1.3 `page_views`
| Column | Type | Notes |
|---|---|---|
| `id` | String (PK) | |
| `page` | String | |
| `user_id` | String, nullable | |
| `created_date` | DateTime | |

## 2. Logical entity data dictionary

Each table below documents the fields expected inside a `records.data` JSON
blob for that `entity_type`. Fields are conventions enforced by the
frontend forms, not database constraints.

### Cattle
| Field | Type | Description |
|---|---|---|
| tag_number | string | Unique herd tag (enforced by convention, not DB constraint) |
| name | string | Optional given name |
| breed | string | Holstein, Jersey, Guernsey, Ayrshire, Brown Swiss, Milking Shorthorn, Crossbreed, Other |
| gender | string | Female \| Male |
| status | string | Active \| Dry \| Pregnant \| Sold \| Deceased |
| date_of_birth | date | |
| weight_kg | number | |
| acquisition_date | date | |
| acquisition_type | string | Born on Farm \| Purchased \| Gifted |
| group_name | string | Free-text group label |
| stage | string | e.g. Calf, Heifer, Mature Cow, Bull |
| lactation_number | number | Auto-incremented on successful calving |
| sire_id / dam_id | string | Parent tag numbers |
| notes | string | |

### CattleGroup
| Field | Type |
|---|---|
| name | string |
| description | string |

### MilkProduction
| Field | Type | Description |
|---|---|---|
| date | date | |
| cattle_tag | string | Denormalized for display and historical stability |
| session | string | Morning \| Afternoon \| Evening |
| quantity_liters | number | |
| milk_used_by_calves | number | Subtracted to get "net" liters |
| fat_percentage / protein_percentage | number | |
| quality_grade | string | A \| B \| C |
| notes | string | |

### HealthRecord
| Field | Type |
|---|---|
| cattle_id, cattle_tag | string |
| date | date |
| record_type | Vaccination \| Treatment \| Checkup \| Surgery \| Deworming \| Injury \| Illness \| Other |
| diagnosis, treatment, medication, dosage, veterinarian | string |
| cost | number |
| follow_up_date | date |
| status | Resolved \| Ongoing \| Monitoring |
| notes | string |

### BreedingRecord
| Field | Type |
|---|---|
| cattle_id, cattle_tag | string |
| breeding_date | date |
| breeding_type | Artificial Insemination \| Natural |
| sire_info, sire_breed, technician | string |
| pregnancy_status | Pending \| Confirmed \| Not Pregnant \| Aborted |
| expected_calving_date | date — auto = breeding_date + 283 days |
| actual_calving_date | date |
| calving_outcome | Pending \| Successful \| Stillborn \| Assisted \| C-Section |
| calf_gender | Male \| Female |
| cost | number |
| notes | string |

### Inventory
| Field | Type |
|---|---|
| name, category | string (category: Feed \| Medicine \| Supplement \| Equipment \| Supplies \| Other) |
| package_quantity, kg_per_package | number |
| package_unit | bags \| boxes \| bottles \| pieces \| sacks |
| total_quantity_kg | number — auto = package_quantity × kg_per_package |
| reorder_level | number |
| cost_per_kg | number |
| purchase_date | date |
| supplier, vendor_id, vendor_name, location, notes | string |

### ConsumptionRecord
| Field | Type |
|---|---|
| date, inventory_id, item_name | |
| group_id, group_name | linked CattleGroup |
| quantity_kg, head_count, kg_per_head | number |
| cost_per_kg, total_cost | number |
| stock_before_kg, stock_after_kg | number |
| recorded_by, notes | string |

### StockAdjustment
| Field | Type |
|---|---|
| inventory_id, item_name | |
| adjustment_type | Purchase \| Consumption \| Waste \| Transfer \| Adjustment |
| quantity_change, previous_quantity, new_quantity | number |
| date | date |
| cost | number, only meaningful for Purchase |
| reason, reference, notes | string |

### ScheduledFeedRatio
| Field | Type |
|---|---|
| cattle_id, cattle_tag, cattle_name | |
| inventory_id, feed_name | |
| feed_amount_kg | number, per day |
| start_date, end_date | date |
| active | boolean |
| last_processed_date | date |

### FeedRatio
| Field | Type |
|---|---|
| cattle_id, cattle_tag, cattle_name | |
| date, inventory_id, feed_name | |
| feed_amount_kg, cost_per_kg, total_cost | number |
| remaining_inventory_kg | number |
| notes | string |

### ShoppingList
| Field | Type |
|---|---|
| inventory_id, item_name, category | |
| current_stock_kg, reorder_level_kg, suggested_quantity_kg | number |
| estimated_cost | number |
| supplier | string |
| priority | Critical \| High \| Medium |
| status | Pending \| Ordered \| Received \| Dismissed |
| auto_generated | boolean |

### Task
| Field | Type |
|---|---|
| title, category, assigned_to | string |
| due_date | date |
| priority | Low \| Medium \| High \| Urgent |
| status | Pending \| In Progress \| Completed \| Overdue |
| recurrence | None \| Daily \| Weekly \| Monthly |
| description | string |

### Transaction
| Field | Type |
|---|---|
| type | Income \| Expense |
| category | e.g. Milk Sales, Cattle Sales, Feed, Medicine, Veterinary, Labor, Equipment, Utilities, Transportation, Other |
| amount | number |
| date | date |
| payment_method | Cash \| Bank Transfer \| Check \| Mobile Money \| Other |
| vendor_id, vendor_name | string |
| reference | string — used for de-duplication, e.g. `MILK-{id}`, `INV-{id}`, `HEALTH-{id}` |
| description | string |

### Vendor
| Field | Type |
|---|---|
| name, category, contact_person, phone, email | string |
| payment_terms | Cash \| Net 7 \| Net 14 \| Net 30 \| Net 60 |
| status | Active \| Inactive |
| address | string |

### CategorySettings
| Field | Type |
|---|---|
| context | inventory \| finance_income \| finance_expense |
| name | string |
| is_default | boolean — defaults cannot be deleted from the UI |

### MilkPrice
| Field | Type |
|---|---|
| month | string, `YYYY-MM` |
| price_per_liter | number |

### MilkYieldAlert
| Field | Type |
|---|---|
| cattle_id, cattle_tag | |
| alert_date | date |
| day_total, seven_day_avg, drop_percent | number |
| status | Active \| Dismissed |

### DashboardSettings / Settings
`Settings` (singleton, one row expected): `farm_name`, `currency`,
`currency_symbol`, `location`, `phone`, `email` (used as the manager email
for automated alerts). `DashboardSettings` is reserved for future
per-user dashboard preferences and is not yet used by any page.

## 3. Relationships

Relationships are by **denormalized reference**, not foreign keys — this
is a direct consequence of the generic JSON store:

```
Cattle (1) -- (many) MilkProduction        via cattle_tag / cattle_id
Cattle (1) -- (many) HealthRecord          via cattle_id
Cattle (1) -- (many) BreedingRecord        via cattle_id
Cattle (1) -- (many) FeedRatio             via cattle_id
CattleGroup (1) -- (many) ConsumptionRecord via group_id
Inventory (1) -- (many) StockAdjustment    via inventory_id
Inventory (1) -- (many) ConsumptionRecord  via inventory_id
Inventory (1) -- (many) ShoppingList       via inventory_id
Vendor (1) -- (many) Inventory             via vendor_id
Vendor (1) -- (many) Transaction           via vendor_id
MilkProduction/StockAdjustment/HealthRecord -> Transaction (auto-created, tagged by reference)
```

There is no database-enforced referential integrity between these — a
deleted `Cattle` record, for example, does not cascade-delete or block
deletion of its `MilkProduction` history. This mirrors the original
Base44 platform's behavior and is a known trade-off (see
[Architecture §7](./ARCHITECTURE.md#7-known-trade-offs)).

## 4. Indexing

- `records.entity_type` — indexed (every query filters by it first).
- `records.created_date` — indexed (default sort for most lists).
- `records.created_by_id` — indexed.
- `users.email` — unique + indexed.

Sorting by an arbitrary JSON field (e.g. `-breeding_date`) uses SQLite's
`json_extract(data, '$.field')` at query time, which is not
index-accelerated. At significant scale, consider promoting frequently
sorted/filtered fields to real columns or moving to Postgres with
generated columns / GIN indexes on the JSON payload.

## 5. Migration notes

There is currently no formal migration tool (e.g. Alembic) — `Base.metadata.create_all()`
runs on startup, which creates missing tables but does not alter existing
ones. Schema changes to the two real tables (`users`, `page_views`) would
need a manual migration; changes to any logical entity's *shape* require
no migration at all, since it's just JSON.
