# Ferris Development Group - Growth Analysis & Implementation Priorities

**Source:** Consultant Report by Michael Greystone (AI Innovators Bootcamp, Babson College)
**Date:** February 18, 2026 - Southborough, MA
**Client:** David Ferris, Founder & CEO

---

## Company Overview

David Ferris runs **four interconnected companies**:
1. **Ferris Development Group** - Real estate development
2. **Beehive** - Trades services subsidiary (launched mid-2024)
3. **Expedited Construction** - Construction operations
4. **Expedited Engineering** - Engineering services

### Key Metrics
- **Headcount:** ~60 people
- **Active Buildouts:** 8 concurrent projects
- **Flagship Project:** $45M drug recovery center under construction
- **Beehive Revenue Trajectory:**
  - First 6 months (2024): $800K
  - Full year 2025: $3M
  - 2026 Projection: $10-12M
- **Weekly Labor Costs:** ~$75,000 across construction/trades
- **Notable Projects:** 260 multifamily units at Westboro, 76 condos in Marlboro, 32 townhomes in Southborough

---

## Core Problem

> The operating infrastructure was built for a 15-person company, and it is now being asked to support an organization four times that size.

Verbal directives, gut-feel management, and personal oversight carried the business through early growth. At 60 people and 8 active projects, those methods are showing real cracks.

---

## Gap #1: Accountability Without Infrastructure

### The Problem
- Verbal directives live in a gray zone between suggestion and requirement
- No deadlines, no owners, no tracking mechanisms for tasks
- Example: A simple instruction ("mark two-thirds of coworking pods as Reserved") was repeated multiple times over 2 months and never executed - not because of personnel failure, but because it was never formally assigned

### Current Workaround
- Ferris personally fills the gap: showing up at job sites at 6am, walking floors, checking in
- This does not scale

### Ferris Quote
> "The worst thing a company at our size can handle is any project or deliverable without a deadline. Without deadlines, you're a dying company."

### What Needs to Be Built
- Every verbal directive converted into a **timestamped, assigned deliverable** with an owner and due date before the conversation ends
- Shared dashboard visible to the entire team
- Habit enforcement across every level of the organization

---

## Gap #2: Labor Productivity

### The Problem
- $75K/week in labor costs with no real-time visibility into what workers are actually doing
- Phone use on job sites is the #1 flagged issue
- One worker logged **171 minutes of phone use and 78 pickups** in a single workday - not an outlier
- Even a **20% productivity recovery** would justify nearly any reasonable capital investment

### Current Tools (Workarounds, Not Systems)
- **WorkYard** - GPS-based clock-ins
- $100 weekly safety bonus
- Site supervisor (Kenny) walking the floor

### What Ferris Wants Built
1. **AI-powered camera system** - Commercial-grade hardware running automated software that:
   - Tracks phone use on job sites
   - Produces a weekly worker productivity report
   - Formatted like the Verizon driving app
   - Estimated cost: $10-20K

2. **Pre-hire onboarding video/testing module**
   - "Guaranteed not to last at Ferris Companies" orientation
   - Must be watched and tested before field deployment
   - Sets clear behavioral expectations before someone starts on site

---

## Gap #3: Financial Reporting

### The Problem
- Financial data reaches Ferris **after the fact**
- No real-time P&L visibility by business unit
- No automated reporting
- No forward-looking model projecting 2 quarters out
- Quarterly reforecast is manual, backward-looking, labor-intensive

### Specific Data Gaps
- **Does not know cost per square foot for electrical work** across last 8 jobs (needed to price third-party Beehive work)
- **Cannot quickly compare in-house vs. contracted labor costs** (though his intuition is sharp: estimated saving $40-45K on a single fire head project by using own crew vs. third-party bids at $84-91K)
- **No automated procurement controls** - a $38,000 plumbing order went out without a competitive price check

### What Needs to Be Built
- Standard BI layer on top of data the team already generates
- **Real-time P&L dashboard** segmented by:
  - Building
  - Business unit
  - Job type
- Two-quarter forward projections
- Year-over-year comparison
- Unit economics by service type
- Long-term: Formalize Beehive's financial profile (avg P&L by job type, labor hours, material costs) for PE/public market presentation

---

## Gap #4: Underleveraged Growth Opportunity (Beehive Marketing & Training)

### The Opportunity
- Of $10-12M projected 2026 revenue, ~$6-7M is captive (internal Ferris projects)
- **Third-party market** is where the valuation story gets built
- More external customers on recurring service contracts = higher EBITDA multiple for eventual exit

### What's Missing

**1. Targeted Digital Marketing at Speed**
- Example: Cold snap forecast for Friday -> by Thursday afternoon, emergency plumbing ads are live on Google, geo-targeted to service area, pulling calls over the weekend
- Today: requires 10 steps, pulls multiple people off other work
- Goal: **Should take 3 steps**

**2. Technician Upsell Training**
- Beehive techs need training as solution-oriented service providers
- Must identify upsell opportunities in the field
- Training module does not exist yet

### Underused Asset
- **Go Happy** (video production company in same building) could produce structured Beehive service content at low cost
- A few well-made videos -> fed into AI tools for versioning and targeting -> closes gap between current and needed marketing operation

---

## What Is Already Working (Structural Advantages)

- **Vertical integration:** Four entities with in-house engineering, construction, and trades under one umbrella creates a cost advantage competitors can't replicate
- **Cost advantage example:** Fire head installation at $20K vs. third-party quotes of $84-91K
- **Zoning expertise:** Unlocking overlays where others saw only surface lots
- **Cross-pollination culture:** People across entities know each other's roles, built-in leadership redundancy
- **Ferris's personal involvement:** On job sites at 6am, contacting governor's office on housing policy, researching National Grid feeder study timelines

---

## Ferris-Ranked Implementation Priorities

### Priority 1: AI Camera & Productivity Monitoring
- Install job-site camera system with automated phone-use tracking
- Weekly productivity reporting
- Capital outlay: $10-20K
- Shortest payback window of any investment on the table
- Extends WorkYard GPS concept to on-site behavior

### Priority 2: Beehive Marketing Engine & Training
- Repeatable content & distribution workflow (video production, AI-assisted copy, Google Local Services Ads)
- Goal: Launch targeted campaign in under 1 hour when market opportunity appears
- Mandatory training/testing module for new Beehive technicians
- Standardize field performance before deployment

### Priority 3: Financial Dashboard
- Automate data ingestion from existing project cost spreadsheets
- Real-time P&L dashboard by building, business unit, job type
- Two-quarter forward projections, YoY comparison, unit economics by service type
- **Prerequisite for everything that comes after** - cannot replicate and scale a business model you haven't quantified at a granular level

---

## BUILD PHASES (Proposed)

> The following phases break each priority into hyper-specific, commit-ready issues. Each issue is scoped for a single focused git push with a clear deliverable.

---

### PHASE 1: Task Accountability System (Addresses Gap #1)

| Issue # | Title | Deliverable |
|---------|-------|-------------|
| 1.1 | Data model for task/directive tracking | Schema: tasks table with fields for owner, deadline, status, source_directive, created_at, completed_at |
| 1.2 | Task creation API endpoint | POST /api/tasks - accepts directive text, assignee, deadline; returns timestamped task object |
| 1.3 | Task list/dashboard backend | GET /api/tasks with filters (by owner, status, overdue); aggregation endpoints for dashboard stats |
| 1.4 | Team dashboard UI - task board view | Kanban-style board showing open/in-progress/completed tasks with owner avatars and due dates |
| 1.5 | Overdue task alerting system | Cron job that flags overdue tasks, sends notifications (email/SMS), escalates after 24h |
| 1.6 | Voice-to-task capture (stretch) | Integration that converts a spoken directive into a structured task with NLP extraction of assignee + deadline |

---

### PHASE 2: Labor Productivity Monitoring (Addresses Gap #2 - Ferris Priority #1)

| Issue # | Title | Deliverable |
|---------|-------|-------------|
| 2.1 | Camera system hardware spec & vendor research | Document: recommended camera hardware, mounting plans, network requirements, cost breakdown |
| 2.2 | Video ingestion pipeline scaffold | Service that accepts camera feeds, stores frames, and queues for analysis |
| 2.3 | Phone detection ML model integration | Integrate pre-trained object detection model (YOLO/similar) to flag phone-in-hand events from frames |
| 2.4 | Worker identification & event logging | System to associate detected phone events with specific workers (badge/zone mapping), log to database |
| 2.5 | Weekly productivity report generator | Automated report: per-worker phone usage minutes, pickup count, comparison to crew average, formatted PDF |
| 2.6 | Report delivery & dashboard display | Email delivery of weekly PDF + web dashboard with drill-down by worker, date, job site |
| 2.7 | Pre-hire onboarding video module | Video hosting + quiz system: new hires watch mandatory orientation, must pass test before field deployment |
| 2.8 | Onboarding completion tracking | Admin view showing which new hires have completed onboarding, pass/fail status, completion dates |

---

### PHASE 3: Financial Dashboard (Addresses Gap #3 - Ferris Priority #3)

| Issue # | Title | Deliverable |
|---------|-------|-------------|
| 3.1 | Data source audit & ingestion mapping | Document: all existing spreadsheets/systems with financial data, field mapping to unified schema |
| 3.2 | Unified financial data model | Database schema for project costs, labor hours, material costs, organized by building/business unit/job type |
| 3.3 | Spreadsheet ingestion ETL pipeline | Automated import from Excel/Google Sheets project cost files into unified database |
| 3.4 | Real-time P&L by business unit | Dashboard view: revenue, COGS, gross margin, operating expenses by Ferris Dev / Beehive / Expedited Construction / Expedited Engineering |
| 3.5 | Unit economics calculator | Cost-per-sqft by trade (electrical, plumbing, fire protection), in-house vs. contracted labor comparison |
| 3.6 | Two-quarter forward projection engine | Model that extrapolates current run-rate + pipeline data into 6-month forward P&L projections |
| 3.7 | YoY comparison views | Dashboard overlays comparing current period to same period last year by all dimensions |
| 3.8 | Procurement alert system | Flagging system for purchase orders above threshold without competitive bid documentation |
| 3.9 | Beehive financial profile export | Formatted output of Beehive avg P&L by job type, labor hours, material costs - investor/PE-ready format |

---

### PHASE 4: Beehive Marketing Engine (Addresses Gap #4 - Ferris Priority #2)

| Issue # | Title | Deliverable |
|---------|-------|-------------|
| 4.1 | Weather-triggered campaign system design | Architecture doc: weather API integration, trigger rules (cold snap -> plumbing ads), campaign template system |
| 4.2 | Campaign template library | Pre-built ad templates for each Beehive service line (plumbing, electrical, HVAC) with variable slots for geo/timing |
| 4.3 | Google Ads API integration | Service that can programmatically create/launch/pause geo-targeted Google Local Services Ads campaigns |
| 4.4 | One-click campaign launcher | UI: select service type + trigger condition -> system auto-generates copy, sets geo-targeting, launches campaign |
| 4.5 | AI copy generation for ad variants | Integration with LLM to generate ad copy variants from service templates + situational context |
| 4.6 | Campaign performance dashboard | Track spend, impressions, clicks, calls, cost-per-lead by campaign type and service line |
| 4.7 | Technician upsell training module | Video-based training system: identify upsell opportunities in field, scripted responses, quiz assessment |
| 4.8 | Video content pipeline with Go Happy | Workflow for producing structured Beehive service videos, AI-assisted versioning for different platforms/audiences |

---

### Summary: Commit Cadence

Each issue above is designed to be:
- **One focused git push** with a clear, reviewable deliverable
- **Self-contained** enough to test and demo independently
- **Sequential within phase** (each builds on the prior issue)
- **Phases can run in parallel** where team capacity allows (e.g., Phase 3 data audit while Phase 2 hardware is procured)

**Total issues across all phases: 31**
