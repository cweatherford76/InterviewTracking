# Interview Tracker — Product Requirements Document

**Status:** Draft v1
**Owner:** cweatherford76
**Last updated:** 2026-05-07

---

## 1. Overview

Interview Tracker is a **locally hosted, single-user web app** for managing a personal job search. It replaces the messy mix of spreadsheets, sticky notes, calendar invites, and inbox searches that most candidates use to keep track of where they applied, who they spoke to, what was asked in interviews, and what's next.

### 1.1 Goals

- Give the user a single place to record everything about a job opportunity, from first interest through final outcome.
- Make it trivial to answer "What's coming up this week?" and "What did they ask me last time?"
- Keep the user's data **local, portable, and private** — one SQLite file, no cloud, no account.
- Be runnable with **one command** on any machine with Python.

### 1.2 Non-goals (v1)

- Multi-user support / authentication
- Cloud sync, mobile apps, or browser extensions
- Resume builder, cover letter generation, or AI assistance
- Email/SMS reminders or push notifications
- Job board scraping or auto-import from LinkedIn/Indeed
- File uploads (folder paths only, see §4.3)

---

## 2. Users & Use Cases

**Primary user:** an active job seeker tracking 5–50 simultaneous opportunities at varying stages.

### Core use cases

1. **Capture a new posting** — drop in a URL, company, title, and rating; tag it; come back later to apply.
2. **Log an application** — record date, method (LinkedIn / referral / direct / etc.), and any deadline.
3. **Schedule and prep for an interview** — add round, format, time, interviewers, prep notes; review later.
4. **Capture interview Q&A** — quickly record what was asked and how you answered, while it's fresh.
5. **Track conversations** — emails, calls, follow-ups, with optional follow-up reminder dates.
6. **See the week ahead** — open the calendar to see all upcoming interviews, deadlines, and follow-ups.
7. **Triage the pipeline** — Kanban view to drag jobs through statuses; filter by tag/company/status.
8. **Reflect on a company** — open a company page to see all jobs, interviews, and contacts there.

---

## 3. Tech Stack

| Layer | Choice | Why |
|---|---|---|
| Language / framework | Python 3.11+, Flask | Tiny, well-known, easy local install |
| ORM / migrations | Flask-SQLAlchemy + Flask-Migrate (Alembic) | Schema evolves cleanly as features land |
| Database | SQLite | Single file, zero ops, easy backup |
| Templating | Jinja2 | Built-in, no build step |
| Interactivity | HTMX (vendored) | Inline updates without an SPA |
| Styling | Bootstrap 5 (CDN) | Clean defaults, responsive, no build step |
| Calendar | FullCalendar 6 (CDN) | Month/week/day views, drag-and-drop |
| Tests | pytest | Smoke tests for routes + models |

---

## 4. Functional Requirements

### 4.1 Jobs

A **Job** represents one specific role at one company. Fields:

- Company (FK, required)
- Title, location, remote type (`remote` / `hybrid` / `onsite`)
- Job post URL, local folder path (string — see §4.3)
- Salary min, salary max, salary notes
- Description, source (where you found it)
- Application date, application method, application deadline
- **Status:** `interested` / `applied` / `interviewing` / `offer` / `rejected` / `withdrawn`
- **Rating:** 1–5 (optional)
- Tags (many-to-many)
- Free-form notes
- Auto: `created_at`, `updated_at`

**Views:**
- `/jobs` — list with filters: status, tag, company, text search
- `/jobs/pipeline` — Kanban by status, drag to change status
- `/jobs/<id>` — detail view (links, tags, rating, contacts, conversations, interviews, notes)
- `/jobs/new`, `/jobs/<id>/edit`

### 4.2 Companies & Contacts

- **Company:** name, website, industry, size, headquarters, notes
- **Contact:** name, title, email, phone, LinkedIn, notes; optional company FK
- Company detail page lists all jobs at that company and all known contacts.

### 4.3 Local folder path

Each Job has a `local_folder_path` text field. The user types/pastes an absolute path (e.g. `/home/me/jobs/Acme/`). On the job detail page it's rendered as `<a href="file://...">Open folder</a>`.

> **Note:** Browsers vary in their handling of `file://` links from `http://` pages. The form will display a hint about this. No files are uploaded or copied; the app only stores the string.

### 4.4 Interviews

An **Interview** belongs to a Job. Fields:

- Scheduled at (datetime), duration in minutes
- Round name (e.g. "Phone Screen", "Tech Round 1", "Onsite Loop")
- Format: `phone` / `video` / `onsite`
- Location or video link (text)
- Status: `scheduled` / `completed` / `cancelled` / `rescheduled`
- Preparation notes, outcome notes
- Overall impression (1–5, optional)

**Sub-records:**
- **Interview Participants** — interviewers; either an existing Contact or a free-text name + role
- **Interview Questions** — ordered list of `(question, my_answer, notes, was_difficult)`; added/removed inline via HTMX

### 4.5 Conversations

A **Conversation** belongs to a Job (and optionally a Contact):

- Occurred at (datetime)
- Channel: `email` / `phone` / `message` / `other`
- Subject, notes
- Follow-up date (optional — surfaces on the calendar and dashboard)

### 4.6 Tags

Free-form labels with a name and color. Many-to-many with Jobs. Managed at `/tags`.

### 4.7 Calendar

`/calendar` renders a FullCalendar with three event sources merged:

| Source | Color | Source field |
|---|---|---|
| Interviews | blue (varies by status) | `interview.scheduled_at` + `duration_minutes` |
| Application deadlines | red (all-day) | `job.application_deadline` |
| Follow-ups | amber (all-day) | `conversation.follow_up_date` |

- Views: month, week, day
- Click an event → navigate to the relevant detail page
- Drag an interview to a new date/time → `PATCH /api/interviews/<id>/reschedule` updates `scheduled_at`
- Backed by `GET /api/calendar/events?start=&end=` returning JSON

### 4.8 Dashboard (`/`)

- Next 7 days of interviews
- Overdue / upcoming follow-ups (next 7 days)
- Job counts by status
- Recently updated jobs

---

## 5. Data Model

Nine tables. Indexes on hot lookup columns.

| Table | Key fields |
|---|---|
| `company` | `id, name, website, industry, size, headquarters, notes, created_at` |
| `contact` | `id, company_id?, name, title, email, phone, linkedin_url, notes` |
| `job` | `id, company_id, title, location, remote_type, job_post_url, local_folder_path, salary_min, salary_max, salary_notes, description, source, application_date, application_method, application_deadline, status, rating, notes, created_at, updated_at` |
| `tag` | `id, name UNIQUE, color` |
| `job_tag` | `job_id, tag_id` (PK composite) |
| `conversation` | `id, job_id, contact_id?, occurred_at, channel, subject, notes, follow_up_date?` |
| `interview` | `id, job_id, scheduled_at, duration_minutes, round_name, format, location_or_link, status, preparation_notes, outcome_notes, overall_impression?` |
| `interview_participant` | `id, interview_id, contact_id?, name_text?, role` |
| `interview_question` | `id, interview_id, position, question, my_answer, notes, was_difficult` |

**Indexes:** `job(status)`, `job(company_id)`, `interview(scheduled_at)`, `conversation(follow_up_date)`, `job(application_deadline)`.

---

## 6. URL / Route Map

```
GET   /                              dashboard
GET   /jobs                          list (filters via querystring)
GET   /jobs/pipeline                 kanban by status
GET   /jobs/new                      form
POST  /jobs                          create
GET   /jobs/<id>                     detail
GET   /jobs/<id>/edit                form
POST  /jobs/<id>                     update
POST  /jobs/<id>/delete              delete
GET/POST /companies, /companies/<id>(/edit)
GET/POST /contacts,  /contacts/<id>(/edit)
GET   /jobs/<id>/interviews/new
POST  /jobs/<id>/interviews
GET   /interviews/<id>(/edit)
POST  /interviews/<id>/questions          (HTMX)
DELETE /interviews/<id>/questions/<qid>   (HTMX)
POST  /interviews/<id>/participants       (HTMX)
GET   /jobs/<id>/conversations/new
POST  /jobs/<id>/conversations
GET   /conversations/<id>/edit
GET   /tags                          manage tags
GET   /calendar                      calendar page
GET   /api/calendar/events           JSON feed for FullCalendar
PATCH /api/interviews/<id>/reschedule    drag-drop endpoint
```

---

## 7. Milestones

Implementation will land in roughly five PRs:

| # | Milestone | Includes |
|---|---|---|
| M1 | Foundation | Flask app skeleton, config, models, migrations, base template, Bootstrap/HTMX wired in, dashboard placeholder |
| M2 | Companies, contacts, jobs CRUD | List/detail/form pages, status pipeline (Kanban), tags, search & filters |
| M3 | Interviews & conversations | Interview CRUD with inline questions/participants (HTMX), conversations CRUD with follow-up dates |
| M4 | Calendar | FullCalendar integration, JSON feed (interviews + deadlines + follow-ups), drag-to-reschedule |
| M5 | Polish & tests | Dashboard widgets, seed script, smoke tests, README finalization |

---

## 8. Acceptance Criteria

The v1 build is "done" when all of the following pass:

1. `flask --app app db upgrade` creates the schema cleanly on a fresh checkout.
2. `pytest` passes with smoke tests covering: create company → create job → tag job → add interview with 2 questions → add conversation with follow-up.
3. Manual end-to-end:
   - Create company "Acme" and a job "Senior Engineer" at Acme with folder path, tags, and rating.
   - Move the job through pipeline statuses on `/jobs/pipeline`.
   - Add 2 interviews with different rounds; add interviewers and questions to each.
   - Add a conversation with a follow-up date 3 days out.
   - `/calendar` shows the 2 interviews (blue), the deadline (red), the follow-up (amber).
   - Drag an interview to a different date in the week view; reload — new time persists.
   - `/jobs?status=interviewing&tag=remote` returns the expected rows.
4. Data backup: copying `interview_tracker.db` while the server is stopped fully preserves state.

---

## 9. Risks & Open Questions

| Risk / question | Mitigation |
|---|---|
| `file://` links blocked by browser | Document the limitation in the form's help text; consider a "copy path" button as a fallback |
| Datetime / timezone confusion | Store all datetimes in UTC; display in the user's local timezone; one timezone-aware test |
| SQLite concurrency on backup | Stop server before copying; document this clearly |
| Schema churn during build | Use Alembic from day one — every model change goes through a migration |

---

## 10. Future Ideas (Post-v1)

- iCal export of interview events
- "Common questions" report across all interviews
- Salary expectation tracker / offer comparison
- Email integration (paste email → conversation)
- AI-assisted interview prep based on logged questions
- Optional auth + remote hosting for use across machines
