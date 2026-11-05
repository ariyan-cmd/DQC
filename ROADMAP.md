# Roadmap

Rule: one slice per branch. A slice is done only when tests and lint pass, the diff is
understood, and DEVLOG.md has an entry. Cut line if time runs short: in-box blur, then the
histogram, then the tiny-resolution check. Never cut label checks, the explainable breakdown,
or the live sample report.

- [ ] **0. Scaffold** `chore/scaffold` (1-2h): repo layout, CLAUDE.md, DEVLOG.md, .gitignore, uv + Vite setup, CI running ruff + pytest
- [ ] **1. Loader + skeleton CLI** `feat/loader` (3-4h): fixture generator, Pydantic models, streaming loader for all 3 layouts, safe data.yaml, path containment, minimal report.json
- [ ] **2. Image checks** `feat/image-checks` (2-3h): corrupt files, tiny resolution, exact duplicates (SHA-256), decompression bombs
- [ ] **3. Label checks** `feat/label-checks` (3h): missing/empty labels, out-of-bounds, zero-size boxes, invalid class IDs
- [ ] **4. Small-object stats** `feat/small-objects` (3-4h): tiny-box ratio, size histogram, in-box blur (warning only)
- [ ] **5. Scoring + final report** `feat/scoring` (2-3h): four sub-scores, weighted overall, reasons, capped issues, generated JSON schema
  - Milestone: CLI works end to end
- [ ] **6. Viewer core** `feat/viewer-core` (3-4h): Vite/React shell, sample report, drag-and-drop, Zod validation, score and section cards
- [ ] **7. Viewer details** `feat/viewer-issues` (2-3h): filterable issue table, histogram, friendly errors, plain-text rendering test
  - Milestone: full product works locally
- [ ] **8. Ship** `feat/deploy` (3-4h): GitHub Pages deploy (set Vite base path), README with Roboflow-vs-COCO comparison, 10k-image timing test
  - Milestone: MVP done per PRD

## Risks to watch
- Dataset format mismatch (check `data.yaml` and label files first)
- In-box blur noisy on tiny boxes
- Score weights are arbitrary until tuned on real runs
- Windows path handling (use pathlib, forward slashes in report)
- Code the owner can't explain: do not merge it