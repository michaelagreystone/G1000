# PROJECT 2: Labor Productivity Monitoring (AI Camera System)

**Client Entity:** Beehive + Expedited Construction (trades/construction workforce)
**Priority:** #1 per David Ferris - shortest payback window of any investment
**Stack:** Supabase (Database, Auth, Storage, Edge Functions) + React frontend + third-party camera hardware + ML inference service
**Estimated Build Time:** 6-8 weeks across all phases

---

## BUSINESS CONTEXT (From David Ferris Interview)

Ferris spends approximately $75,000 per week on labor costs across construction and trades operations. By his own math, even a 20% productivity recovery justifies nearly any reasonable capital investment. That's $15,000/week or $780,000/year in recovered productivity.

The #1 productivity drain is phone use on job sites. One worker logged **171 minutes of phone use and 78 pickups in a single workday** - not an outlier but indicative of a broader pattern.

**Current tools (workarounds, not systems):**
- WorkYard GPS app for clock-ins (already saved significant costs catching time theft)
- $100/week bonus for safety compliance + no phone use during work hours
- Kenny, a site supervisor who walks floors and pushes people physically

**What Ferris wants:** "Airport-style sophisticated cameras with AI software. At the end of the day it's going to say, Kyle picked up his phone, was on his phone for 171 minutes and picked it up 78 times. It's coming right off your pay."

**He wants the output formatted like his Verizon fleet tracking app** - a clean weekly report per worker.

---

## FEASIBILITY ASSESSMENT

### Critical Decision: Build vs. Buy the Camera AI

**RECOMMENDATION: Hybrid approach - Buy cameras, buy ML inference, build the dashboard/reporting layer.**

| Component | Build or Buy | Why |
|-----------|-------------|-----|
| Camera hardware | **Buy** | Commercial PoE IP cameras ($100-300 each). Brands: Reolink, Hikvision, Axis. No reason to build hardware. |
| Video storage | **Buy** | Camera NVR (Network Video Recorder) or cloud storage. Local NVR is cheaper and keeps footage on-site. |
| Phone detection ML | **Buy/Integrate** | Use a pre-trained object detection model (YOLOv8 or similar) fine-tuned for "person holding phone" detection. Running inference on-premise with a small GPU box ($500-1000) avoids per-frame cloud costs. |
| Worker identification | **Build** | Zone-based identification (camera X covers area Y where Worker Z is assigned). Badge/vest color coding. Full facial recognition is expensive, legally risky, and unnecessary. |
| Weekly report generation | **Build** | Custom to Ferris's exact requirements. This is the dashboard they'll interact with daily. |
| Dashboard & admin | **Build on Supabase** | Same stack as Project 1 for consistency. Shared auth across all Ferris tools. |

### Security Considerations
- **Video footage is sensitive.** Store on-premise on the NVR, NOT in the cloud. Only aggregated metrics (phone usage minutes, pickup count) are stored in Supabase.
- **No facial recognition.** Worker identification is by assigned zone/camera, not biometrics. This avoids Massachusetts biometric data laws (MA has no BIPA equivalent yet, but it's coming).
- **Employee consent.** Terms and conditions of employment must include consent to camera monitoring on job sites. This is standard in construction. Ferris already mentioned this goes into the pre-hire video/testing module.
- **Data retention.** Raw video retained 30 days on NVR, then auto-deleted. Aggregated metrics retained indefinitely in Supabase for trend analysis.
- **Access control.** Only Ferris (super_admin), site managers, and HR can view individual worker reports. Workers can see their own data only.

### Cost Estimate
| Item | One-Time Cost | Monthly Cost |
|------|--------------|--------------|
| 8x PoE IP cameras (Reolink RLC-810A) | $1,200 | $0 |
| 1x NVR (Reolink 16ch) | $300 | $0 |
| 1x GPU inference box (Intel NUC + Hailo-8 AI accelerator or Jetson Orin Nano) | $500-800 | $0 (electricity ~$10/mo) |
| Network switch + cabling per site | $200 | $0 |
| Supabase (shared instance from Project 1) | $0 | $0-25 |
| Twilio SMS for weekly reports | $0 | $15-30 |
| **Total per site** | **$2,200-2,500** | **$25-65/mo** |
| **Total for 3 active job sites** | **$6,600-7,500** | **$75-195/mo** |

**Ferris estimated $10-20K.** This comes in well under that at $7-8K for 3 sites with room for expansion.

**ROI:** At $75K/week labor spend, a 10% productivity improvement = $7,500/week = $390,000/year. The system pays for itself in the first week.

### Alternative Approaches Considered & Rejected
| Option | Why Rejected |
|--------|-------------|
| Cloud-based video analytics (AWS Rekognition, Google Vision) | $0.001-0.01 per frame. At 30fps across 8 cameras, that's 14.4M frames/day = $14K-144K/day. Absurdly expensive. On-premise inference is the only viable path. |
| Full SaaS construction monitoring (Smartvid.io, Vinnie, OpenSpace) | $500-2000/mo per site. Designed for safety compliance, not phone-use tracking. Doesn't produce the specific report format Ferris wants. |
| Manual review of camera footage | Defeats the purpose. Ferris already has Kenny walking floors. The value is AUTOMATED detection and reporting. |
| Wearable devices / phone lockbox | Workers would revolt. Cameras are passive and less invasive than physically confiscating phones. |

---

## PHASE 1: Infrastructure & Hardware Setup
**Goal:** Get cameras installed, recording, and streaming to a local processing box at one job site as a proof of concept.

### Issue 2.1: Hardware Procurement & Network Design Document
**Description:** Research, specify, and document the exact hardware needed for the camera system. This is a planning/procurement issue, not a code issue.
**Deliverables:**
1. **Camera selection:** Specific model, resolution (minimum 1080p for phone detection at 15-20ft), PoE support, weather rating (IP67 for outdoor construction sites), night vision capability
2. **NVR selection:** Channel count, storage capacity (calculate: 8 cameras x 1080p x 12hrs/day x 30 days retention), ONVIF compatibility
3. **ML inference hardware:** Specify the edge compute device. Options:
   - NVIDIA Jetson Orin Nano ($500) - 40 TOPS, runs YOLOv8 easily
   - Intel NUC + Hailo-8 M.2 ($400+200) - 26 TOPS, lower power consumption
   - Recommendation: Jetson Orin Nano for better ML ecosystem support
4. **Network diagram:** Camera -> PoE Switch -> NVR (recording) + Inference Box (analysis) -> Supabase (metrics only)
5. **Site survey checklist:** Power availability, WiFi/cellular for metrics upload, mounting locations, camera angles for optimal coverage

**Git Commit Message:** `docs(hardware): camera system hardware spec, network design, and site survey checklist`

**Acceptance Criteria:**
- [ ] Specific model numbers and prices for all hardware
- [ ] Network diagram showing data flow from camera to cloud
- [ ] Storage calculation proving 30-day retention fits NVR capacity
- [ ] Site survey checklist ready for use at first job site
- [ ] Total cost per site documented

---

### Issue 2.2: Camera Installation & NVR Configuration at Pilot Site
**Description:** Physical installation of cameras and NVR at the first job site (recommend: the $45M Chelmsford drug recovery center where Ferris does daily 6am walks).
**Steps:**
1. Mount 8 cameras at key work zones (follow site survey from 2.1)
2. Run PoE cables to central switch
3. Connect NVR and configure recording schedule (6am-4pm weekdays, matching work hours)
4. Verify all 8 feeds are recording and accessible on local network
5. Connect inference box to same network switch
6. Verify inference box can pull RTSP streams from cameras

**This is a physical/IT issue, not a software issue.** May require a low-voltage electrician for cable runs.

**Git Commit Message:** `chore(infra): pilot site camera installation and NVR configuration`

**Acceptance Criteria:**
- [ ] All 8 cameras recording clear 1080p footage
- [ ] NVR accessible on local network
- [ ] Inference box can pull all 8 RTSP streams
- [ ] Recording schedule matches work hours
- [ ] Night vision functional for early morning (6am) winter starts

---

## PHASE 2: ML Pipeline - Phone Detection
**Goal:** Build the software that watches camera feeds and detects when workers are holding/using phones.

### Issue 2.3: YOLOv8 Phone Detection Model Setup
**Description:** Set up the ML inference pipeline on the Jetson Orin Nano to detect "person holding cell phone" events from camera feeds.
**Approach:**
1. Use YOLOv8 pre-trained on COCO dataset (already detects "cell phone" as class 67)
2. Fine-tune with construction-specific images if detection accuracy is below 85% (open datasets: COCO, Open Images V7 both have phone-in-hand annotations)
3. Optimize model for Jetson using TensorRT for real-time inference
4. Process each camera at 1 frame per 5 seconds (not 30fps - we don't need real-time video, just periodic sampling). This reduces compute load by 150x.

**Detection Logic:**
- For each frame: run YOLOv8 → detect persons + cell phones → if phone bounding box overlaps with person bounding box within threshold → flag as "phone event"
- Debounce: if phone detected in consecutive frames (3+ in a row = 15 seconds), count as 1 "phone usage session"
- Session ends when 2+ consecutive frames show no phone for that person/zone

**Git Commit Message:** `feat(ml): YOLOv8 phone detection pipeline on Jetson with TensorRT optimization`

**Acceptance Criteria:**
- [ ] YOLOv8 running on Jetson at 1 frame/5sec across 8 cameras
- [ ] Phone detection accuracy >80% on test footage
- [ ] False positive rate <15% (e.g., not flagging a worker holding a walkie-talkie)
- [ ] Detection events logged locally with timestamp, camera_id, confidence score
- [ ] Debounce logic correctly groups consecutive detections into sessions

---

### Issue 2.4: Worker Zone Mapping & Identification System
**Description:** Map cameras to physical work zones and associate workers with zones for the shift, so phone events can be attributed to specific workers.
**Approach (NO facial recognition):**
1. Create a `job_sites` table in Supabase with site name, address, active status
2. Create a `cameras` table: camera_id, job_site_id, zone_name (e.g., "Floor 2 West Wing"), rtsp_url
3. Create a `shift_assignments` table: worker_id, camera_zone_id, date, shift_start, shift_end
4. Site managers log shift assignments each morning via a simple form: "Today, Kyle is in Zone 3 (cameras 5,6), James is in Zone 1 (cameras 1,2)"
5. Phone events from camera 5 during Kyle's shift → attributed to Kyle

**Why this works for construction:** Workers are generally assigned to specific areas/floors for the day. Unlike an office, they don't wander between zones frequently.

**Edge case handling:**
- If a zone has 2+ workers, phone events are flagged as "Zone 3 - unattributed" and a manager can manually assign after reviewing a snapshot
- Break periods (9:00-9:15, 12:00-12:30) are excluded from phone usage calculations automatically

**Git Commit Message:** `feat(zones): worker zone mapping with shift assignment and break exclusion`

**Acceptance Criteria:**
- [ ] Job sites and cameras configurable in Supabase
- [ ] Shift assignment form works on mobile (managers are on-site, not at desks)
- [ ] Phone events correctly attributed to assigned worker
- [ ] Multi-worker zones flagged for manual review
- [ ] Break periods excluded from metrics

---

### Issue 2.5: Event Aggregation & Metrics Storage
**Description:** Aggregate raw phone detection events into daily and weekly metrics per worker, stored in Supabase for dashboard consumption.
**Data Flow:**
1. Inference box logs raw events locally (SQLite or flat file)
2. Every hour, an aggregation script runs on the inference box:
   - Groups phone sessions by worker
   - Calculates: total_minutes, pickup_count, longest_session_minutes
   - Uploads aggregated hourly metrics to Supabase via Edge Function
3. Why hourly (not real-time): minimizes network usage on construction sites with spotty WiFi, and raw events stay on-premise for privacy.

**Supabase Schema:**
```sql
CREATE TABLE phone_usage_metrics (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  worker_id UUID REFERENCES profiles(id) NOT NULL,
  job_site_id UUID REFERENCES job_sites(id) NOT NULL,
  date DATE NOT NULL,
  hour_bucket INT CHECK (hour_bucket BETWEEN 0 AND 23),
  total_phone_minutes NUMERIC(6,1) NOT NULL,
  pickup_count INT NOT NULL,
  longest_session_minutes NUMERIC(5,1),
  work_minutes_in_bucket NUMERIC(5,1) NOT NULL, -- excludes breaks
  created_at TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE(worker_id, job_site_id, date, hour_bucket)
);
```

**RLS Policies:**
- Workers can read their own metrics
- Site managers can read metrics for their site
- Ferris/admins can read all metrics

**Git Commit Message:** `feat(metrics): hourly phone usage aggregation pipeline from edge to Supabase`

**Acceptance Criteria:**
- [ ] Hourly aggregation runs reliably on inference box
- [ ] Data uploads to Supabase without duplicates (UPSERT on unique constraint)
- [ ] Break periods correctly excluded from work_minutes_in_bucket
- [ ] RLS enforces access control on metrics
- [ ] Metrics survive inference box restart (local queue for failed uploads)

---

## PHASE 3: Reporting Dashboard
**Goal:** Build the weekly productivity report and dashboard that Ferris will actually look at.

### Issue 2.6: Weekly Productivity Report Generator
**Description:** Generate the automated weekly report Ferris described - formatted like his Verizon driving app. One report per worker, one summary report per site.
**Per-Worker Report:**
- Worker name and site assignment
- Total phone usage minutes (Mon-Fri)
- Total pickup count
- Daily breakdown (bar chart: minutes per day)
- Comparison to site average ("Kyle: 171 min | Site Average: 43 min")
- Trend: this week vs. last week (arrow up/down + percentage)
- Status badge: Green (<30 min/week), Yellow (30-60 min), Red (>60 min)

**Per-Site Summary Report:**
- Ranked list of all workers by phone usage (worst offenders at top)
- Site-wide average phone usage
- Total estimated productivity loss in dollars ($X based on hourly rates)
- Week-over-week trend for the whole site

**Output Format:** PDF generated via a Supabase Edge Function using a PDF library (e.g., jsPDF or Puppeteer for HTML-to-PDF). Stored in Supabase Storage.

**Delivery:** Every Monday at 6am, email the site summary to Ferris + site managers. Individual reports accessible via dashboard.

**Git Commit Message:** `feat(reports): weekly productivity PDF with per-worker and per-site views`

**Acceptance Criteria:**
- [ ] Per-worker report generates correctly with all fields
- [ ] Per-site summary ranks workers correctly
- [ ] Dollar estimate uses actual hourly rate from worker profile
- [ ] Week-over-week comparison is accurate
- [ ] PDF is clean, professional, and readable on mobile
- [ ] Monday 6am delivery works via Supabase cron + Resend email

---

### Issue 2.7: Productivity Dashboard (Web UI)
**Description:** Web dashboard for real-time and historical phone usage data. This is the interactive companion to the weekly PDF.
**Views:**
1. **Site Overview:** All sites on a map or list. Click a site to see its workers.
2. **Site Detail:** All workers at a site, ranked by phone usage this week. Color-coded badges.
3. **Worker Detail:** Full history for one worker - daily/weekly/monthly charts. Drill down to hourly breakdown.
4. **Trend Analysis:** Site-wide phone usage over time (line chart, weekly granularity, last 12 weeks).

**Realtime:** Not needed here (hourly data). Simple polling or Supabase subscription on metrics table.

**Access Control:**
- Workers see only their own Worker Detail page
- Site managers see their site's Overview and all workers at their site
- Ferris sees everything

**Git Commit Message:** `feat(ui): productivity dashboard with site, worker, and trend views`

**Acceptance Criteria:**
- [ ] Site overview loads all active sites
- [ ] Worker ranking updates when new hourly data arrives
- [ ] Charts render correctly (use Recharts or Chart.js)
- [ ] Access control enforced - workers cannot see other workers' data
- [ ] Mobile responsive (managers check this on-site from phones)

---

## PHASE 4: Pre-Hire Onboarding Module
**Goal:** Build the mandatory pre-hire video/testing module Ferris described as the "guaranteed not to last at Ferris Companies" orientation.

### Issue 2.8: Onboarding Video Hosting & Playback System
**Description:** A system where new hires watch mandatory orientation videos before they're allowed on job sites.
**Requirements:**
- Video stored in Supabase Storage (or linked from a private YouTube/Vimeo for bandwidth)
- Playback tracking: system knows if the video was watched to completion (not just opened)
- Multiple videos possible: general orientation, trade-specific (electrical safety, plumbing protocols, HVAC handling)
- Anti-skip: cannot fast-forward past unwatched sections (simple JS player control)

**Content (Ferris to produce with Go Happy downstairs):**
- "What we expect at Ferris Companies" (phone policy, break schedule, accountability)
- "Your first 120 days" (the laborer-to-apprentice path Ferris described)
- Safety requirements (PPE, site rules)
- Trade-specific modules as needed

**Git Commit Message:** `feat(onboarding): video hosting with playback tracking and anti-skip`

**Acceptance Criteria:**
- [ ] Videos upload to Supabase Storage (or linked from external host)
- [ ] Playback tracked per user - system knows exact watch progress
- [ ] Cannot skip ahead past unwatched portions
- [ ] Works on mobile (new hires will watch on phones)
- [ ] Admin can add/remove/reorder videos

---

### Issue 2.9: Post-Video Quiz & Certification System
**Description:** After watching each video, the new hire must pass a quiz before being cleared for field work.
**Requirements:**
- Multiple choice questions tied to each video
- Minimum passing score: 80% (configurable by admin)
- Failed attempts logged - new hire can retry after 24 hours
- Upon passing all required quizzes: system marks the hire as "Field Cleared" in their profile
- Managers can see which new hires have completed onboarding and which haven't

**Supabase Schema:**
```sql
CREATE TABLE onboarding_quizzes (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  video_id UUID REFERENCES onboarding_videos(id),
  title TEXT NOT NULL,
  passing_score INT DEFAULT 80
);

CREATE TABLE quiz_questions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  quiz_id UUID REFERENCES onboarding_quizzes(id),
  question_text TEXT NOT NULL,
  options JSONB NOT NULL, -- ["Option A", "Option B", "Option C", "Option D"]
  correct_option INT NOT NULL -- 0-indexed
);

CREATE TABLE quiz_attempts (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES auth.users(id),
  quiz_id UUID REFERENCES onboarding_quizzes(id),
  score INT NOT NULL,
  passed BOOLEAN NOT NULL,
  answers JSONB NOT NULL, -- record of what they selected
  attempted_at TIMESTAMPTZ DEFAULT NOW()
);
```

**Admin View:**
- Table of all new hires showing: name, hire date, videos watched (X/Y), quizzes passed (X/Y), field cleared (yes/no)
- Filter by: entity (Beehive, Expedited Construction), cleared status, hire date range

**Git Commit Message:** `feat(onboarding): quiz system with scoring, retry logic, and field clearance`

**Acceptance Criteria:**
- [ ] Quizzes render correctly with multiple choice options
- [ ] Score calculated and pass/fail determined
- [ ] Failed users cannot retry for 24 hours
- [ ] Passing all quizzes sets "field_cleared" flag on profile
- [ ] Admin view shows onboarding status for all new hires
- [ ] Managers cannot deploy a worker who hasn't been cleared

---

### Issue 2.10: Onboarding Integration with Shift Assignment
**Description:** Connect the onboarding system to the shift assignment system from Issue 2.4 so that uncleared workers cannot be assigned to shifts.
**Logic:**
- When a manager tries to assign a worker to a shift zone, the system checks `field_cleared` status
- If not cleared: assignment is blocked with message "This worker has not completed onboarding. X of Y videos watched, X of Y quizzes passed."
- If cleared: assignment proceeds normally

**Git Commit Message:** `feat(onboarding): block shift assignment for workers who haven't completed onboarding`

**Acceptance Criteria:**
- [ ] Shift assignment form checks field_cleared status
- [ ] Blocked assignment shows specific progress (what's missing)
- [ ] Cleared workers can be assigned without friction
- [ ] Admin can override block in emergency (logged in activity)

---

## PHASE 5: Deployment & Rollout
**Goal:** Deploy to production and roll out to the first job site.

### Issue 2.11: Production Deployment & Pilot Site Go-Live
**Description:** Deploy the full system to production and run a 2-week pilot at the Chelmsford site.
**Steps:**
1. Inference box configured and running at pilot site
2. Dashboard deployed to Vercel (shared Supabase instance from Project 1)
3. 3-5 workers enrolled for pilot (with their knowledge - transparent, not surveillance)
4. Daily check: verify detection accuracy, check for false positives
5. First weekly report generated and reviewed with Ferris
6. Adjust detection thresholds based on pilot feedback
7. After 2 weeks: decision to expand to remaining sites or iterate

**Git Commit Message:** `chore(deploy): production deployment and Chelmsford pilot site go-live`

**Acceptance Criteria:**
- [ ] System running unattended for 5+ consecutive workdays
- [ ] Weekly report generated and delivered on Monday
- [ ] Ferris reviews report and confirms format matches expectations
- [ ] Detection accuracy >80% confirmed on real job-site footage
- [ ] No privacy complaints from pilot workers (transparent consent)

---

## TOTAL ISSUES: 11
## ESTIMATED HARDWARE COST: $7,000-8,000 (3 sites)
## ESTIMATED MONTHLY COST: $75-195/mo (hosting, SMS, electricity)
## ESTIMATED BUILD TIME: 6-8 weeks (1 developer, hardware procurement may add 1-2 weeks lead time)
## ESTIMATED ANNUAL ROI: $390,000+ (10% productivity recovery on $75K/week labor spend)
