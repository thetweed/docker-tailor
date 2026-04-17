# Session B — Quick Wins: Tailor, Export, Forms & Labels

## Context
This is a resume-tailoring Flask app ("Docker Tailor"). A UX persona review identified 12 quick wins. Session A covers identity/onboarding/flow (7 items touching navigation, dashboard, resume page, routes). This session covers the remaining 5 items touching tailor, export, suggestions, and job forms — NO file overlap with Session A.

**Run Session A first** (or at least the nav/title renames), since these templates inherit from base.html which Session A updates.

All Tier 1+2 audit fixes are committed. The repo is clean on `main`. Run `docker-compose up -d --build` to test; app is on port 8080.

## What to change (5 items)

### 1. Change default export format from .txt to .pdf
- `templates/export_select.html`: Move the `checked` attribute from the `value="txt"` radio button to the `value="pdf"` radio button
- That's it — one attribute move

### 2. Sort recommended skills by relevance score on tailor results
- `templates/tailor_results.html`: The skills section (around line 122-138) iterates `analysis.skills` without sorting. Experiences and bullets both use `|sort(attribute='relevance_score', reverse=True)`. Apply the same filter to skills:
  - Change `{% for skill_rec in analysis.skills %}` to `{% for skill_rec in analysis.skills|sort(attribute='relevance_score', reverse=True) %}`
- Also display the relevance score badge on each skill (currently skills don't show their score, unlike experiences/bullets/education). Add a score badge span before the skill name, matching the style used in the education section.

### 3. Add search/filter to tailor home job list
- `templates/tailor.html`: Add a client-side text filter input above the job list in the left column (the "Select a Job to Tailor For" card). 
- Add an input field: `<input type="text" id="jobFilter" class="form-input" placeholder="Filter jobs..." style="margin-bottom: var(--spacing-md);">` before the job cards loop
- Add JS at the bottom: on input, filter the job cards by checking if the card's text content (job title + company name + location) contains the search string (case-insensitive). Hide non-matching cards with `style.display = 'none'`.
- Show a "No matching jobs" message when all cards are hidden.
- This is purely client-side — no route changes needed.

### 4. Make URL optional on manual job add form
- `templates/add_job_manual.html`: Remove `required=true` from the URL `input` macro call (around line 21-25). Change `type='url'` to just `type='text'` so the browser doesn't enforce URL format on optional input.
- `routes/jobs.py`: In the `add_job_manual()` POST handler, the URL is currently used as-is. Make it optional:
  - If URL is provided, validate it (existing SSRF check + scheme check should still apply)
  - If URL is empty/blank, either store an empty string or generate a placeholder like `manual-entry-{timestamp}` — BUT check that `Job.exists(url)` won't false-positive on empty strings. The `jobs` table has `url UNIQUE`, so empty strings will collide. Best approach: if URL is blank, generate a unique placeholder like `manual://{company}-{title}-{timestamp}` that won't collide.
  - The SSRF check (`is_safe_url()`) should only run when a real URL is provided.

### 5. Rename suggestion action buttons to plain language
- `templates/suggestions.html`: In the bullet improvements section (around lines 228-248), rename the buttons:
  - "Replace Original" → "Use This Instead" (the `🔄` emoji can stay)
  - "Add as New (Keep Original)" → "Keep Both" (the `➕` emoji can stay)
  - "Dismiss" → "Skip" (change `✗ Dismiss` to `✗ Skip`)
- Also in the same template, for the general dismiss buttons used across all sections, keep "Dismiss" as-is — the rename only applies to the bullet improvement section where the three-way choice is confusing.
- "Dismiss All" buttons at section headers can stay as "Dismiss All" since they're clearly destructive actions, not a skip.

## Acceptance criteria
- Export select page defaults to PDF radio button selected
- Tailor results page shows skills sorted by relevance with score badges
- Tailor home has a working filter input that hides non-matching job cards
- Manual job add works without a URL (stores a generated placeholder)
- Bullet improvement buttons say "Use This Instead" / "Keep Both" / "Skip"
- Docker build succeeds, all pages render without errors

## Gotchas
- The `jobs` table has a UNIQUE constraint on `url`. Empty strings cannot be stored for multiple manual entries — must generate unique placeholders.
- `Job.exists(url)` is used for duplicate detection. Make sure the placeholder scheme doesn't interfere (prefixing with `manual://` ensures it won't match real URLs).
- The Jinja `|sort` filter works on lists of dicts — `analysis.skills` comes from parsed JSON and should be a list of dicts with `relevance_score` keys. If any skill is missing `relevance_score`, the sort will fail. Add a fallback: `|sort(attribute='relevance_score', reverse=True)` — Jinja's sort handles missing keys by placing them last, but verify this works with the actual data structure.
- The client-side job filter should use `textContent` not `innerHTML` for matching to avoid matching against HTML attribute values.
