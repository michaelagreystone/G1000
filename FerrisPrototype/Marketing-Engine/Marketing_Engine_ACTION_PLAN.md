# PROJECT 4: Beehive Marketing Engine & Technician Training

**Client Entity:** Beehive (trades services subsidiary)
**Priority:** #4 in implementation order (last) but high revenue impact - drives third-party customer acquisition
**Stack:** Supabase (Database, Auth, Edge Functions, Storage) + React frontend + Google Ads API + Weather API + LLM for copy generation
**Estimated Build Time:** 5-6 weeks across all phases

---

## BUSINESS CONTEXT (From David Ferris Interview)

Of Beehive's projected $10-12M in 2026 revenue, roughly $6-7M is **captive** (internal Ferris projects). The third-party market is where the valuation story gets built. More external customers on recurring service contracts means a higher EBITDA multiple when Ferris eventually takes Beehive to market (PE or IPO).

**The marketing bottleneck Ferris described:**
> "Getting ads online takes 10 steps when it should take 3. There's a cold snap coming, emergency plumbing ads should be live by Thursday afternoon, pulling calls over the weekend. Today it requires somebody getting a video, somebody getting the LSA account approved, content has to be written... that's something AI could speed up dramatically."

**The training gap:**
Beehive techs are skilled tradespeople but not trained as solution-oriented service providers. When they go to a service call, they fix the immediate problem but don't identify upsell opportunities (e.g., "your water heater is 15 years old - you might want to consider replacement before it fails").

**Current marketing assets:**
- Google LSA (Local Services Ads) account already approved
- **Go Happy** - a video production company operating in the same Ferris building - can produce content at low cost
- Ariela handles some sales/marketing but gets pulled into other work
- ~400 customers, ~150 core (Bass Pro Shops, Marriott Sheraton, etc.)
- Service Titan for job management and customer database

**Ferris on training:** "We're contemplating sending techs to Tennessee for HVAC training modules. If there's already great training for new HVAC techs, I just need to find it, pay the subscription, and I'm cool with it."

---

## FEASIBILITY ASSESSMENT

### Marketing Engine: Build vs. Buy

| Component | Recommendation | Why |
|-----------|---------------|-----|
| Weather-triggered campaign logic | **Build** | No off-the-shelf tool does "cold snap forecast → auto-launch plumbing ads." This is the core innovation. |
| Google Ads management | **Build integration** | Use Google Ads API directly. Tools like WordStream ($300-1000/mo) add unnecessary cost and don't support weather triggers. |
| Ad copy generation | **Build with LLM** | Use Claude API or OpenAI to generate ad copy from templates. Much cheaper than hiring a copywriter for each campaign. |
| Video content production | **Buy (Go Happy)** | Ferris already has Go Happy downstairs. Pay them to shoot 10-15 core service videos. |
| Video AI versioning | **Build** | Use LLM + simple video editing API to create variants from master videos (different intros, different service areas, different CTAs). |
| Technician training | **Hybrid** | Check if Service Titan has training modules first. If not, build a lightweight LMS on Supabase similar to the onboarding module in Project 2. |

### Security Considerations
- **Google Ads API credentials** stored in Supabase Vault. NEVER in client-side code.
- **Ad spend limits** enforced in code: daily maximum, per-campaign maximum, monthly maximum. Cannot be overridden without admin approval. Ferris does NOT want runaway ad spend.
- **LLM-generated copy** must be reviewed before going live (at least initially). Build a "draft → review → publish" workflow, not auto-publish.
- **Customer data** (phone numbers, addresses from Service Titan) stays in Supabase with RLS. Never sent to third-party AI services.

### Cost Estimate
| Item | Monthly Cost |
|------|-------------|
| Supabase (shared instance) | $0-25 |
| Vercel hosting (shared) | $0-20 |
| Google Ads spend (variable - Beehive budget) | $1,000-5,000 (client's ad budget, not our cost) |
| Claude API for copy generation | $5-20 (estimated 500-2000 generations/mo) |
| Weather API (OpenWeatherMap) | $0 (free tier: 1000 calls/day, more than enough) |
| Go Happy video production (one-time) | $2,000-5,000 for initial video library |
| **Platform cost (our build)** | **$25-65/mo** |
| **Ad spend (client controls)** | **$1,000-5,000/mo (Beehive's marketing budget)** |

### Alternative Approaches Considered & Rejected
| Option | Why Rejected |
|--------|-------------|
| HubSpot Marketing Hub | $800-3600/mo. Overkill for a trades company. No weather triggers. |
| Mailchimp / Constant Contact | Email marketing tools, not Google Ads management. Wrong channel for emergency plumbing. |
| Hiring a marketing agency | $3,000-10,000/mo retainer. Cannot react in real-time to weather events. The whole point is speed and automation. |
| Manual campaign management | This IS the current state. It takes 10 steps. The project exists to make it take 3. |

---

## PHASE 1: Campaign Infrastructure
**Goal:** Set up the Google Ads integration, weather monitoring, and campaign template system.

### Issue 4.1: Google Ads API Integration & Account Configuration
**Description:** Connect to Beehive's existing Google Ads / LSA account via the API and build the foundation for programmatic campaign management.
**Steps:**
1. Register for Google Ads API access (requires developer token application - takes 3-7 days for approval)
2. Set up OAuth2 flow for Beehive's Google Ads account
3. Store credentials in Supabase Vault
4. Build Edge Functions for core operations:
   - `createCampaign(params)` - create a new campaign with budget, targeting, and ad copy
   - `pauseCampaign(campaignId)` - pause a running campaign
   - `getCampaignMetrics(campaignId)` - pull performance data (impressions, clicks, calls, cost)
   - `listCampaigns()` - list all campaigns with status and spend
5. Set up Google Local Services Ads integration specifically (LSA has a different API flow than standard Google Ads)
6. Implement spend limits: daily cap, per-campaign cap, monthly cap with alerts at 80% threshold

**Git Commit Message:** `feat(ads): Google Ads API integration with campaign CRUD and spend limits`

**Acceptance Criteria:**
- [ ] OAuth2 connection to Beehive's Google Ads account works
- [ ] Can create a test campaign programmatically
- [ ] Can pause/resume campaigns
- [ ] Can pull performance metrics
- [ ] Spend limits enforced - cannot exceed configured daily/monthly caps
- [ ] All credentials in Supabase Vault, not in code

---

### Issue 4.2: Weather Monitoring & Trigger System
**Description:** Build the automated weather monitoring that triggers campaign launches based on forecast conditions.
**Implementation:**
1. Use OpenWeatherMap API (free tier: 1000 calls/day)
2. Monitor 5-day forecast for Beehive's service area (configurable zip codes / metro area)
3. Create a `weather_triggers` table:
```sql
CREATE TABLE weather_triggers (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  trigger_name TEXT NOT NULL, -- 'Cold Snap', 'Heat Wave', 'Storm Warning'
  condition_type TEXT NOT NULL, -- 'temp_below', 'temp_above', 'weather_event'
  threshold_value NUMERIC, -- e.g., 20 (degrees F)
  weather_codes TEXT[], -- OpenWeatherMap weather condition codes
  service_line TEXT NOT NULL, -- 'plumbing', 'hvac', 'electrical'
  campaign_template_id UUID REFERENCES campaign_templates(id),
  lead_time_hours INT DEFAULT 24, -- how far in advance to trigger
  active BOOLEAN DEFAULT TRUE,
  created_at TIMESTAMPTZ DEFAULT NOW()
);
```
4. Supabase cron job: every 6 hours, check forecast against active triggers
5. When a trigger fires:
   - Log the trigger event
   - Generate ad copy from template (Issue 4.4)
   - Create draft campaign for review
   - Notify marketing manager via SMS/email: "Cold snap forecast for Friday. Draft emergency plumbing campaign ready for review."

**Pre-configured triggers (based on Ferris's examples):**
- Temperature below 20°F within 48 hours → Emergency plumbing (frozen pipes)
- Temperature above 95°F within 48 hours → HVAC emergency service
- Severe storm warning → Emergency electrical / generator services

**Git Commit Message:** `feat(weather): automated weather monitoring with configurable campaign triggers`

**Acceptance Criteria:**
- [ ] Weather API polling runs every 6 hours via cron
- [ ] Triggers fire correctly when forecast meets conditions
- [ ] Draft campaign created automatically on trigger
- [ ] Notification sent to marketing manager
- [ ] Lead time configurable (24h, 48h, etc.)
- [ ] Triggers can be enabled/disabled without code changes

---

### Issue 4.3: Campaign Template Library
**Description:** Pre-built campaign templates for each Beehive service line that can be launched instantly when a trigger fires or a manager decides to run a campaign.
**Templates Structure:**
```sql
CREATE TABLE campaign_templates (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name TEXT NOT NULL,
  service_line TEXT NOT NULL, -- 'plumbing', 'hvac', 'electrical', 'handyman'
  scenario TEXT, -- 'emergency', 'seasonal', 'promotional', 'general'
  headline_template TEXT NOT NULL, -- "Emergency {{service}} in {{city}} - 24/7 Response"
  description_template TEXT NOT NULL, -- template with {{variables}}
  target_radius_miles INT DEFAULT 25,
  target_zip_codes TEXT[],
  default_daily_budget NUMERIC(8,2),
  default_duration_days INT DEFAULT 7,
  keywords TEXT[], -- Google Ads keywords
  negative_keywords TEXT[], -- keywords to exclude
  created_at TIMESTAMPTZ DEFAULT NOW()
);
```

**Initial Template Set:**
| Template | Service | Scenario | Example Headline |
|----------|---------|----------|-----------------|
| Frozen Pipes Emergency | Plumbing | Emergency | "Frozen Pipes? Beehive Plumbing - Emergency Response in {{city}}" |
| Water Heater Failure | Plumbing | Emergency | "No Hot Water? Same-Day Water Heater Repair in {{city}}" |
| AC Breakdown | HVAC | Emergency | "AC Not Working? Beehive HVAC - Fast {{city}} Service" |
| Heating System Failure | HVAC | Emergency | "Heater Down? Emergency Heating Repair - Beehive {{city}}" |
| Electrical Emergency | Electrical | Emergency | "Power Out? Licensed Electricians in {{city}} - 24/7" |
| Seasonal HVAC Tune-Up | HVAC | Seasonal | "Get Your {{system_type}} Ready for {{season}} - Beehive {{city}}" |
| General Plumbing | Plumbing | General | "Trusted Plumbers in {{city}} - Beehive Pros" |
| General Electrical | Electrical | General | "Licensed Electricians in {{city}} - Beehive Pros" |

**Git Commit Message:** `feat(templates): campaign template library with 8 initial templates for Beehive service lines`

**Acceptance Criteria:**
- [ ] All 8 templates created and stored in database
- [ ] Variable substitution works ({{city}}, {{service}}, etc.)
- [ ] Templates editable via admin UI
- [ ] New templates can be added without code changes
- [ ] Keywords and negative keywords configured per template

---

## PHASE 2: Campaign Launch Workflow
**Goal:** Build the "3-step" campaign launch Ferris described: select trigger/template → review copy → go live.

### Issue 4.4: AI Ad Copy Generation
**Description:** Use an LLM (Claude API) to generate ad copy variants from campaign templates, customized for the specific scenario.
**Workflow:**
1. Template selected (manually or via weather trigger)
2. System sends prompt to Claude API:
   ```
   Generate 3 Google Ads copy variants for a {{service_line}} {{scenario}} campaign.
   Business: Beehive Pros, a trades service company in {{city}}, MA.
   Context: {{weather_context or manual_context}}
   Template headline: {{headline_template}}
   Requirements: headline max 30 chars, description max 90 chars, include phone CTA.
   ```
3. Claude returns 3 variants
4. Variants displayed for manager review
5. Manager selects preferred variant (or edits manually)
6. Selected copy saved to campaign draft

**Cost control:** Cache generated copy for identical template+context combinations. Average cost per generation: ~$0.01.

**Git Commit Message:** `feat(ai): LLM-powered ad copy generation with 3 variants per template`

**Acceptance Criteria:**
- [ ] Claude API integration works via Supabase Edge Function
- [ ] 3 copy variants generated per request
- [ ] Copy respects Google Ads character limits
- [ ] Manager can review, select, or edit variants
- [ ] API key stored in Supabase Vault
- [ ] Cached results prevent duplicate API calls

---

### Issue 4.5: One-Click Campaign Launcher UI
**Description:** The core UI that makes campaign launching a 3-step process instead of 10.
**User Flow:**
```
Step 1: SELECT
  - Choose: service line (plumbing/hvac/electrical)
  - Choose: scenario (emergency/seasonal/promotional)
  - OR: select from triggered campaigns waiting for review
  → System auto-selects matching template

Step 2: REVIEW
  - See generated ad copy (3 variants to choose from)
  - See targeting: geo area on map, radius, zip codes
  - See budget: daily spend, duration, total max spend
  - Edit any field if needed

Step 3: LAUNCH
  - Click "Launch Campaign"
  - System creates campaign via Google Ads API
  - Confirmation screen with campaign ID and estimated reach
  - Campaign appears in active campaigns list
```

**Additional Features:**
- "Quick Launch" button on dashboard for triggered campaigns (skips Step 1)
- Campaign status badges: Draft → Active → Paused → Completed
- Panic button: "Pause All Campaigns" in case of runaway spend

**Git Commit Message:** `feat(ui): 3-step campaign launcher with template selection, copy review, and one-click launch`

**Acceptance Criteria:**
- [ ] Full 3-step flow works end to end
- [ ] Template auto-selected based on service + scenario
- [ ] Ad copy variants displayed for review
- [ ] Geo-targeting shown on map
- [ ] Budget clearly displayed with daily and total caps
- [ ] Campaign successfully created in Google Ads on launch
- [ ] "Pause All" panic button works

---

### Issue 4.6: Campaign Performance Dashboard
**Description:** Track and display performance metrics for all campaigns so Ferris and the marketing team can see ROI.
**Metrics per campaign:**
- Impressions
- Clicks
- Click-through rate (CTR)
- Phone calls received
- Cost per click (CPC)
- Cost per lead (phone call)
- Total spend vs. budget
- Status (active/paused/completed)

**Aggregate view:**
- Total marketing spend this month
- Total leads (calls) generated
- Average cost per lead
- Best performing campaign (by cost-per-lead)
- Worst performing campaign
- Spend by service line (pie chart)
- Leads trend over time (line chart, weekly)

**Data source:** Google Ads API metrics pulled daily via Supabase cron job.

**Git Commit Message:** `feat(ui): campaign performance dashboard with per-campaign and aggregate metrics`

**Acceptance Criteria:**
- [ ] Metrics pulled from Google Ads API daily
- [ ] Per-campaign metrics displayed correctly
- [ ] Aggregate view shows monthly totals
- [ ] Best/worst performing campaigns highlighted
- [ ] Spend vs budget clearly shown (progress bar)
- [ ] Historical data retained for trend analysis

---

## PHASE 3: Video Content Pipeline
**Goal:** Build the workflow for producing, managing, and deploying Beehive service videos using Go Happy.

### Issue 4.7: Video Content Management System
**Description:** A simple CMS for managing Beehive's video library - uploaded from Go Happy productions and organized for use in ads and training.
**Features:**
- Upload video files to Supabase Storage (or link from YouTube/Vimeo)
- Metadata per video: title, service line, scenario (emergency/educational/testimonial), duration, thumbnail
- Organize by: service line, content type, target audience (customers vs techs)
- Tag system for searchability
- Embed codes for Google Ads, website, social media

**Initial Video Library Plan (to produce with Go Happy):**
1. "About Beehive Pros" - company overview (60 sec)
2. "Emergency Plumbing Response" - dramatic cold-weather scenario (30 sec ad cut)
3. "HVAC Installation Process" - professional team at work (60 sec)
4. "Electrical Safety Inspection" - service walkthrough (60 sec)
5. "Customer Testimonial - Commercial" - Bass Pro or Marriott manager (30 sec)
6. "Customer Testimonial - Residential" - Martha's Vineyard homeowner (30 sec)
7. "Why Choose Beehive" - value proposition (30 sec ad cut)
8. "Meet Our Technicians" - team profiles (60 sec)

**Git Commit Message:** `feat(video): video content management system with upload, metadata, and organization`

**Acceptance Criteria:**
- [ ] Videos upload and stream from Supabase Storage
- [ ] Metadata fields all editable
- [ ] Tag and filter system works
- [ ] Embed codes generated for each video
- [ ] Thumbnail auto-generated or manually uploadable

---

### Issue 4.8: AI Video Versioning for Ad Variants
**Description:** Take master videos from Go Happy and generate variants (different intros, different city names, different CTAs) using AI tools.
**Approach:**
- Use text overlay + audio swap to create geo-targeted variants from master videos
- Example: Master "Emergency Plumbing" video → variants for "Boston", "Marlboro", "Southborough", "Martha's Vineyard"
- Text overlay: city name in intro and CTA
- This is simpler than full AI video generation - just templated overlays on existing footage

**Implementation:** Use FFmpeg (via Edge Function or local processing) for:
- Adding text overlays (city name, phone number)
- Trimming to 15/30/60 second cuts for different ad placements
- Generating thumbnails at key frames

**Git Commit Message:** `feat(video): automated video versioning with geo-targeted text overlays via FFmpeg`

**Acceptance Criteria:**
- [ ] Master video can generate city-specific variants
- [ ] Text overlay clean and professional (proper font, positioning)
- [ ] 15, 30, and 60 second cuts generated automatically
- [ ] Thumbnails generated at key frames
- [ ] Variants linked to campaign templates for easy ad creation

---

## PHASE 4: Technician Training Module
**Goal:** Build or integrate the training system for Beehive technicians.

### Issue 4.9: Training Platform Decision & Setup
**Description:** Before building anything, check if Service Titan (which Beehive already uses) has built-in training features. If yes, use it. If no, build a lightweight LMS on Supabase.
**Research Tasks:**
1. Check Service Titan's training/learning features
2. Check if there are industry-standard HVAC/plumbing/electrical training platforms (Ferris mentioned "training modules in Tennessee" - likely Interplay Learning or similar)
3. Cost comparison: existing platform subscription vs custom build

**If external platform exists and is affordable (<$50/user/mo):**
- Recommend subscribing. Do NOT build custom.
- Build a lightweight integration: link from Beehive dashboard to training platform, pull completion status via API if available.

**If no suitable platform or too expensive:**
- Build lightweight LMS on Supabase (reuse onboarding video/quiz pattern from Project 2, Issues 2.8-2.9)
- Modules: trade-specific technical training + customer service/upsell training

**Git Commit Message:** `docs(training): training platform evaluation and recommendation`

**Acceptance Criteria:**
- [ ] Service Titan training features documented (available or not)
- [ ] At least 2 industry training platforms evaluated with pricing
- [ ] Clear recommendation: build vs buy
- [ ] If buy: specific platform and onboarding plan
- [ ] If build: scope document for custom LMS

---

### Issue 4.10: Upsell Training Content & Assessment
**Description:** Whether using an external platform or custom LMS, Beehive needs custom content for training technicians on identifying upsell opportunities.
**Training Module: "Solution-Oriented Service"**
Curriculum:
1. **Identifying Upsell Opportunities** (video + quiz)
   - "Your water heater is 15 years old" → recommend replacement quote
   - "Your electrical panel is outdated" → recommend upgrade quote
   - "Your HVAC filter hasn't been changed in a year" → recommend maintenance plan
2. **Customer Communication Scripts** (video + role-play scenarios)
   - How to present an upsell without being pushy
   - How to explain cost savings of proactive replacement vs emergency failure
   - How to generate a follow-up quote on-site using Service Titan
3. **Pricing Confidence** (video + quiz)
   - Understanding Beehive's pricing vs market rates (reference the water heater story: Beehive at $20K vs market at $35-50K)
   - How to respond to "that seems high" objections
   - When to escalate to Kevin Puquette or sales team

**Content Production:** Script these modules, have Go Happy produce the videos, host on the training platform.

**Git Commit Message:** `feat(training): upsell training curriculum with 3 modules, scripts, and quiz content`

**Acceptance Criteria:**
- [ ] 3 training modules scripted with learning objectives
- [ ] Quiz questions written for each module (10 questions each, 80% passing)
- [ ] Video production brief ready for Go Happy
- [ ] Completion tracking integrated with Beehive dashboard
- [ ] Technician training status visible to Kevin Puquette (ops manager)

---

## PHASE 5: Deployment & Integration
**Goal:** Deploy everything, connect the marketing engine to the rest of the Ferris ecosystem, and hand off to the team.

### Issue 4.11: Production Deployment & Campaign Dry Run
**Description:** Deploy the marketing engine to production and run a complete dry run before going live with real ad spend.
**Steps:**
1. Deploy to Vercel (shared infrastructure)
2. Connect production Google Ads account
3. Set up weather monitoring for Beehive service area
4. Run a full dry run:
   - Simulate a weather trigger
   - Generate ad copy variants
   - Review and "launch" a test campaign (with $0 budget or test mode)
   - Verify metrics pipeline pulls data correctly
5. Go live with first real campaign:
   - Start conservative: $50/day budget
   - Monitor for 1 week
   - Review performance with Ferris and adjust

**Git Commit Message:** `chore(deploy): marketing engine production deployment with campaign dry run`

**Acceptance Criteria:**
- [ ] All components deployed and functional in production
- [ ] Weather monitoring running and triggers configured
- [ ] Dry run completed successfully
- [ ] First real campaign launched with conservative budget
- [ ] Performance data flowing into dashboard
- [ ] Ferris and marketing team can operate without developer assistance

---

## TOTAL ISSUES: 11
## ESTIMATED PLATFORM COST: $25-65/mo (hosting + AI API)
## ESTIMATED AD SPEND: $1,000-5,000/mo (Beehive's marketing budget, controlled by them)
## ESTIMATED VIDEO PRODUCTION: $2,000-5,000 one-time (Go Happy)
## ESTIMATED BUILD TIME: 5-6 weeks (1 developer, Google Ads API approval may add 1 week lead time)
## CRITICAL DEPENDENCY: Google Ads API developer token approval (3-7 business days)
