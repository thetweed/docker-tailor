# Session C — Bigger Moves: Interactive Import, Quick Export & Guided Builder

## Context
This is a resume-tailoring Flask app ("Docker Tailor"). After a UX persona review across three personas (early-career, mid-career, veteran), we identified the top bigger-move improvements. This session tackles the three highest-impact features. Sessions A+B (quick wins) should be completed first.

Consult `CLAUDE.md` at the project root for full file structure, DB schema, route map, and key patterns.

Run `docker-compose up -d --build` to test; app is on port 8080.

## What to build (3 features)

### Feature 1: Interactive Import Review (HIGH IMPACT — all personas)

**Problem:** The review_resume_import.html page currently shows all extracted components and AI suggestions as read-only. The only action is "Save All to Resume Library" — no way to edit, deselect, or reject individual items before saving. Veterans import 80 items and want to skip half; early-career users see AI suggestions they can't act on.

**Current flow:**
1. User uploads resume on `/resume/import`
2. `routes/resume.py` `import_resume()` POST handler calls AI, stores results in `session['import_data']` and `session['import_suggestions']`, redirects to `review_resume_import.html`
3. Review page renders everything read-only
4. "Save All" POSTs to `save_import()` which reads from session and creates all records

**Target flow:**
1. Same upload step
2. Review page renders with **checkboxes** on each extracted component (experiences, bullets, skills, education) — all checked by default
3. Each component has an **inline edit** capability (click to expand an edit form, or at minimum an edit icon that reveals input fields)
4. AI suggestions (clarifying questions, bullet improvements) have **action buttons** inline — not just display text
5. "Save Selected" button at the bottom saves only checked items
6. The save handler reads which IDs were checked from the form POST, not blindly from session

**Implementation approach:**
- Add checkboxes to each component in `templates/review_resume_import.html`. Each component needs a unique index (loop.index) to generate form field names like `include_experience_0`, `include_bullet_3`, etc.
- Add hidden inputs with the component data (or keep using session data keyed by index)
- In `routes/resume.py` `save_import()`, check which indices were submitted as checked
- For inline editing: add collapsible edit forms per component. On POST, read edited values from form fields, falling back to session data for unedited items.
- For AI suggestion actions: bullet improvements can have "Accept" (replaces the extracted bullet text before save) and "Skip" buttons. This can be client-side JS that swaps the displayed text and updates a hidden input.

**Files to modify:**
- `templates/review_resume_import.html` — major rework (checkboxes, edit forms, suggestion actions)
- `routes/resume.py` — `save_import()` needs to handle selective saving
- Possibly `static/js/main.js` or inline JS for edit toggle and suggestion accept

### Feature 2: Quick Export from Tailor Results (HIGH IMPACT — mid-career, early-career)

**Problem:** Every export currently goes through: Export home → Export Select (profile picker + component checkboxes + format selection) → download. Users coming from tailor results already have pre-selected components — they just want a PDF.

**Target:** Add a "Download as PDF" button directly on the tailor results page that exports the AI-recommended components with no intermediate steps.

**Implementation approach:**
- Add a button on `templates/tailor_results.html` next to the existing "Export Tailored Resume" link: "Quick Export as PDF"
- This button should POST to a new route (or reuse `export.export_generate()`) with:
  - The pre-selected component IDs from the analysis
  - `export_format=pdf`
  - No profile (or the default profile if one exists)
- New route option: Add a `routes/export.py` route like `POST /export/quick/<int:analysis_id>` that:
  1. Loads the analysis
  2. Extracts recommended component IDs from the analysis JSON
  3. Calls the same export generation logic as `generate_export()`
  4. Returns the PDF file download
- Alternative: reuse the existing `generate_export()` by constructing a form POST with hidden inputs (client-side JS builds a form and submits it). This avoids a new route but is messier.

**Recommended: new route.** It's cleaner and the logic for extracting component IDs from an analysis already exists in the export_select template context.

**Files to modify:**
- `routes/export.py` — add `quick_export(analysis_id)` route
- `templates/tailor_results.html` — add "Quick Export as PDF" button
- Possibly `routes/tailoring.py` — if the analysis_id needs to be passed differently

### Feature 3: Guided "Build from Scratch" Wizard (HIGH IMPACT — early-career)

**Problem:** The only way to get resume content into the app is Import (requires a file) or adding components one at a time via separate forms (add experience, add bullet, add skill, add education — each a separate page with no sequencing). Early-career users who don't have a resume file are stranded.

**Target:** A step-by-step wizard flow: Add Experience → Add Bullets for it → Add Skills → Add Education → Done!

**Implementation approach:**
- New template: `templates/resume_wizard.html` — a multi-step form or a sequence of linked pages
- Option A (single page with JS steps): One page with 4 sections shown one at a time. Each "Next" button hides the current section and shows the next. Final "Save All" submits everything at once.
- Option B (linked pages with session state): Each step is a separate page that saves its data and redirects to the next. Use session to track wizard progress. Simpler server-side, more page loads.
- **Recommend Option A** — it's more modern, avoids session complexity, and feels faster.

**Wizard steps:**
1. **Experience** — Company, title, dates, location, description. "Add Another Experience" button to add more. Minimum 1.
2. **Bullets** — For each experience added in step 1, show a section with a textarea per bullet. "Add Another Bullet" button. Show the experience name as context.
3. **Skills** — Skill name + category fields. "Add Another Skill" button. Could pre-suggest categories.
4. **Education** — School, degree, field, year, location. "Add Another" button.
5. **Review & Save** — Summary of everything, then "Save to My Resume" button.

**The save handler** can reuse the existing model create methods: `Experience.create()`, `Bullet.create()`, `Skill.create()`, `Education.create()`.

**Entry point:** Add a "Build from Scratch" button on the dashboard (in the getting-started section from Session A quick wins) and on the resume import page ("Don't have a resume file? Build from scratch").

**Files to create:**
- `templates/resume_wizard.html` — new template
**Files to modify:**
- `routes/resume.py` — add `resume_wizard()` GET/POST route
- `templates/index.html` — add "Build from Scratch" link in getting-started section
- `templates/import_resume.html` — add "Build from Scratch" link

## Acceptance criteria
- Import review page has checkboxes, components can be deselected before saving
- Import review page supports inline editing of at least component text fields
- Tailor results page has a "Quick Export as PDF" button that downloads immediately
- "Build from Scratch" wizard walks user through adding experience → bullets → skills → education
- Wizard is accessible from dashboard and import page
- All new features work in Docker build

## Suggested order
1. Quick Export (smallest scope, highest ratio of impact to effort)
2. Interactive Import Review (medium scope, touches existing templates)
3. Guided Builder Wizard (largest scope, new template + route)

## Gotchas
- The import review page stores data in `session['import_data']` — Flask sessions have a size limit (~4KB with cookies). Large resumes may already be pushing this. If you hit issues, consider using server-side session storage or a temporary DB table.
- The quick export route needs to handle the case where the analysis references components that have been deleted since the analysis was run (stale IDs). Filter to only existing component IDs.
- The wizard's "Save All" handler should use `_import_or_skip()` from `routes/resume.py` for duplicate detection, same as the import flow.
- `Bullet.create()` requires `experience_id` — bullets created in the wizard should be linked to the experience created in step 1. Since everything saves at once, you'll need to create experiences first, capture their IDs, then create bullets with those IDs.
- CSRF: all new forms need `{{ csrf_input() }}`.
