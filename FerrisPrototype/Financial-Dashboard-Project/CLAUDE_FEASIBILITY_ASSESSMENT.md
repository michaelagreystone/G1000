# Claude Code Feasibility Assessment: Financial Dashboard Project

**Assessment Date:** March 4, 2026
**Purpose:** Honest evaluation of what Claude can build, what requires YOUR action, and what will trip you up if you're not prepared.

---

## ISSUE-BY-ISSUE CAPABILITY BREAKDOWN

### GREEN = Claude can build this fully in-session
### YELLOW = Claude can build the code, but YOU must do something external
### RED = Claude cannot do this - entirely on you

---

### Issue 3.1: Data Source Audit & Field Mapping
**Rating: RED - 100% on you**

This requires sitting with Madison Scott and the finance team. I cannot:
- Access their computers to see their spreadsheets
- Interview them about their workflow
- Determine which columns map to what
- Assess data quality in files I've never seen

**What you need to prepare:**
- Schedule a 1-2 hour meeting with Madison Scott (finance lead)
- Bring a laptop and take notes in a structured format
- Ask to see EVERY spreadsheet they maintain - take screenshots of column headers
- Ask: "What accounting software do you use?" (QuickBooks? Xero? Sage?)
- Get a sample export from WorkYard and Service Titan (even just 10 rows)
- Document the exact column names, data types, and any quirks ("oh we sometimes put notes in the amount column")

**What I CAN do after you bring me the data:**
- Create the field mapping document from your notes
- Identify gaps between their data and what the dashboard needs
- Design the schema based on actual column names, not assumptions

**CRITICAL:** The schema in the action plan (Issue 3.2) is my best guess based on the interview transcript. The REAL schema will change after this audit. Do NOT skip this step or the entire import pipeline will break on contact with real data.

---

### Issue 3.2: Unified Financial Data Model
**Rating: GREEN (after 3.1 is done)**

I can write every line of SQL. Supabase migrations, RLS policies, indexes, seed data - all of it. This is straightforward PostgreSQL work.

**Caveat:** The schema in the plan is a starting point. After the data audit (3.1), I'll need to adjust:
- Column names to match what the finance team actually exports
- Data types that match their reality (do they track sqft as integers or decimals? do they use project codes?)
- Additional tables if they have data structures I didn't anticipate from the interview

**What you need to prepare:**
- A Supabase project created (free tier is fine). Go to supabase.com, create an account, create a project.
- Give me the project URL and anon key (NOT the service role key - that one stays with you)
- Or: I can write the SQL migrations as files and you run them in the Supabase SQL editor yourself

---

### Issue 3.3: Spreadsheet Ingestion Pipeline
**Rating: GREEN - This is where Claude shines**

I can build the entire upload → preview → map → validate → import flow. This is React + SheetJS + Supabase client code. Fully within my capability.

**What I'll build:**
- File upload component (drag-and-drop .xlsx/.csv)
- SheetJS parsing in the browser (no server needed for parsing)
- Column mapping UI with dropdowns
- Row validation with clear error messages
- Supabase insert with import logging
- Saved mapping templates

**What you need to prepare:**
- 2-3 sample spreadsheets from the finance team (from Issue 3.1) so I can test against real data formats
- These don't need to contain real financial numbers - column headers and data structure are what matter. The finance team can sanitize amounts if sensitive.

---

### Issue 3.4: WorkYard & Service Titan Integration
**Rating: YELLOW - Code is easy, access is the bottleneck**

**WorkYard:**
- If it only exports CSV: GREEN. I build a pre-configured import template. Simple.
- If it has an API: YELLOW. I can write the integration code, but YOU need to get API credentials from WorkYard. This may require contacting their support or asking Kevin Puquette (he likely manages the account).

**Service Titan:**
- YELLOW with a major asterisk. Service Titan's API requires:
  1. A Service Titan developer account (apply at developer.servicetitan.com)
  2. API key approval (they review your use case - can take 1-2 weeks)
  3. OAuth2 integration with Beehive's specific Service Titan tenant
  4. Service Titan's API has rate limits and pagination quirks

**What you need to prepare:**
- Ask Kevin Puquette: "What's our WorkYard account? Can we export CSV? Does it have an API?"
- Ask whoever manages Service Titan: "Can we get API access? Who's the admin?"
- Apply for Service Titan developer access NOW (it takes time)
- Alternative: if API access is slow, I'll build it as CSV upload first (Service Titan can export to CSV from their reports). This is the pragmatic path.

**My recommendation:** Start with CSV import for BOTH systems. Get the dashboard working with manual uploads. Add API automation later. Don't let API access delays block the entire project.

---

### Issue 3.5: Real-Time P&L by Business Unit
**Rating: GREEN**

This is a React component with Supabase queries. I can build:
- The P&L table layout (matching the ASCII mockup in the plan)
- SQL aggregation queries for revenue and costs by entity
- Period/entity/property filters
- Drill-down on click (query project_costs WHERE business_unit_id = X AND date BETWEEN Y AND Z)
- Supabase Realtime subscription for live updates

**What you need to prepare:**
- Nothing technical. But you should know: this dashboard will look empty until the finance team imports data (Issue 3.3). Don't demo it to Ferris until there's real data in it.
- Decide: do you want a charting library? I'd recommend **Recharts** (lightweight, React-native) over Chart.js (heavier, canvas-based). Or I can do it with just tables and no charts to keep it simple.

---

### Issue 3.6: Unit Economics Calculator
**Rating: GREEN**

Pure math on data already in the database. The SQL is:
```sql
SELECT trade,
  COUNT(DISTINCT p.id) as project_count,
  SUM(pc.amount) as total_cost,
  SUM(p.sqft) as total_sqft,
  SUM(pc.amount) / NULLIF(SUM(p.sqft), 0) as cost_per_sqft
FROM project_costs pc
JOIN projects p ON pc.project_id = p.id
GROUP BY trade
```

The in-house vs external comparison is equally straightforward.

**What you need to prepare:**
- The finance team MUST enter `sqft` for projects. If they don't track square footage, this calculation doesn't work. Confirm during the data audit (3.1) that sqft data exists.

---

### Issue 3.7: Property-Level Financial View
**Rating: GREEN**

Same pattern as 3.5 - aggregation queries + React table + color coding. NOI and cap rate are simple formulas.

**What you need to prepare:**
- Need `acquisition_cost` for each property to calculate cap rate. If the finance team doesn't track this centrally, you'll need to get it from Ferris or Brian.
- Need to know: which properties does Ferris own? The transcript mentions Westboro, Marlboro, Southborough, Chelmsford, Martha's Vineyard. Get a complete list.

---

### Issue 3.8: Two-Quarter Forward Projection Engine
**Rating: YELLOW - The code is easy, the methodology needs Ferris's sign-off**

I can build any projection model you want. The risk isn't technical - it's that projections are OPINIONS and Ferris may not agree with the methodology.

**The real challenge:**
- Recurring revenue projection is easy (carry forward known leases)
- Beehive growth projection is a judgment call. Do you use 3-month trailing average? 6-month? Do you apply a growth rate? Which rate? Ferris said $3M in 2025 → $10-12M in 2026. That's 230-300% growth. A trailing average won't capture that kind of acceleration.
- Cost projection depends on what Ferris considers "fixed" vs "variable." Payroll is fixed until he hires, then it jumps. Materials scale with projects but not linearly.

**What you need to prepare:**
- Have a 15-minute conversation with Ferris about HOW he wants projections calculated. Ask:
  - "For Beehive revenue, should we project based on last 3 months or use a target growth rate?"
  - "Which costs do you consider fixed vs variable?"
  - "Do you want to manually input pipeline projects, or should the system guess based on historical patterns?"
- I can build multiple projection modes (conservative/moderate/aggressive) and let him toggle between them. That's usually the best approach for a CEO who has strong intuitions.

---

### Issue 3.9: Year-Over-Year Comparison
**Rating: GREEN (if historical data exists)**

Trivially simple SQL and chart rendering.

**What you need to prepare:**
- Need at least 12 months of historical data imported. If the finance team only has 6 months in a usable format, the YoY view will show "No data for prior year" for the first 6 months. That's fine - it fills in over time. But manage Ferris's expectations.

---

### Issue 3.10: Procurement Alert System
**Rating: GREEN**

Database trigger + notification. Straightforward.

**What you need to prepare:**
- Confirm the threshold with Ferris. Plan says $5,000 but he might want $10K or $2,500. This is configurable in the admin UI regardless.
- The procurement alert only works if costs are entered INTO the system. If someone places a $38K order and never logs it in the dashboard, the alert never fires. This is a process/culture change, not a technology problem.

---

### Issue 3.11: Beehive Financial Profile Export
**Rating: YELLOW**

I can generate the PDF and Excel. The challenge is making it look PROFESSIONAL enough for PE investors.

**Options:**
1. **HTML-to-PDF via Puppeteer** - best looking but requires a server/Edge Function with Puppeteer (heavier)
2. **jsPDF** - runs in browser, lighter, but PDF formatting is more manual and less polished
3. **React-PDF (@react-pdf/renderer)** - good middle ground, React components that render to PDF

**My recommendation:** React-PDF. It produces clean PDFs from React components, runs in the browser, and the output is professional enough for investor presentations.

**What you need to prepare:**
- Get an example of a financial profile / pitch deck that PE firms in real estate expect. If Ferris has ever received a CIM (Confidential Information Memorandum) from a deal he evaluated, that's the format to replicate.
- The EBITDA calculation needs operating expense data that may not be in the project cost spreadsheets (rent, insurance, G&A). Confirm this exists during the data audit.

---

### Issue 3.12: Production Deployment
**Rating: GREEN for deployment, RED for training**

I can deploy to Vercel in one command. I can write the user guide. But I cannot:
- Train Madison Scott on the import workflow (that's a screen-share or in-person session you run)
- Import historical data (I need the files first)
- Demo the dashboard to Ferris (that's your meeting)

---

## SUMMARY SCORECARD

| Issue | Claude Can Build? | Your Action Required |
|-------|------------------|---------------------|
| 3.1 Data Audit | NO | Meet with finance team, collect spreadsheet samples |
| 3.2 Schema | YES | Create Supabase project |
| 3.3 Spreadsheet Import | YES | Provide sample spreadsheet files |
| 3.4 WorkYard/Service Titan | PARTIAL | Get API credentials or CSV exports |
| 3.5 P&L Dashboard | YES | None |
| 3.6 Unit Economics | YES | Confirm sqft data exists |
| 3.7 Property View | YES | Get property list and acquisition costs |
| 3.8 Projections | YES (code) | Get Ferris's sign-off on methodology |
| 3.9 YoY Comparison | YES | Need 12+ months historical data |
| 3.10 Procurement Alerts | YES | Confirm threshold with Ferris |
| 3.11 Beehive Profile Export | YES | Get PE report format example |
| 3.12 Deployment | YES (deploy) | You run training sessions |

---

## THE 5 THINGS THAT WILL BLOCK YOU

### 1. The Data Audit (Issue 3.1) - BIGGEST RISK
If you skip this and we build on assumptions from the interview, the import pipeline WILL break when it meets real spreadsheets. Madison Scott's column headers won't match what we assumed. Their date formats will be inconsistent. Some projects won't have sqft. This is not a maybe - it's a certainty.

**Mitigation:** Do the audit FIRST. Even a quick 30-minute call where she screen-shares her spreadsheets is enough. I can work with screenshots of column headers.

### 2. Service Titan API Access
Service Titan gates their API behind a review process. If Beehive doesn't already have developer access, this could take 1-2 weeks.

**Mitigation:** Start with CSV exports from Service Titan's reporting module. Build the API integration as a Phase 2 enhancement. Don't block the project on this.

### 3. Historical Data Quality
The dashboard is only as good as the data in it. If the finance team has been inconsistent (some projects tracked in detail, others barely logged), the P&L will have gaps.

**Mitigation:** During the data audit, identify which projects have complete data. Import those first. Fill gaps over time. Better to show 8 accurate projects than 20 incomplete ones.

### 4. Ferris's Expectations on Projections
Forward projections are inherently imprecise. If Ferris expects the projection to match his gut intuition exactly, he'll be disappointed. If he understands it's a model with assumptions, he'll find it useful.

**Mitigation:** Label every projection with its methodology. Offer multiple scenarios (conservative/moderate/aggressive). Let him override assumptions manually.

### 5. Adoption by the Finance Team
This tool only works if Madison and her team import data regularly. If they see it as "one more thing to do" rather than something that saves them time on the quarterly reforecast, they won't use it.

**Mitigation:** The spreadsheet import (Issue 3.3) must be FAST - under 2 minutes to upload and import. If it's slow or confusing, they'll revert to email and spreadsheets. The saved mapping templates are critical for repeat uploads.

---

## RECOMMENDED BUILD ORDER (Optimized for Claude Sessions)

**Session 1:** Issue 3.2 (schema) - I can do this immediately with no dependencies
**YOU DO:** Issue 3.1 (data audit) in parallel - meet with finance team

**Session 2:** Issue 3.3 (spreadsheet import) - once you bring me sample files from the audit
**Session 3:** Issue 3.5 (P&L dashboard) + Issue 3.6 (unit economics) - these can be built together
**Session 4:** Issue 3.7 (property view) + Issue 3.10 (procurement alerts)
**Session 5:** Issue 3.8 (projections) + Issue 3.9 (YoY) - after Ferris approves methodology
**Session 6:** Issue 3.11 (Beehive export) + Issue 3.4 (WorkYard/Service Titan)
**Session 7:** Issue 3.12 (deployment)

**Each session = 1 focused git push = 1 clean context window.**

---

## WHAT YOU SHOULD DO BEFORE WE START BUILDING

1. **Create a Supabase project** at supabase.com (5 minutes, free)
2. **Schedule the finance team meeting** for the data audit (Issue 3.1)
3. **Get 2-3 sample spreadsheets** from the finance team (even with fake numbers)
4. **Ask Ferris:** "What's the first thing you'd want to see when you log into a financial dashboard?" - his answer tells us which view to polish first
5. **Check Service Titan access** - ask Kevin Puquette if they have API credentials or can export CSV

Once you have items 1-3, we can start Session 1 immediately.
