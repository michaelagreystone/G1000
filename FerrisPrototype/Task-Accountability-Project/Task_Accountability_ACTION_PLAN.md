# PROJECT 1: Task Accountability System

**Client Entity:** Ferris Development Group (Holding Company - serves ALL entities)
**Priority:** Foundation layer - enables accountability across Ferris Dev, Beehive, Expedited Construction, Expedited Engineering
**Stack:** Supabase (Auth, Database, Edge Functions, Realtime) + Next.js or React frontend
**Estimated Build Time:** 3-4 weeks across all phases

---

## BUSINESS CONTEXT (From David Ferris Interview)

David Ferris told his team 6-7 times over 2 months to mark two-thirds of coworking pods as "Reserved" to manufacture scarcity and drive tenant urgency. It never happened. Not because anyone refused - because no one owned it, no deadline existed, and no system tracked it.

Ferris makes fewer than 50 decisions per day intentionally, pushing authority downward. But the gap between delegating a task and confirming execution is filled only by him personally showing up at 6am to walk job sites. That does not scale at 60 people across 4 companies and 8 active projects.

**His exact words:** "The worst thing a company at our size can handle is any project or deliverable without a deadline. Without deadlines, you're a dying company."

**His vision:** A shared dashboard visible to the team where every verbal directive becomes a timestamped, assigned deliverable with an owner and due date before the conversation ends.

---

## FEASIBILITY ASSESSMENT

### Why Supabase is the Right Choice
- **Row Level Security (RLS):** Critical - Ferris has 4 separate entities with different personnel. RLS ensures employees only see tasks for their entity unless granted cross-entity access.
- **Realtime subscriptions:** Dashboard updates live when tasks are created/completed - no refresh needed.
- **Auth:** Supabase Auth with email/password is sufficient. No need for SSO at 60 employees.
- **Edge Functions:** Lightweight serverless for notifications (email/SMS alerts for overdue tasks).
- **Cost:** Free tier supports up to 500MB database, 50K monthly active users, 500K Edge Function invocations. This project will never exceed free tier for a 60-person company.

### Security Considerations
- All data in Supabase is encrypted at rest (AES-256) and in transit (TLS 1.2+).
- RLS policies enforce entity-level isolation at the database layer - not the application layer.
- No sensitive PII beyond employee names and email addresses.
- Supabase is SOC2 Type II compliant.

### Cost Estimate
| Item | Cost |
|------|------|
| Supabase Free Tier | $0/mo |
| Domain (optional) | $12/yr |
| Vercel Free Tier (hosting) | $0/mo |
| **Total** | **$0-1/mo** |

If they outgrow free tier: Supabase Pro is $25/mo, Vercel Pro is $20/mo = $45/mo total.

### Alternative Approaches Considered & Rejected
| Option | Why Rejected |
|--------|-------------|
| Monday.com / Asana / ClickUp | $8-20/user/mo = $480-1200/mo for 60 users. No customization for Ferris's specific 4-entity structure. Cannot enforce the exact workflow Ferris described. |
| Notion | Not designed for task tracking with deadlines and escalation. No native alerting. |
| Custom Rails/Django | Overkill. Supabase + React gives the same result with 1/10th the code and built-in auth, realtime, and hosting. |
| Airtable | $20/user/mo = $1200/mo. Limited RLS. No realtime. |

**Recommendation:** Build custom on Supabase. The 4-entity structure, escalation logic, and dashboard requirements are specific enough that off-the-shelf tools would require heavy workarounds. Custom build is both cheaper and more precise.

---

## PHASE 1: Database Foundation & Auth
**Goal:** Establish the data model, authentication, and entity isolation so every subsequent phase builds on a secure, correct foundation.

### Issue 1.1: Supabase Project Setup & Auth Configuration
**Description:** Create the Supabase project, configure authentication, and set up the organizational structure.
**Exact Steps:**
1. Create Supabase project named `ferris-task-system`
2. Enable email/password auth provider
3. Create `organizations` table with the 4 entities:
   - Ferris Development Group
   - Beehive
   - Expedited Construction
   - Expedited Engineering
4. Create `profiles` table extending `auth.users` with fields: `full_name`, `role` (admin/manager/member), `organization_id` (FK to organizations), `phone` (for SMS alerts)
5. Create `user_organizations` junction table for users who span multiple entities (e.g., Ferris himself, Brian Charville)
6. Write RLS policies:
   - Users can only read profiles within their organization(s)
   - Only admins can create/update profiles
   - Ferris (super_admin role) can see all organizations
7. Seed the database with the 4 organizations

**Git Commit Message:** `feat(auth): Supabase project setup with org structure, profiles, and RLS policies`

**Acceptance Criteria:**
- [ ] Supabase project live with auth enabled
- [ ] 4 organizations seeded
- [ ] Profiles table with role-based access
- [ ] RLS policies tested - member of Beehive cannot see Expedited Engineering profiles
- [ ] Super admin can see all orgs

---

### Issue 1.2: Tasks Data Model & Core Schema
**Description:** Create the tasks table with all fields needed to convert a verbal directive into a tracked, assigned deliverable.
**Exact Schema:**
```sql
CREATE TABLE tasks (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  title TEXT NOT NULL,
  description TEXT,
  organization_id UUID REFERENCES organizations(id) NOT NULL,
  created_by UUID REFERENCES auth.users(id) NOT NULL,
  assigned_to UUID REFERENCES auth.users(id),
  status TEXT CHECK (status IN ('open', 'in_progress', 'completed', 'overdue', 'escalated')) DEFAULT 'open',
  priority TEXT CHECK (priority IN ('low', 'medium', 'high', 'critical')) DEFAULT 'medium',
  deadline TIMESTAMPTZ NOT NULL,
  completed_at TIMESTAMPTZ,
  source TEXT, -- 'verbal', 'email', 'meeting', 'text'
  source_context TEXT, -- optional note about where directive came from
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);
```
**RLS Policies:**
- Users can read tasks for their organization(s)
- Users can update tasks assigned to them (status, completed_at only)
- Managers/admins can create, update, delete tasks for their org
- Super admin (Ferris) has full CRUD across all orgs

**Indexes:**
- `idx_tasks_org_status` on (organization_id, status) for dashboard queries
- `idx_tasks_assigned_deadline` on (assigned_to, deadline) for "my tasks" view
- `idx_tasks_overdue` on (status, deadline) WHERE status NOT IN ('completed') for overdue cron

**Git Commit Message:** `feat(db): tasks table with RLS, indexes, and status workflow`

**Acceptance Criteria:**
- [ ] Tasks table created with all constraints
- [ ] RLS policies enforce org isolation
- [ ] Beehive manager can create task for Beehive employee
- [ ] Ferris can create task for any entity
- [ ] Member cannot create tasks (only managers/admins)

---

### Issue 1.3: Task Activity Log (Audit Trail)
**Description:** Every action on a task must be logged for accountability. Ferris needs to see WHEN a task was assigned, WHEN it was acknowledged, and WHEN it was completed or escalated.
**Schema:**
```sql
CREATE TABLE task_activity (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  task_id UUID REFERENCES tasks(id) ON DELETE CASCADE NOT NULL,
  actor_id UUID REFERENCES auth.users(id) NOT NULL,
  action TEXT NOT NULL, -- 'created', 'assigned', 'status_changed', 'deadline_changed', 'commented', 'escalated'
  old_value TEXT,
  new_value TEXT,
  note TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW()
);
```
**Database Trigger:** Create a PostgreSQL trigger on the `tasks` table that automatically inserts into `task_activity` on INSERT and UPDATE, capturing the old and new values for status and assigned_to changes.

**Git Commit Message:** `feat(db): task activity log with auto-trigger for audit trail`

**Acceptance Criteria:**
- [ ] Activity log table created
- [ ] Trigger fires on task creation (logs 'created')
- [ ] Trigger fires on status change (logs old -> new status)
- [ ] Trigger fires on reassignment (logs old -> new assignee)
- [ ] RLS: users can read activity for tasks in their org

---

## PHASE 2: Core API & Task Management
**Goal:** Build the backend logic for creating, assigning, updating, and querying tasks. This is the engine behind the dashboard.

### Issue 2.1: Task CRUD Edge Functions
**Description:** Create Supabase Edge Functions (or use the Supabase JS client directly) for all task operations.
**Endpoints (via Supabase client, not separate API):**
- **Create task:** Insert into `tasks` + validate deadline is in the future + auto-log to `task_activity`
- **Update task status:** Transition validation (open -> in_progress -> completed; any -> escalated)
- **Reassign task:** Update `assigned_to` + log activity
- **List tasks:** Filtered by org, status, assignee, overdue, priority with pagination
- **Get single task:** Full task details + activity log

**Validation Rules:**
- Deadline must be at least 1 hour in the future on creation
- Title is required, max 200 chars
- Only the assignee or a manager can mark a task as `in_progress`
- Only the assignee or a manager can mark a task as `completed`
- Completed tasks require `completed_at` timestamp

**Git Commit Message:** `feat(api): task CRUD operations with validation and activity logging`

**Acceptance Criteria:**
- [ ] Tasks can be created with all required fields
- [ ] Status transitions are enforced (cannot go from 'completed' back to 'open')
- [ ] Activity log entries created automatically for all mutations
- [ ] Pagination works on list endpoint
- [ ] Validation errors return clear messages

---

### Issue 2.2: Overdue Detection & Escalation Logic
**Description:** Build a Supabase Edge Function that runs on a cron schedule (via pg_cron or Supabase's built-in cron) to detect overdue tasks and escalate them.
**Logic:**
1. Every 15 minutes, query tasks WHERE `deadline < NOW()` AND `status NOT IN ('completed', 'escalated')`
2. Update status to `overdue`
3. Log activity: 'status_changed' from current status to 'overdue'
4. If a task has been `overdue` for 24+ hours with no activity, update status to `escalated`
5. Log activity: 'escalated'

**Why 15 minutes:** Ferris's operations are construction/trades - not real-time trading. 15-minute resolution catches things before the end of any workday.

**Git Commit Message:** `feat(cron): overdue detection and 24h escalation cron job`

**Acceptance Criteria:**
- [ ] Cron runs every 15 minutes
- [ ] Tasks past deadline are marked 'overdue' automatically
- [ ] Tasks overdue 24h+ with no activity are marked 'escalated'
- [ ] Activity log captures all automatic status changes
- [ ] Cron does NOT touch completed tasks

---

### Issue 2.3: Notification System (Email + SMS)
**Description:** Send notifications to task assignees and managers when critical events occur.
**Trigger Events:**
| Event | Who Gets Notified | Channel |
|-------|-------------------|---------|
| Task assigned to you | Assignee | Email + SMS |
| Task deadline in 2 hours | Assignee | SMS |
| Task marked overdue | Assignee + their manager | Email + SMS |
| Task escalated (24h overdue) | Assignee + manager + Ferris | Email + SMS |
| Task completed | Creator of the task | Email |

**Implementation:**
- Use Supabase Edge Functions triggered by database webhooks (on INSERT to task_activity)
- Email: Use Resend (free tier: 3,000 emails/mo - more than enough for 60 people)
- SMS: Use Twilio (pay-per-message, ~$0.0079/SMS - estimated $20-40/mo at scale)

**Security:** Store Resend and Twilio API keys in Supabase Vault (encrypted secrets), never in code.

**Git Commit Message:** `feat(notifications): email and SMS alerts for task lifecycle events`

**Acceptance Criteria:**
- [ ] Email sent on task assignment
- [ ] SMS sent on 2-hour deadline warning
- [ ] SMS + email sent on overdue detection
- [ ] Escalation notifies Ferris directly
- [ ] API keys stored in Supabase Vault
- [ ] No notifications for completed/closed tasks

---

## PHASE 3: Dashboard Frontend
**Goal:** Build the visual dashboard Ferris described - a shared screen where everyone sees what's assigned, what's overdue, and what's escalated.

### Issue 3.1: Project Scaffolding & Auth UI
**Description:** Set up the frontend application with authentication.
**Stack Decision:**
- **React + Vite** (faster builds, simpler config than Next.js for a dashboard app with no SEO needs)
- **Supabase JS client** for auth and data
- **Tailwind CSS** for styling (consistent, fast to build)
- **React Router** for navigation

**Pages to scaffold (empty shells):**
- `/login` - email/password login
- `/dashboard` - main task board
- `/tasks/new` - create task form
- `/tasks/:id` - task detail view
- `/admin` - user management (admin only)

**Auth Flow:**
1. User logs in with email/password
2. Supabase session stored in browser
3. Protected routes redirect to `/login` if no session
4. User's org membership loaded on login and stored in context

**Git Commit Message:** `feat(ui): React + Vite scaffold with Supabase auth and route protection`

**Acceptance Criteria:**
- [ ] Login page functional with Supabase Auth
- [ ] Protected routes redirect unauthenticated users
- [ ] User profile and org loaded into React context
- [ ] All page shells render without errors
- [ ] Tailwind configured and working

---

### Issue 3.2: Task Board Dashboard (Main View)
**Description:** The primary dashboard view - a Kanban-style board showing tasks by status across the user's organization(s).
**Layout:**
```
[Open] → [In Progress] → [Overdue] → [Escalated] → [Completed (last 7 days)]
```
**Each task card shows:**
- Title (truncated to 60 chars)
- Assigned to (avatar + name)
- Deadline (relative: "in 3 hours", "2 days overdue")
- Priority badge (color-coded: low=gray, medium=blue, high=orange, critical=red)
- Organization badge (for Ferris's cross-org view)

**Filtering:**
- By organization (dropdown - shows all orgs for Ferris, only user's org for others)
- By assignee
- By priority
- By date range

**Realtime:** Subscribe to Supabase Realtime on the `tasks` table so the board updates live when anyone creates/updates a task.

**Git Commit Message:** `feat(ui): Kanban task board with realtime updates, filtering, and priority badges`

**Acceptance Criteria:**
- [ ] Tasks display in correct status columns
- [ ] Cards show all required info (title, assignee, deadline, priority, org)
- [ ] Drag-and-drop moves tasks between statuses (with validation)
- [ ] Realtime: new task appears without page refresh
- [ ] Filters work independently and in combination
- [ ] Overdue tasks visually distinct (red border or background)

---

### Issue 3.3: Task Creation Form
**Description:** A form to create a new task - this is where "every verbal directive gets converted into a timestamped, assigned deliverable."
**Fields:**
- Title (required, text input)
- Description (optional, textarea)
- Organization (dropdown - auto-selected if user is in only 1 org)
- Assign to (dropdown of org members, searchable)
- Priority (radio: low/medium/high/critical, default medium)
- Deadline (date+time picker, must be future)
- Source (dropdown: verbal, email, meeting, text)
- Source context (optional, text - e.g., "Discussed in Thursday site walk")

**UX Requirements:**
- Form must be completable in under 30 seconds (Ferris's team won't use it if it's slow)
- After submit, redirect to dashboard with success toast
- Keyboard shortcuts: Ctrl+Enter to submit

**Git Commit Message:** `feat(ui): task creation form with validation and source tracking`

**Acceptance Criteria:**
- [ ] All fields render correctly
- [ ] Validation prevents past deadlines
- [ ] Assignee dropdown only shows members of selected org
- [ ] Form submits successfully and redirects to dashboard
- [ ] Activity log entry created automatically
- [ ] Notification sent to assignee on creation

---

### Issue 3.4: Task Detail View & Activity Timeline
**Description:** Clicking a task card opens a detail view showing full task info + the complete activity timeline.
**Layout:**
- Left side: Task details (title, description, status, priority, deadline, assignee, org)
- Right side: Activity timeline (chronological list of all events)
- Action buttons: Change status, Reassign, Edit deadline, Add comment

**Activity timeline entries show:**
- Timestamp
- Actor name
- Action description ("Michael assigned this to Kevin Puquette")
- Old/new values for changes

**Git Commit Message:** `feat(ui): task detail view with activity timeline and action buttons`

**Acceptance Criteria:**
- [ ] All task fields displayed
- [ ] Activity timeline shows full history
- [ ] Status can be changed via button (with transition validation)
- [ ] Reassignment works from detail view
- [ ] Comments can be added (stored in task_activity with action='commented')

---

### Issue 3.5: Admin Panel - User & Organization Management
**Description:** Admin-only panel for managing users, org membership, and roles.
**Features:**
- Invite user (sends email invite via Supabase Auth)
- Assign user to organization(s)
- Set user role (admin/manager/member)
- Deactivate user (soft delete - preserves task history)
- View all users across all orgs (super_admin only)

**Git Commit Message:** `feat(ui): admin panel for user management, roles, and org assignment`

**Acceptance Criteria:**
- [ ] Only admin/super_admin can access this page
- [ ] Users can be invited via email
- [ ] Org membership can be changed
- [ ] Roles can be changed
- [ ] Deactivated users cannot log in but their task history remains

---

## PHASE 4: Polish & Deployment
**Goal:** Make it production-ready, deploy, and onboard the team.

### Issue 4.1: Mobile Responsive Design
**Description:** Ferris and his managers are on job sites all day. The dashboard MUST work on phones.
**Requirements:**
- Task board collapses to single-column list view on mobile
- Task creation form works on phone keyboard
- Swipe gestures for status changes on mobile
- SMS notification links deep-link to the relevant task

**Git Commit Message:** `feat(ui): mobile responsive layout with touch interactions`

**Acceptance Criteria:**
- [ ] Dashboard usable on iPhone and Android
- [ ] Forms work with mobile keyboards
- [ ] No horizontal scrolling on any screen
- [ ] SMS links open correct task in mobile browser

---

### Issue 4.2: Dashboard Summary Stats
**Description:** Top-of-dashboard summary showing key metrics at a glance.
**Metrics:**
- Total open tasks (this week)
- Tasks overdue right now
- Tasks completed this week
- Average time from creation to completion (this month)
- Breakdown by organization (bar chart)

**Git Commit Message:** `feat(ui): dashboard summary stats with org breakdown`

**Acceptance Criteria:**
- [ ] All 5 metrics displayed at top of dashboard
- [ ] Numbers update in realtime
- [ ] Org breakdown chart renders correctly
- [ ] Stats respect user's org filter

---

### Issue 4.3: Production Deployment & Environment Configuration
**Description:** Deploy the application to production with proper environment separation.
**Steps:**
1. Supabase project already on cloud (created in Issue 1.1)
2. Deploy frontend to Vercel (connect GitHub repo, auto-deploy on push to main)
3. Set environment variables in Vercel: `VITE_SUPABASE_URL`, `VITE_SUPABASE_ANON_KEY`
4. Configure custom domain (optional, e.g., tasks.ferrisdev.com)
5. Enable Supabase email rate limiting (prevent abuse)
6. Enable Supabase Auth email confirmation for new signups
7. Test full flow: signup -> login -> create task -> receive notification -> complete task

**Git Commit Message:** `chore(deploy): production deployment to Vercel with env config`

**Acceptance Criteria:**
- [ ] App accessible via public URL
- [ ] Auth works in production
- [ ] Realtime works in production
- [ ] Notifications (email + SMS) work in production
- [ ] No secrets exposed in client-side code

---

### Issue 4.4: Seed Production Data & Onboard Team
**Description:** Create accounts for all 60 employees and organize them into their correct entities.
**Steps:**
1. Create admin accounts: David Ferris (super_admin), Brian Charville (admin), Kevin Puquette (admin - Beehive), Chris & Kelsey (admin - Expedited Construction)
2. Bulk invite remaining employees via CSV upload to Supabase Auth
3. Write a 1-page user guide: "How to create a task in 30 seconds"
4. Schedule 15-minute demo with each entity lead

**Git Commit Message:** `chore(onboard): seed users, org assignments, and generate user guide`

**Acceptance Criteria:**
- [ ] All key personnel have accounts with correct roles
- [ ] Each employee assigned to correct organization(s)
- [ ] User guide written and distributed
- [ ] Ferris can log in and see tasks across all entities

---

## TOTAL ISSUES: 13
## ESTIMATED COST: $0-45/mo (Supabase Free/Pro + Vercel Free/Pro + ~$30/mo Twilio SMS)
## ESTIMATED BUILD TIME: 3-4 weeks (1 developer, sequential phases)
