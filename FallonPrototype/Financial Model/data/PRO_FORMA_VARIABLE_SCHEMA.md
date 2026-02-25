# Fallon Pro Forma Variable Schema

> **Purpose:** Canonical reference for every variable in a Fallon development pro forma.
> Every generated model must conform to this schema. The validation script
> (`shared/validate_defaults.py`) enforces these requirements against `market_defaults.json`.
>
> **Format:** Each variable entry in `market_defaults.json` follows this structure:
> ```json
> {
>   "variable_name": {
>     "value": <number>,
>     "unit": "<string>",
>     "source": "<string>"
>   }
> }
> ```

---

## 1. Revenue Variables

Revenue variables are **program-type specific** — each program type has its own
set of revenue drivers that reflect how that asset class generates income.

### Multifamily

| Variable | Unit | Description |
|----------|------|-------------|
| `rent_psf_monthly` | $/sf/month | Average monthly rent per rentable square foot |
| `avg_unit_size_sf` | sf | Average unit size in square feet |
| `unit_count` | units | Total residential units (user-provided, not a default) |
| `stabilized_occupancy_pct` | % | Occupancy at stabilization (0-100 scale) |
| `annual_rent_growth_pct` | % | Projected annual rent growth rate |
| `lease_up_months` | months | Months from first delivery to stabilized occupancy |
| `other_income_per_unit_monthly` | $/unit/month | Non-rent income: parking, storage, pet fees, etc. |

### Office

| Variable | Unit | Description |
|----------|------|-------------|
| `rent_psf_annual_nnn` | $/sf/year NNN | Annual triple-net asking rent per rentable sf |
| `rentable_sf` | sf | Total rentable square footage (user-provided, not a default) |
| `stabilized_occupancy_pct` | % | Occupancy at stabilization (0-100 scale) |
| `lease_up_months` | months | Months from delivery to stabilized occupancy |
| `free_rent_months` | months | Months of free rent in concession package |
| `ti_allowance_psf` | $/sf | Tenant improvement allowance per rentable sf |
| `leasing_commission_pct` | % | Leasing commission as % of total lease value |

### Hotel

| Variable | Unit | Description |
|----------|------|-------------|
| `adr` | $/night | Average daily rate per occupied room |
| `stabilized_occupancy_pct` | % | Stabilized room occupancy (0-100 scale) |
| `revpar` | $/available room/night | Revenue per available room (ADR x occupancy) |
| `total_keys` | keys | Total hotel rooms/keys (user-provided or placeholder) |
| `management_fee_pct` | % | Hotel management fee as % of gross revenue |
| `ff_and_e_reserve_pct` | % | FF&E reserve as % of gross revenue |

---

## 2. Cost Variables (All Program Types)

These variables apply to every program type. Values differ by market and
program but the variables themselves are universal.

| Variable | Unit | Description | Typical Range |
|----------|------|-------------|---------------|
| `hard_cost_psf` | $/sf | Construction hard cost per gross sf | $250-$450+ depending on market/type |
| `soft_cost_pct_of_hard` | % | Soft costs (A&E, permits, legal) as % of hard cost | 20-30% |
| `developer_fee_pct_of_total_cost` | % | Developer fee as % of total project cost | 3-5% |
| `contingency_pct_of_hard` | % | Construction contingency as % of hard cost | 5-10% |
| `land_cost` | $ | Total land acquisition cost | User-provided or estimated ($/acre x acreage) |
| `carry_cost_months` | months | Total carry period (construction + lease-up/ramp-up) | 30-42 months |

**Note:** `land_cost` is user-provided at the deal level and does not appear in
`market_defaults.json`. It is captured during parameter extraction (Phase 2).

---

## 3. Financing Variables

| Variable | Unit | Description | Typical Range |
|----------|------|-------------|---------------|
| `construction_loan_ltc_pct` | % | Loan-to-cost ratio | 55-65% |
| `construction_loan_rate_pct` | % | Interest rate on construction loan | 7.5-8.5% (SOFR + spread) |
| `construction_loan_term_months` | months | Construction loan term | 36-42 months |
| `equity_split_lp_pct` | % | LP ownership share of equity | 85-95% |
| `preferred_return_pct` | % | LP preferred return (hurdle rate before promote) | 8-10% |
| `promote_pct` | % | GP share of profits above preferred return | 20-25% |

---

## 4. Exit / Disposition Variables

| Variable | Unit | Description | Typical Range |
|----------|------|-------------|---------------|
| `exit_cap_rate_pct` | % | Stabilized NOI / exit sale price | 4.75-7.25% by market/type |
| `exit_sale_cost_pct` | % | Transaction costs at exit (broker fees, transfer taxes) | 2-3% |
| `exit_year` | years | Years from construction start to exit/disposition | 5-7 years |

---

## 5. Return Metrics (Calculated, Not Input)

These are **outputs** of the pro forma, not assumptions. They are computed by
the return calculator (`shared/return_calculator.py`) and cross-checked against
Claude's estimates. They do NOT appear in `market_defaults.json`.

| Metric | Unit | Description |
|--------|------|-------------|
| `project_irr_levered_pct` | % | Levered internal rate of return for the project |
| `project_irr_unlevered_pct` | % | Unlevered IRR (all-equity basis) |
| `lp_irr_pct` | % | LP-specific IRR after waterfall/promote |
| `equity_multiple_lp` | x | LP equity multiple (total distributions / LP equity invested) |
| `profit_on_cost_pct` | % | Total profit / total project cost x 100 |
| `development_spread_bps` | bps | (Yield on cost - exit cap rate) x 10,000 |

---

## 6. Required Market/Program Combinations

The following combinations must exist in `market_defaults.json` at minimum:

| Market | Multifamily | Office | Hotel |
|--------|:-----------:|:------:|:-----:|
| Charlotte | Required | Required | — |
| Nashville | Required | Required | Required |
| Boston | Required | Required | — |
| National Average | Required | Required | Required |

`national_average` serves as the fallback when a user specifies a market not
in the dataset. All assumptions from the fallback are labeled with a warning.

---

## 7. Data Quality & Metadata

Each market block includes a `_meta` object at the top level:

```json
{
  "market_name": {
    "_meta": {
      "last_updated": "YYYY-MM-DD",
      "data_quality": "estimated | broker_confirmed",
      "update_notes": "Free text describing data source and confidence"
    },
    "multifamily": { ... },
    "office": { ... }
  }
}
```

- `"estimated"` — sourced from public reports (CBRE, JLL, Marcus & Millichap).
  All assumptions labeled "estimated" in the generated pro forma.
- `"broker_confirmed"` — verified by Fallon's team with local broker data.
  Assumptions labeled "confirmed" in the generated pro forma.

---

## 8. Percentage Convention

All percentage values use the **0-100 scale**, not 0-1.

- Correct: `"stabilized_occupancy_pct": 93` (means 93%)
- Incorrect: `"stabilized_occupancy_pct": 0.93`

The validation script enforces this for all `_pct` variables.

---

## 9. Label Taxonomy (Generated Pro Forma Output)

When the pro forma generator produces output, every numeric value carries a label:

| Label | Meaning |
|-------|---------|
| `"confirmed"` | Value explicitly stated by the user |
| `"estimated"` | Value sourced from market defaults |
| `"calculated"` | Value derived mathematically from other values |
| `"missing"` | Required value not available — broker input needed |

This taxonomy flows through to the Excel export, where each label maps to a
background color for visual auditability.
