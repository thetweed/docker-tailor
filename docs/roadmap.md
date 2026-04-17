# UX Improvement Roadmap

Generated 2026-04-17 from a three-persona UX review (early-career, mid-career, veteran).

## Session Order

| Session | Scope | Est. items | Depends on |
|---|---|---|---|
| **A** | Quick wins: identity, onboarding, flow guidance | 7 items | — |
| **B** | Quick wins: tailor, export, forms, labels | 5 items | A (base.html titles) |
| **C** | Bigger moves: interactive import, quick export, guided builder | 3 features | A+B |
| **D** | Bigger moves: saved selections, tailor UX, bulk actions | 4 features | A+B |

Sessions C and D are independent of each other and can run in any order after A+B.

## Handoff Docs

- [Session A — Quick Wins: Identity, Onboarding & Flow Guidance](session-a-quick-wins-identity.md)
- [Session B — Quick Wins: Tailor, Export, Forms & Labels](session-b-quick-wins-tailor-export.md)
- [Session C — Bigger Moves: Interactive Import, Quick Export & Guided Builder](session-c-bigger-moves-import-export-builder.md)
- [Session D — Bigger Moves: Saved Selections, Tailor UX & Bulk Actions](session-d-bigger-moves-power-user.md)

## Quick Wins Summary (Sessions A+B)

1. Rename app "Job Tracker" → "Resume Tailor" (all templates)
2. Rename "Components" nav → "Resume", page header → "My Resume"
3. Sequenced getting-started guidance on empty dashboard
4. "What's next" flash messages after import and job add
5. Rename "Analyze with AI" → "Improve with AI"
6. Contextual empty-state help text on resume page
7. Pending-suggestions count badge on Suggestions nav item
8. Default export format .txt → .pdf
9. Sort skills by relevance on tailor results + show score badges
10. Client-side search/filter on tailor home job list
11. Make URL optional on manual job add
12. Rename bullet improvement actions to plain language

## Bigger Moves Summary (Sessions C+D)

### Session C
1. **Interactive import review** — checkboxes, inline editing, suggestion actions before save
2. **Quick export from tailor results** — one-click PDF download with AI-recommended components
3. **Guided "build from scratch" wizard** — step-by-step resume creation for users without a file

### Session D
1. **Saved component selections on export profiles** — profiles remember which items to include
2. **Relevance threshold filter on tailor results** — slider to hide low-relevance items
3. **Bulk actions on resume library** — multi-select delete and re-categorize for bullets/skills
4. **Saved analyses search/sort** — searchable, sortable analyses table with component counts

## Deferred (not in current roadmap)

These were identified but deprioritized:
- Analysis comparison view (side-by-side diff of two tailoring runs)
- "Never recommended" audit view (content that no analysis has ever suggested)
- Scoped AI suggestions (analyze one experience at a time instead of whole resume)
- Onboarding checklist widget (persistent progress tracker on dashboard)
- "Paste job description" as primary add-job flow (tab alongside URL scraper)
- Export preview (render HTML preview before downloading)
- Re-tailor with guidance (text box to steer AI emphasis on re-run)
- Job editing after scrape
- Named resume snapshots (save component selection with a name)

These can be picked up in future sessions if the core roadmap proves out.
