# PROJECT 3: Financial Dashboard & Business Intelligence

**Client Entity:** Ferris Development Group (Holding Company - reporting across ALL entities)
**Priority:** #3 per David Ferris - "prerequisite for everything that comes after"
**Stack:** Supabase (Database, Edge Functions, Storage) + React frontend + spreadsheet ingestion pipeline
**Estimated Build Time:** 5-7 weeks across all phases

---

## BUSINESS CONTEXT (From David Ferris Interview)

Ferris put it plainly: **"I can't fix problems I don't know about."**

Financial data reaches him after the fact. There is no real-time P&L visibility by business unit, no automated reporting, and no forward-looking model projecting two quarters out. The quarterly reforecast his team produces is manual, backward-looking, and labor-intensive.

**Specific data gaps Ferris identified:**
1. Cannot tell what they spent per square foot on electrical work across the last 8 jobs
2. Cannot quickly compare in-house vs. contracted labor costs (though his intuition is sharp - saved $40-45K on a single fire head project by using own crew vs $84-91K third-party bids)
3. No automated procurement controls - a $38,000 plumbing order went out to FW Webb without a competitive price check
4. No standardized unit economics for Beehive service types (water heater replacement avg P&L, avg hours, avg materials)

**The endgame:** Formalize Beehive's financial profile so the business can be priced consistently, scaled into new markets (Martha's Vineyard is the test case), and eventually presented to private equity or IPO. **"I can't formulatize it until I start to understand the P&L from various job sets."**

**Finance team structure:** Madison Scott leads finance, reports to Brian Charville (COO). Below them are bookkeeping/data entry staff updating finance books. The team currently uses spreadsheets for project cost tracking and produces manual quarterly reforecasts.

---

## FEASIBILITY ASSESSMENT

### Data Source Reality Check
Ferris's finance team already generates the raw data in spreadsheets. The problem is not data collection - it's data aggregation, visualization, and forward projection. This is a **data pipeline + dashboard** problem, not a new data capture problem.

**Likely existing data sources:**
- Excel/Google Sheets: project cost spreadsheets (labor hours, materials, subcontractor costs by project)
- WorkYard: worker time tracking data (hours per worker per project)
- Service Titan: Beehive job management (service calls, proposals, invoicing)
- QuickBooks or similar: general ledger, AP/AR, payroll

### Why Supabase + Custom Dashboard (Not Off-the-Shelf BI)
| Option | Why Rejected |
|--------|-------------|
| Tableau / Power BI | $70-100/user/mo. Requires technical literacy to build dashboards. Ferris wants a "log in and see it" experience, not a tool he has to learn. Ongoing license cost for 5+ users = $4,200-6,000/yr. |
| Metabase (open source) | Better option but requires self-hosting, maintenance, and SQL knowledge to build views. No built-in alerting. |
| QuickBooks reporting | Already exists. Not granular enough (no cost-per-sqft by trade, no job-type P&L for Beehive). |
| Spreadsheet automation (Zapier + Google Sheets) | Fragile. Breaks when columns change. No RLS. No realtime. |

**Recommendation:** Custom dashboard on Supabase. The data model is specific to Ferris's 4-entity structure, the unit economics calculations are custom, and the forward projection logic needs to be tailored to their business model. Supabase's PostgreSQL gives us full SQL power for complex aggregations.

### Security Considerations
- **Financial data is highly sensitive.** RLS policies must ensure entity-level isolation AND role-based access within entities.
- Finance staff can see their entity's data. Ferris and Brian see everything.
- **No direct database access** for anyone outside the app. All queries go through Supabase RLS.
- **Audit trail:** Every data import logged with who uploaded what, when, and what changed.
- **Data validation:** Imported spreadsheets are validated before writing to the database. Malformed data is rejected with clear error messages, not silently accepted.

### Cost Estimate
| Item | Cost |
|------|------|
| Supabase (shared instance from Project 1) | $0-25/mo |
| Vercel hosting (shared from Project 1) | $0-20/mo |
| Resend email for automated reports | $0/mo (within free tier) |
| **Total** | **$0-45/mo** |

---

## PHASE 1: Data Model & Ingestion Pipeline
**Goal:** Design the unified financial data model and build the pipeline to ingest existing spreadsheet data.

### Issue 3.1: Data Source Audit & Field Mapping Document
**Description:** Before writing any code, audit every spreadsheet and system the finance team currently uses. Map each field to the unified schema.
**Deliverables:**
1. List of ALL spreadsheets/files the finance team maintains with:
   - File name and location
   - Update frequency (daily, weekly, monthly)
   - Who maintains it
   - Key fields/columns
   - Data quality notes (any known issues, inconsistencies, missing data)
2. List of ALL external systems with exportable data:
   - WorkYard (time tracking exports)
   - Service Titan (job/invoice exports)
   - Accounting software (GL exports)
3. Field mapping: source column → unified schema field for each data source
4. Data gaps: what data is needed for the dashboard but currently not captured

**This is a RESEARCH issue.** Requires sitting with Madison Scott or the finance team for 1-2 hours to catalog their workflow.

**Git Commit Message:** `docs(data): financial data source audit and field mapping document`

**Acceptance Criteria:**
- [ ] Every spreadsheet cataloged with columns, update frequency, and owner
- [ ] Every external system documented with export format
- [ ] Field mapping covers all sources
- [ ] Data gaps identified and documented
- [ ] Finance team has reviewed and confirmed the audit

---

### Issue 3.2: Unified Financial Data Model (Supabase Schema)
**Description:** Design and create the PostgreSQL schema that unifies all financial data into a queryable structure optimized for the dashboard views Ferris wants.
**Core Tables:**
```sql
-- Business entities
CREATE TABLE business_units (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name TEXT NOT NULL, -- 'Ferris Development', 'Beehive', 'Expedited Construction', 'Expedited Engineering'
  type TEXT CHECK (type IN ('development', 'trades', 'construction', 'engineering'))
);

-- Properties/buildings in the portfolio
CREATE TABLE properties (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name TEXT NOT NULL,
  address TEXT,
  business_unit_id UUID REFERENCES business_units(id),
  property_type TEXT, -- 'office', 'residential', 'mixed_use', 'construction_site'
  total_sqft NUMERIC(10,2),
  status TEXT CHECK (status IN ('active', 'under_construction', 'sold', 'held')),
  acquisition_date DATE,
  acquisition_cost NUMERIC(14,2)
);

-- Individual jobs/projects (both Ferris buildouts and Beehive service jobs)
CREATE TABLE projects (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name TEXT NOT NULL,
  property_id UUID REFERENCES properties(id),
  business_unit_id UUID REFERENCES business_units(id) NOT NULL,
  project_type TEXT NOT NULL, -- 'buildout', 'service_call', 'install', 'maintenance'
  trade TEXT, -- 'electrical', 'plumbing', 'hvac', 'general', 'framing', 'fire_protection'
  status TEXT CHECK (status IN ('planned', 'in_progress', 'completed', 'cancelled')),
  budgeted_cost NUMERIC(12,2),
  actual_cost NUMERIC(12,2),
  sqft NUMERIC(10,2),
  start_date DATE,
  estimated_completion DATE,
  actual_completion DATE,
  notes TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Line-item costs for each project
CREATE TABLE project_costs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  project_id UUID REFERENCES projects(id) NOT NULL,
  cost_type TEXT CHECK (cost_type IN ('labor_internal', 'labor_external', 'materials', 'equipment', 'permits', 'subcontractor', 'overhead', 'other')) NOT NULL,
  vendor TEXT,
  description TEXT NOT NULL,
  amount NUMERIC(12,2) NOT NULL,
  date DATE NOT NULL,
  was_price_checked BOOLEAN DEFAULT FALSE, -- procurement control flag
  competing_quotes JSONB, -- [{"vendor": "X", "amount": 46000}, {"vendor": "Y", "amount": 126000}]
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Revenue entries (rent, service invoices, project billings)
CREATE TABLE revenue_entries (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  property_id UUID REFERENCES properties(id),
  project_id UUID REFERENCES projects(id),
  business_unit_id UUID REFERENCES business_units(id) NOT NULL,
  revenue_type TEXT CHECK (revenue_type IN ('rent', 'service_invoice', 'install_invoice', 'sale', 'other')),
  tenant_or_customer TEXT,
  amount NUMERIC(12,2) NOT NULL,
  date DATE NOT NULL,
  recurring BOOLEAN DEFAULT FALSE,
  notes TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Labor hours (imported from WorkYard or manual entry)
CREATE TABLE labor_entries (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  project_id UUID REFERENCES projects(id) NOT NULL,
  worker_name TEXT NOT NULL,
  worker_id UUID REFERENCES profiles(id),
  trade TEXT,
  hours NUMERIC(6,2) NOT NULL,
  hourly_rate NUMERIC(8,2) NOT NULL,
  date DATE NOT NULL,
  source TEXT DEFAULT 'manual', -- 'workyard', 'manual', 'service_titan'
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Data import log (audit trail)
CREATE TABLE import_log (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  uploaded_by UUID REFERENCES auth.users(id) NOT NULL,
  file_name TEXT NOT NULL,
  file_type TEXT, -- 'xlsx', 'csv'
  source_system TEXT, -- 'manual_spreadsheet', 'workyard_export', 'service_titan_export'
  rows_imported INT,
  rows_rejected INT,
  errors JSONB,
  created_at TIMESTAMPTZ DEFAULT NOW()
);
```

**Key Design Decisions:**
- `project_costs.was_price_checked` directly addresses Ferris's complaint about the $38K plumbing order. The procurement alert system (Issue 3.8) uses this flag.
- `project_costs.competing_quotes` stores the comparison data Ferris wants (vendor A at $126K vs vendor B at $46K).
- `labor_entries` is separate from `project_costs` because it needs hourly granularity for the unit economics calculations.

**RLS Policies:**
- Finance staff: read/write for their business unit
- Managers: read for their business unit
- Ferris + Brian: read/write across all business units
- Bookkeepers: write (import) for their business unit, read own imports only

**Git Commit Message:** `feat(db): unified financial data model with projects, costs, revenue, and labor tables`

**Acceptance Criteria:**
- [ ] All tables created with proper constraints and foreign keys
- [ ] RLS policies enforce entity-level isolation
- [ ] Business units seeded (4 entities)
- [ ] Sample data inserted for at least 1 project per entity to test queries
- [ ] Import log table tracks all data imports

---

### Issue 3.3: Spreadsheet Ingestion Pipeline (Excel/CSV Upload)
**Description:** Build the automated import system that takes the finance team's existing spreadsheets and loads them into the unified schema.
**User Flow:**
1. Finance user clicks "Import Data" on dashboard
2. Selects file type: Project Costs / Labor Hours / Revenue
3. Uploads .xlsx or .csv file
4. System shows preview: first 10 rows mapped to schema fields
5. User confirms or adjusts column mapping
6. System validates all rows:
   - Required fields present
   - Numeric fields are valid numbers
   - Dates parse correctly
   - Foreign key references exist (project_id, business_unit_id)
7. Valid rows imported, invalid rows shown in error report
8. Import logged to `import_log` table

**Implementation:**
- File upload to Supabase Storage (temporary, deleted after import)
- Parsing via SheetJS (xlsx) in browser or Edge Function
- Column mapping UI: dropdowns matching source columns to schema fields
- Template system: save column mappings so repeat uploads from the same spreadsheet format are one-click

**Git Commit Message:** `feat(import): spreadsheet upload with column mapping, validation, and error reporting`

**Acceptance Criteria:**
- [ ] .xlsx and .csv files accepted
- [ ] Preview shows first 10 rows with mapped columns
- [ ] Validation catches: missing required fields, invalid numbers, bad dates
- [ ] Valid rows import successfully
- [ ] Invalid rows shown with specific error messages per row
- [ ] Import logged with row counts and errors
- [ ] Saved templates work for repeat uploads

---

### Issue 3.4: WorkYard & Service Titan Data Integration
**Description:** Build automated or semi-automated import from WorkYard (time tracking) and Service Titan (Beehive job management).
**WorkYard Integration:**
- WorkYard exports time data as CSV. Build a dedicated import template that maps WorkYard columns to `labor_entries` automatically.
- If WorkYard has an API: build a scheduled sync (daily) via Supabase Edge Function
- If API not available: CSV upload with pre-configured mapping (no manual column matching needed)

**Service Titan Integration:**
- Service Titan has a REST API. Build an Edge Function that syncs:
  - Completed jobs → `projects` table (project_type = 'service_call' or 'install')
  - Job costs → `project_costs` table
  - Invoices → `revenue_entries` table
- Sync frequency: daily at midnight
- Handle duplicates: use Service Titan job ID as external_id, upsert on conflict

**Git Commit Message:** `feat(import): WorkYard time tracking and Service Titan job data integrations`

**Acceptance Criteria:**
- [ ] WorkYard CSV import works with pre-configured template
- [ ] Service Titan API sync pulls jobs, costs, and invoices
- [ ] No duplicate records on re-import
- [ ] Import log tracks all syncs with row counts
- [ ] Error handling: if Service Titan API is down, retry in 1 hour (max 3 retries)

---

## PHASE 2: Core Dashboard Views
**Goal:** Build the dashboard views Ferris described - P&L by business unit, property-level financials, and unit economics.

### Issue 3.5: Real-Time P&L by Business Unit
**Description:** The primary dashboard view - profit and loss for each of Ferris's 4 entities, updated as data is imported.
**Layout:**
```
┌─────────────────────────────────────────────────────┐
│ Period: [Q1 2026 ▼]  Entity: [All ▼]               │
├─────────────┬──────────┬──────────┬────────┬────────┤
│             │ Ferris   │ Beehive  │ Exp.   │ Exp.   │
│             │   Dev    │          │ Const  │ Eng    │
├─────────────┼──────────┼──────────┼────────┼────────┤
│ Revenue     │ $X,XXX   │ $X,XXX   │ $X,XXX │ $X,XXX │
│ - Rent      │ $X,XXX   │    -     │    -   │    -   │
│ - Service   │    -     │ $X,XXX   │    -   │    -   │
│ - Install   │    -     │ $X,XXX   │    -   │    -   │
│ - Eng Fees  │    -     │    -     │    -   │ $X,XXX │
├─────────────┼──────────┼──────────┼────────┼────────┤
│ COGS        │ $X,XXX   │ $X,XXX   │ $X,XXX │ $X,XXX │
│ - Labor Int │ $X,XXX   │ $X,XXX   │ $X,XXX │ $X,XXX │
│ - Labor Ext │ $X,XXX   │ $X,XXX   │ $X,XXX │    -   │
│ - Materials │ $X,XXX   │ $X,XXX   │ $X,XXX │ $X,XXX │
│ - Subs      │ $X,XXX   │    -     │ $X,XXX │    -   │
├─────────────┼──────────┼──────────┼────────┼────────┤
│ Gross Margin│ $X,XXX   │ $X,XXX   │ $X,XXX │ $X,XXX │
│ GM %        │   XX%    │   XX%    │   XX%  │   XX%  │
├─────────────┼──────────┼──────────┼────────┼────────┤
│ Operating   │ $X,XXX   │ $X,XXX   │ $X,XXX │ $X,XXX │
│ Net Income  │ $X,XXX   │ $X,XXX   │ $X,XXX │ $X,XXX │
└─────────────┴──────────┴──────────┴────────┴────────┘
```

**Filters:** Period (month/quarter/year), Entity (all or specific), Property (all or specific)
**Click-through:** Clicking any cell drills down to the underlying project-level data

**Git Commit Message:** `feat(ui): real-time P&L dashboard by business unit with drill-down`

**Acceptance Criteria:**
- [ ] P&L table renders for all 4 entities
- [ ] Revenue and cost breakdowns are correct
- [ ] Period filter works (month, quarter, year)
- [ ] Entity filter works
- [ ] Clicking a cell drills down to project-level detail
- [ ] Numbers update when new data is imported (no page refresh needed)

---

### Issue 3.6: Unit Economics Calculator (Cost Per Square Foot by Trade)
**Description:** This is the specific metric Ferris said he needs: cost per square foot for electrical, plumbing, HVAC, and other trades across all projects. This is what lets him price Beehive third-party work competitively.
**Calculation:**
```
Cost per sqft (electrical) = SUM(project_costs WHERE trade='electrical') / SUM(projects.sqft WHERE trade='electrical')
```
**Dashboard View:**
- Table: Trade | # Projects | Total Cost | Total SqFt | Cost/SqFt | Avg Job Size
- Filter by: time period, business unit, project type (buildout vs. service)
- Chart: Cost/SqFt trend over time (line chart by quarter)

**In-House vs. External Comparison:**
- Side-by-side: internal labor cost for job type X vs. average third-party bid
- Uses `project_costs.cost_type` to separate 'labor_internal' from 'labor_external' and 'subcontractor'
- The fire head example: internal crew = ~$20K vs third-party bids of $84-91K

**Git Commit Message:** `feat(ui): unit economics calculator with cost-per-sqft by trade and in-house vs external comparison`

**Acceptance Criteria:**
- [ ] Cost per sqft calculated correctly for each trade
- [ ] In-house vs external comparison renders side-by-side
- [ ] Filters work (period, entity, project type)
- [ ] Trend chart shows cost/sqft over time
- [ ] Data exportable to CSV for finance team

---

### Issue 3.7: Property-Level Financial View
**Description:** Each property in the Ferris portfolio gets its own financial summary. Ferris said he wants to see "which buildings are healthy, which ones are trending in the right direction and why."
**Per-Property View:**
- Property name, address, total sqft, acquisition date and cost
- Monthly income (rent + service revenue)
- Monthly expenses (maintenance, buildout costs, operating expenses)
- NOI (Net Operating Income) = Income - Expenses
- Cap rate = NOI / Acquisition Cost
- Occupancy rate (if applicable)
- Active buildout projects and their status/budget

**Portfolio Overview:**
- All properties in a sortable table
- Color-coded: Green (NOI positive and growing), Yellow (NOI positive but flat/declining), Red (NOI negative)
- Sort by: NOI, revenue, occupancy, cap rate

**Git Commit Message:** `feat(ui): property-level financials with NOI, cap rate, and portfolio health overview`

**Acceptance Criteria:**
- [ ] Each property shows income, expenses, and NOI
- [ ] Portfolio overview table with color-coded health indicators
- [ ] Sorting works on all columns
- [ ] Cap rate calculated correctly
- [ ] Active buildout projects shown per property

---

## PHASE 3: Forward Projections & Procurement Controls
**Goal:** Add the forward-looking capabilities and procurement safeguards Ferris described.

### Issue 3.8: Two-Quarter Forward Projection Engine
**Description:** Build a projection model that extrapolates current financial data into a 6-month forward P&L.
**Methodology:**
1. **Revenue projection:**
   - Recurring revenue (rent): carry forward current monthly amounts, adjusting for known lease expirations and new leases
   - Beehive service revenue: use trailing 3-month average with growth rate derived from month-over-month trend
   - Project revenue: use pipeline data (projects in 'planned' status with estimated start dates)
2. **Cost projection:**
   - Fixed costs (payroll, insurance, overhead): carry forward current monthly amounts
   - Variable costs (materials, subs): scale with projected revenue using historical cost-to-revenue ratio
   - Known future costs (committed purchases, planned projects): include at their budgeted amounts
3. **Output:** Projected P&L for each of the next 6 months, by business unit

**Assumptions clearly labeled.** Every projected number shows the methodology used (e.g., "Based on 3-month trailing average with 12% MoM growth rate from Beehive service trend").

**Git Commit Message:** `feat(projections): two-quarter forward P&L projection engine with methodology labels`

**Acceptance Criteria:**
- [ ] Forward P&L generates for 6 months out
- [ ] Revenue projections use appropriate methodology per type
- [ ] Cost projections scale with historical ratios
- [ ] Known pipeline items included at budgeted amounts
- [ ] Every projected number shows its methodology
- [ ] Projections update when new actuals are imported

---

### Issue 3.9: Year-Over-Year Comparison Views
**Description:** Dashboard overlays comparing current period to same period last year.
**Views:**
- P&L table with YoY columns: This Year | Last Year | Change ($) | Change (%)
- Revenue trend chart: current year line vs prior year line (12-month view)
- Cost trend chart: same format
- Beehive-specific: revenue trajectory overlay (2024 vs 2025 vs 2026 projected)

**Git Commit Message:** `feat(ui): year-over-year comparison overlays on P&L and trend charts`

**Acceptance Criteria:**
- [ ] YoY columns appear on P&L table
- [ ] Revenue and cost trend charts show current vs prior year
- [ ] Beehive multi-year trajectory renders correctly
- [ ] Positive changes highlighted green, negative red
- [ ] Works with partial-year data (doesn't break if Q4 data not yet available)

---

### Issue 3.10: Procurement Alert System
**Description:** Automated flagging when purchase orders above a threshold go out without competitive bids. Directly addresses the $38K FW Webb plumbing order.
**Logic:**
1. When a `project_cost` entry is created with `amount > $5,000` (configurable threshold):
   - Check `was_price_checked` flag
   - If FALSE: create an alert visible to Ferris + project manager
   - Alert shows: vendor, amount, project, date, and prompts for competing quotes
2. Dashboard widget: "Unchecked Purchases" showing all flagged items
3. Resolution flow: manager adds competing quotes (`competing_quotes` JSONB field), marks as resolved
4. Monthly summary: total spend that went through without price checks vs. total that was checked

**Git Commit Message:** `feat(procurement): automated alerts for large purchases without competitive bids`

**Acceptance Criteria:**
- [ ] Purchases over threshold without price check generate alerts
- [ ] Alerts visible on dashboard and via email to Ferris
- [ ] Resolution flow: add competing quotes and mark resolved
- [ ] Monthly summary shows procurement compliance rate
- [ ] Threshold configurable by admin

---

### Issue 3.11: Beehive Financial Profile Export (Investor-Ready)
**Description:** Generate a formatted financial profile of Beehive suitable for PE presentation or investor discussions. This is the long-term play Ferris described.
**Report Contents:**
- Revenue by service type (service calls, installs, maintenance contracts)
- Average P&L by job type (water heater replacement, HVAC install, electrical service, etc.)
- Average labor hours per job type
- Average material cost per job type
- Customer acquisition cost (if marketing spend data available)
- Revenue trajectory: monthly revenue with growth rate
- Customer metrics: total customers, recurring vs one-time, avg revenue per customer
- Geographic breakdown (local vs Martha's Vineyard)
- EBITDA and EBITDA margin

**Output:** Professional PDF with charts. Also exportable as Excel for PE due diligence.

**Git Commit Message:** `feat(reports): Beehive investor-ready financial profile with PDF and Excel export`

**Acceptance Criteria:**
- [ ] Report generates with all sections populated from actual data
- [ ] PDF is clean and professional
- [ ] Excel export includes raw data behind each chart
- [ ] Revenue trajectory chart shows growth clearly
- [ ] EBITDA calculated correctly
- [ ] Report can be regenerated on demand as new data comes in

---

## PHASE 4: Deployment & Onboarding
**Goal:** Deploy to production and train the finance team on the import workflow.

### Issue 3.12: Production Deployment & Finance Team Training
**Description:** Deploy the financial dashboard and train Madison Scott and the finance team on the data import workflow.
**Steps:**
1. Deploy dashboard to Vercel (shared infrastructure from Projects 1 & 2)
2. Create accounts for finance team with appropriate roles
3. Import historical data: at minimum 6 months of project costs, labor, and revenue to populate the dashboard
4. Walk through the import workflow with Madison: upload spreadsheet → map columns → validate → import
5. Walk through the dashboard with Ferris: P&L view, unit economics, property view, projections
6. Document the expected weekly/monthly import cadence

**Git Commit Message:** `chore(deploy): financial dashboard production deployment and team onboarding`

**Acceptance Criteria:**
- [ ] Dashboard live in production with historical data
- [ ] Finance team can import data without developer assistance
- [ ] Ferris can log in and navigate all dashboard views
- [ ] At least 6 months of historical data populated
- [ ] Import cadence documented and agreed with finance team

---

## TOTAL ISSUES: 12
## ESTIMATED COST: $0-45/mo (shared Supabase + Vercel instance)
## ESTIMATED BUILD TIME: 5-7 weeks (1 developer, data audit may take 1 week with finance team)
## CRITICAL DEPENDENCY: Requires cooperation from Madison Scott / finance team for data audit (Issue 3.1) and historical data import (Issue 3.12)
