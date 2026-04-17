# Session D — Bigger Moves: Saved Selections, Tailor UX & Bulk Actions

## Context
This is a resume-tailoring Flask app ("Docker Tailor"). After a UX persona review across three personas (early-career, mid-career, veteran), we identified bigger-move improvements. This session tackles the power-user and scalability features — primarily benefiting the veteran persona (50-80 bullets, 8-12 experiences, 15+ jobs) but also improving the mid-career flow.

Sessions A+B (quick wins) and Session C (interactive import, quick export, guided builder) should be completed first.

Consult `CLAUDE.md` at the project root for full file structure, DB schema, route map, and key patterns.

Run `docker-compose up -d --build` to test; app is on port 8080.

## What to build (4 features, in priority order)

### Feature 1: Saved Component Selections on Export Profiles (HIGH IMPACT — veteran)

**Problem:** Export profiles currently save transformation rules (rename_category, merge_categories, section_order, use_alternate_title) but NOT which components to include. A veteran who regularly exports a "product-focused" resume and an "engineering-focused" resume must manually re-select components every time. This is the single biggest repeated-effort pain point for power users.

**Target:** Export profiles can optionally store a saved component selection (which experience IDs, bullet IDs, skill IDs, education IDs to pre-check). When starting an export with that profile, the saved selections are pre-loaded.

**Implementation approach:**
- **Schema change:** Add a new table `export_profile_selections`:
  ```sql
  CREATE TABLE IF NOT EXISTS export_profile_selections (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      profile_id INTEGER NOT NULL REFERENCES export_profiles(id),
      component_type TEXT NOT NULL,  -- 'experience', 'bullet', 'skill', 'education'
      component_id INTEGER NOT NULL,
      UNIQUE(profile_id, component_type, component_id)
  );
  ```
  Add this to `models/database.py` `init_db()`. Use the established migration pattern (CREATE TABLE IF NOT EXISTS).
- **Model methods:** Add to `models/export_profile.py`:
  - `ExportProfile.save_selections(profile_id, experience_ids, bullet_ids, skill_ids, education_ids)` — clears existing selections for the profile, inserts new ones
  - `ExportProfile.get_selections(profile_id)` — returns a dict like `{'experience_ids': set(...), 'bullet_ids': set(...), ...}`
- **Export select page:** On `templates/export_select.html`, when a profile with saved selections is chosen, pre-check the matching components (in addition to or instead of the analysis-based pre-selection). Add a "Save current selection to profile" button that POSTs the checked component IDs.
- **New route:** `POST /export/profiles/<id>/save-selections` in `routes/export.py`
- **Profile change handler:** The JS `onProfileChange()` function needs to also load and apply saved selections when a profile is chosen.

**Interaction with existing pre-selection:** If the user arrives via a tailor analysis AND selects a profile with saved selections, the profile selections should take precedence (they're the user's explicit curation). Show a note: "Profile selections loaded. Analysis recommendations are available as a starting point if you clear the profile selection."

### Feature 2: Relevance Threshold Filter on Tailor Results (MEDIUM IMPACT — veteran)

**Problem:** Tailor results with 50-80 scored bullets are an enormous page. Users must scroll through everything even though they only care about high-relevance items.

**Target:** A client-side filter on the tailor results page that lets users show only items above a chosen relevance threshold.

**Implementation approach:**
- Add a filter control at the top of `templates/tailor_results.html`, below the action buttons:
  ```html
  <div class="card" style="margin-bottom: var(--spacing-lg);">
      <div class="card-body" style="display: flex; align-items: center; gap: var(--spacing-md);">
          <label>Show items with relevance above:</label>
          <input type="range" id="relevanceSlider" min="0" max="100" value="0" step="5">
          <span id="relevanceValue">0%</span>
          <button class="btn btn-small btn-secondary" onclick="resetFilter()">Show All</button>
      </div>
  </div>
  ```
- Each recommendation card needs a `data-relevance="85"` attribute on its container div.
- JS: On slider change, hide all cards with `data-relevance` below the threshold. Update counts in section headers.
- Also add a visual count: "Showing X of Y experiences, X of Y bullets" that updates as the filter changes.

**Files to modify:**
- `templates/tailor_results.html` — add filter UI, add data attributes to cards, add JS

### Feature 3: Bulk Actions on Resume Library (MEDIUM IMPACT — veteran)

**Problem:** Managing 80 bullets one at a time (Edit/Delete per bullet) is tedious. No multi-select, no bulk delete, no bulk re-categorize.

**Target:** Add a "Manage" mode to the resume library's Bullets and Skills sections that enables multi-select checkboxes with a floating action bar.

**Implementation approach:**
- Add a "Manage" toggle button in the Bullets section header (next to "Add Bullet" and "Variants")
- When active:
  - Each bullet row gets a checkbox (left side)
  - A floating action bar appears at the bottom of the viewport: "X selected | Delete Selected | Change Category | Cancel"
  - "Delete Selected" POSTs an array of bullet IDs to a new route
  - "Change Category" shows a dropdown of existing categories + custom input, then POSTs
- Same pattern for Skills section (bulk delete, bulk change category)

**New routes in `routes/resume.py`:**
- `POST /resume/bullets/bulk-delete` — accepts `bullet_ids[]` form array, deletes all
- `POST /resume/bullets/bulk-categorize` — accepts `bullet_ids[]` + `category`, updates all
- `POST /resume/skills/bulk-delete` — accepts `skill_ids[]`, deletes all
- `POST /resume/skills/bulk-categorize` — accepts `skill_ids[]` + `category`, updates all

**Files to modify:**
- `templates/resume.html` — add manage mode toggle, checkboxes, floating action bar
- `routes/resume.py` — add bulk action routes
- `static/css/style.css` — floating action bar styling

### Feature 4: Saved Analyses Search and Improved UX (LOWER PRIORITY)

**Problem:** The saved analyses page (`templates/saved_analyses.html`) is a flat table with no search, sort, or grouping. After 15+ tailoring runs it's hard to find anything.

**Target:** Add client-side search/filter and improve the table with more context.

**Implementation approach:**
- Add a search input above the table (filter by job title, company name)
- Add sortable column headers (reuse the pattern from `templates/jobs.html` which already has client-side sorting)
- Add a "recommended components" count per row (e.g., "8 bullets, 5 skills") so users can gauge depth without opening each one
- The component count needs to come from the analysis JSON. In `models/tailor_analysis.py`, add a method or modify `get_all_with_job_info()` to also return counts from the JSON.

**Files to modify:**
- `templates/saved_analyses.html` — search input, sortable headers, extra columns
- `models/tailor_analysis.py` — possibly `get_all_with_job_info()` to extract counts

## Acceptance criteria
- Export profiles can save and restore component selections
- Tailor results have a working relevance threshold slider
- Resume library has a "Manage" mode with bulk delete and bulk re-categorize for bullets and skills
- Saved analyses page has search/filter and sortable columns
- All new features work in Docker build, no regressions

## Suggested order
1. Relevance threshold filter (smallest scope, pure client-side)
2. Saved analyses search (small scope, client-side + minor model change)
3. Saved component selections (medium scope, schema change + model + route + template)
4. Bulk actions (medium scope, new routes + significant template JS)

## Gotchas
- **Schema migration:** The `export_profile_selections` table uses `CREATE TABLE IF NOT EXISTS` which is safe. But if a profile is deleted, its selections should also be deleted. Since there's no `ON DELETE CASCADE` on existing FKs (noted as Tier 3 audit item), add explicit cleanup in `ExportProfile.delete()` — delete from `export_profile_selections WHERE profile_id = ?` before deleting the profile.
- **Bulk delete safety:** Bulk bullet delete should check for group_id implications — deleting a group default should auto-promote another member (existing pattern in `delete_bullet()`). The bulk delete route should iterate and call the existing `Bullet.delete()` method per bullet rather than a raw `DELETE WHERE id IN (...)` to preserve this logic.
- **CSRF:** All new POST routes need CSRF protection. The bulk action forms use JS-constructed requests — include the CSRF token from the meta tag (`meta[name="csrf-token"]`).
- **sqlite3.Row access:** All model methods must use `row['column']` not `row.get('column')`.
- **The relevance slider values come from AI-generated JSON.** Some analysis entries may lack `relevance_score` — default missing scores to 0 in the data attribute.
