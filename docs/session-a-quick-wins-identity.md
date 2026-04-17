# Session A — Quick Wins: Identity, Onboarding & Flow Guidance

## Context
This is a resume-tailoring Flask app ("Docker Tailor"). A UX persona review identified 12 quick wins. This session covers the 7 that touch navigation, identity, the dashboard, the resume page, and route-level flash messages. Session B covers the remaining 5 (tailor, export, suggestions, job forms).

All Tier 1+2 audit fixes are committed. The repo is clean on `main`. Run `docker-compose up -d --build` to test; app is on port 8080.

## What to change (7 items)

### 1. Rename app from "Job Tracker" to "Resume Tailor"
- `templates/partials/navigation.html`: Change navbar logo text from "Job Tracker" to "Resume Tailor"
- `templates/base.html`: Change default `{% block title %}` from "Job Tracker" to "Resume Tailor"
- Every template that has `{% block title %}Foo - Job Tracker{% endblock %}`: replace "Job Tracker" with "Resume Tailor"
- Files to grep: `grep -r "Job Tracker" templates/` — should be ~20 occurrences across all templates
- The `<meta name="description">` in base.html says "AI-powered job application tracking system" — change to "AI-powered resume tailoring tool"

### 2. Rename "Components" nav item to "Resume"
- `templates/partials/navigation.html`: Change the nav link text from "Components" to "Resume" (the href stays the same — `url_for('resume.view_resume')`)
- `templates/resume.html`: Change page header from "Resume Component Library" to "My Resume"
- Keep the blueprint name `resume` and all url_for references unchanged

### 3. Add sequenced getting-started guidance to empty dashboard
- `templates/index.html`: When ALL stats are zero (job_count == 0 and exp_count + bullet_count == 0 and analyses_count == 0), replace the three equal quick-action cards at the bottom with a numbered getting-started section:
  1. "Import or build your resume" → link to import page
  2. "Add a job you're applying for" → link to add job page
  3. "Tailor your resume for that job" → link to tailor page
- When user has data, show the current three cards as-is
- The stats grid and recent jobs table above should remain unchanged

### 4. Add "what's next" flash messages after key actions
- `routes/resume.py` — in the `save_import()` function, after the success flash, add: `flash('Next step: Add a job posting to tailor your resume against!', 'info')` (only if the user has zero jobs — check with a quick count query)
- `routes/jobs.py` — in `add_job()` and `add_job_manual()`, after the success flash, add a flash with a direct link: `flash(Markup('Job added! <a href="' + url_for('tailoring.run_tailor', job_id=new_id) + '">Tailor your resume for this job &rarr;</a>'), 'info')` — make sure to import Markup from markupsafe. Note: this is safe because no user input is interpolated into the Markup string.

### 5. Rename "Analyze with AI" button to "Improve Resume with AI"
- `templates/resume.html`: Change the button text from "Analyze with AI" to "Improve with AI"
- Change the confirm dialog text from "Run AI analysis on your resume?" to "Run AI improvement suggestions on your resume?"
- Change the loading indicator text from "Analyzing your resume with AI..." to "Generating improvement suggestions..."
- Change the JS variable/ID references: `analyzeForm` → `improveForm`, `analyzeBtn` → `improveBtn`, `analyzeLoading` → `improveLoading` (keep consistent)

### 6. Add contextual empty-state help text on resume page
- `templates/resume.html`: Change empty-state messages:
  - Experiences: "No experiences added yet." → "No work experiences yet. Add jobs, internships, volunteer work, or projects."
  - Bullets: "No bullets added yet." → "No bullet points yet. These are the achievement statements that go under each experience."
  - Skills: "No skills added yet." → "No skills added yet. Include technical skills, tools, languages, and soft skills."
  - Education: "No education entries added yet." → "No education yet. Add degrees, certifications, bootcamps, or relevant coursework."

### 7. Add pending-suggestions count badge to "Suggestions" nav item
- `templates/partials/navigation.html`: The Suggestions nav link needs a badge showing the count of pending suggestions. This requires the count to be available in every template.
- `app.py`: In the `create_app()` function, add a `@app.context_processor` that injects `pending_suggestions_count` into all templates. Query: `SELECT COUNT(*) FROM suggestions WHERE status = 'pending'`. Use `get_db_context()` for the query.
- `templates/partials/navigation.html`: After the "Suggestions" text, add a small badge span showing the count (only when > 0): `{% if pending_suggestions_count %}<span class="nav-badge">{{ pending_suggestions_count }}</span>{% endif %}`
- Add minimal CSS for `.nav-badge` in `static/css/style.css` (small pill, primary color background, white text)

## Acceptance criteria
- Navbar says "Resume Tailor" with a "Resume" link instead of "Components"
- All page titles say "- Resume Tailor" instead of "- Job Tracker"
- Empty dashboard shows numbered getting-started steps
- After importing a resume (with no jobs), a flash message suggests adding a job
- After adding a job, a flash message links to tailoring
- "Improve with AI" button on resume page (not "Analyze with AI")
- Empty sections have helpful guidance text
- Suggestions nav item shows a count badge when there are pending suggestions
- Docker build succeeds, all pages render without errors

## Gotchas
- `routes/jobs.py` `add_job()` uses `flash(Markup(...))` — import `Markup` from `markupsafe`, NOT from `flask` (deprecated). The string must not interpolate any user input.
- The context processor for suggestion count runs on every request. Use `get_db_context()` not `get_db()` since it's outside a request-scoped DB connection. Keep the query simple — it's a single COUNT.
- The confirm dialog on "Improve with AI" is in an `onclick` attribute, not in JS — update it inline.
- Don't change any url_for references, blueprint names, or route paths — only display text.
