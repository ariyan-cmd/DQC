# DEVLOG

One entry per finished slice, newest last.

## Template

### Slice N: <name> (<date>)
- **What:**
- **Why:**
- **What I learned:**
- **Tests:**
- **Next:**

## Entries

### Slice 0: Scaffold (2026-11-05)
- **What:** Repo skeleton. `engine/` has a Typer `dsc hello` command, uv setup, ruff config and
  one pytest. `viewer/` has a Vite + React + TypeScript + Tailwind shell and one Vitest test.
  Added .gitignore, this DEVLOG and a GitHub Actions CI workflow (ruff + pytest, lint + test + build).
- **Why:** Fix the folder layout and tooling first so later slices only add code to known places.
- **What I learned:** An entry point in pyproject.toml maps a command name to a Python object.
  Lock files (uv.lock, package-lock.json) pin exact versions. typescript-eslint 8.72.1 does not
  support TypeScript 7, so the viewer uses 6.0.3. uv could not link its Python install inside the
  virtualized AppData folder, so `UV_PYTHON_INSTALL_DIR` pointed outside it.
- **Tests:** engine 1 pytest passed; viewer 1 Vitest passed; ruff, ESLint and the Vite build clean.
  CI not yet seen running on GitHub.
- **Next:** Slice 1, `feat/loader`: fixture generator, Pydantic models, streaming loader.

### Slice 1: Loader + skeleton CLI (2026-11-05)
- **What:** `dsc check <dataset> -o report.json` finds images and labels in all three layouts,
  reads class names from data.yaml, and writes a minimal report (placeholder score, no checks).
  Added Pydantic report models, a streaming loader, a fixture generator and tests.
- **Why:** Everything later (checks, scoring, viewer) needs a trustworthy list of samples and a
  fixed report shape first.
- **What I learned:** A generator (`yield`) hands out one sample at a time so big datasets stay
  out of memory. `safe_load` builds plain data only, so a YAML file cannot run code. `resolve()`
  follows symlinks, which is how paths that escape the dataset root are caught. An unclear
  layout is an error, never a guess.
- **Tests:** 27 passed, 4 symlink tests skipped locally (Windows needs Developer Mode; they run
  in CI on Linux). ruff and `uv build` clean. Not tried on a real Roboflow or COCO export yet.
- **Next:** Slice 2, `feat/image-checks`: corrupt files, tiny resolution, exact duplicates,
  decompression bombs.

### Slice 2: Image checks (2026-11-06)
- **What:** Added the Check protocol and two checks. `ImageCheck` flags corrupt files, files over
  Pillow's pixel limit (decompression bombs) and images under 32 px. `DuplicateCheck` flags
  byte-identical images by SHA-256. Pillow is now a runtime dependency.
- **Why:** Broken, oversized, tiny and repeated images waste training runs and are cheap to find
  before training.
- **What I learned:** `Image.open()` reads only the header, so a truncated file needs a full
  `load()` to fail. Pillow only warns between 1x and 2x its pixel limit, so the warning is turned
  into an error. Hashing in 1 MiB chunks keeps memory flat. A protocol lets checks plug in with
  one line in `build_report`. Fixture images must differ per split or they count as duplicates.
- **Tests:** 36 passed, 4 symlink tests skipped locally (run in CI). ruff and `uv build` clean.
  A planted-problems test finds exactly the corrupt, tiny and duplicate image. Not timed on a
  large dataset or tried on real broken files yet.
- **Next:** Slice 3, `feat/label-checks`: missing/empty labels, out-of-bounds and zero-size
  boxes, invalid class IDs.

### Slice 3: Label checks (2026-11-06)
- **What:** `LabelCheck` reports `missing_label` (warning), `empty_label` (info) and, as errors,
  `malformed_label_line`, `invalid_class_id`, `box_out_of_bounds` and `zero_size_box`. A shared
  `parse_label_file` reads YOLO lines. One issue per problem type per file, with count and first line.
- **Why:** Broken labels silently ruin training; these are the cheapest problems to catch first.
- **What I learned:** YOLO boxes are centre x/y plus width/height as 0-1 fractions, so edges are
  centre minus or plus half the size. `nan` parses as a float but defeats every comparison, so
  non-finite values are rejected. Parsing the class as a float keeps a bad id like 1.5 reportable.
  Adding a check changes what a clean scan returns, so older tests had to be updated.
- **Tests:** 62 passed, 4 symlink tests skipped locally (run in CI). ruff and `uv build` clean.
  A planted-problems test finds exactly the six expected label issues. Bounds rule and 1e-6
  tolerance not yet tried on a real exported dataset.
- **Limits:** Label files with no image are not reported. Segmentation (polygon) lines count as
  malformed.
- **Next:** Slice 4, `feat/small-objects`: tiny-box ratio, size histogram, in-box blur.

### Slice 4: Small-object stats (2026-11-07)
- **What:** `SmallObjectCheck` fills `stats`: a box-size histogram (<8, 8-16, 16-32, 32-96, 96+ px),
  `tiny_box_ratio` (boxes under 16 px) and `blur_summary`. Blur is the Laplacian variance of each
  box crop (boxes 8 px or larger); an image whose median score is under 100 gets a
  `blurry_objects` warning. NumPy added; OpenCV deliberately not (stack line in CLAUDE.md updated).
- **Why:** Tiny and blurry objects are what hurts small-object detectors, and the PRD wants them
  visible before training.
- **What I learned:** Labels are fractions, so pixel size needs the image size (read from the
  header only). Box size is the square root of its area. A flat area has Laplacian variance 0, so
  low variance means blurry; crops under 8 px are too noisy to score. Solid-colour test images
  count as blurry, so fixtures use seeded random noise. Stats live on the check object and
  `build_report` reads them, so the Check protocol stays unchanged.
- **Tests:** 74 passed, 4 symlink tests skipped locally (run in CI). ruff and `uv build` clean.
  A planted test checks the exact histogram, ratio, blur summary and the single warning.
- **Limits:** Thresholds (16 px, 100, 8 px) are placeholders not tuned on real data. Images are
  decoded a third time for blur; speed is untested until the 10k-image timing in Slice 8.
- **Next:** Slice 5, `feat/scoring`: four sub-scores, weighted overall, reasons, capped issues,
  generated JSON schema.

### Slice 5: Scoring + final report (2026-11-07)
- **What:** `scoring.py` scores four sections (Files, Labels, Duplicates, Small-object quality) from
  0 to 100 with plain-English reasons, plus a weighted overall score (0.25 / 0.35 / 0.15 / 0.25).
  Issues are capped at 100 per type; `issue_counts` keeps the true counts. `schema/report.schema.json`
  is generated from the Pydantic models with `uv run python -m dsc.schema`. The CLI prints the
  overall score. Milestone: the CLI works end to end.
- **Why:** The PRD wants a score a stranger can understand and trace back to specific problems.
- **What I learned:** An issue-based section score is `100 x (1 - weighted issues / images)`,
  clamped at 0. Scoring must run before the cap, or trimming the list would change the score.
  Weights come from severity with a few overrides, and unknown types fall back to severity. A test
  that regenerates the schema and compares it to the committed file stops the engine and viewer
  contract drifting.
- **Tests:** 91 passed, 4 symlink tests skipped locally (run in CI). ruff and `uv build` clean.
  End-to-end tests check exact section scores, the overall score and the cap.
- **Limits:** Weights, thresholds and the cap are placeholders, not tuned on real data. A dataset
  of genuinely tiny objects scores 0 in Small-object quality. All issues are held in memory until
  the end of the scan. Score is not validated against model accuracy.
- **Next:** Slice 6, `feat/viewer-core`: Vite/React shell, sample report, drag-and-drop, Zod
  validation, score and section cards.

### Slice 6: Viewer core (2026-11-08)
- **What:** The viewer loads a report from "Load sample report", drag-and-drop or a file chooser,
  validates it with Zod, and shows the overall score (Good / Needs work / Poor) plus a card per
  section with score, reason and issue count. Added `viewer/public/sample-report.json`, generated
  by the engine from the planted fixture. Zod 4.6.7 added.
- **Why:** Viewing the report is the product's second half; the PRD requires a stranger to open
  the site, click the sample and understand it.
- **What I learned:** TypeScript types vanish at runtime, so an untrusted report.json needs a
  runtime check (Zod), and `z.infer` keeps the type and the check in sync. React renders `{value}`
  as plain text, so no `dangerouslySetInnerHTML` is needed. `preventDefault` on dragover is what
  allows a drop. A visually hidden file input inside a label gives a keyboard and screen-reader
  path. Vitest has globals off, so testing-library needs an explicit `cleanup`. A test comparing
  field names with `schema/report.schema.json` keeps the engine and viewer contract honest.
- **Tests:** 25 viewer tests passed; ESLint, tsc and the Vite build clean. Also checked the sample
  report in a real browser. Engine unchanged.
- **Limits:** The sample is the 13-image fixture, not a real dataset. Score bands (80 / 50) and the
  20 MB limit are placeholders. No issue table or histogram yet. Not tried with a screen reader or
  at phone width.
- **Next:** Slice 7, `feat/viewer-issues`: filterable issue table, histogram, friendlier errors,
  plain-text rendering test.

### Slice 7: Viewer details (2026-11-08)
- **What:** The summary screen gets a filterable problems table (severity, type, file search;
  errors first; a notice with the true total when the report was capped), a box-size histogram
  drawn with Tailwind bars plus tiny-box and blur numbers, and load errors that carry a next-step
  hint. The file limit dropped from 20 MB to 5 MB. A plain-text rendering guard was added.
- **Why:** The PRD's problem list and histogram, and the rule that report.json is untrusted.
- **What I learned:** Keeping filtering in a pure function makes it testable without rendering.
  `Array.sort` is stable, so scan order survives within a severity. A `<table>` with a caption and
  header cells, labelled controls and an `aria-live` count make the table usable with a screen
  reader. Error hints are fixed strings so nothing from the untrusted file is echoed. A guard test
  is only trustworthy once it has been seen failing, so I planted a forbidden string to check it.
- **Tests:** 45 viewer tests passed; ESLint, tsc and the Vite build clean. Checked in a real
  browser at desktop and 375 px width (no horizontal page scroll). Engine unchanged.
- **Limits:** No pagination (the engine cap keeps it near 1,400 rows). Not tried with a screen
  reader or a real large report. Histogram is plain bars, not Recharts (CLAUDE.md stack updated).
- **Next:** Slice 8, `feat/deploy`: GitHub Pages deploy (Vite base path), README with the
  Roboflow-vs-COCO comparison, 10k-image timing test.

### Slice 8: Ship (2026-11-08)
- **What:** `deploy.yml` builds the viewer and publishes it to GitHub Pages on every push to main
  (Vite `base` is `/DQC/`). A slow, opt-in 10k-image timing test. MIT license. A one-off
  `scripts/coco_to_yolo.py`. A new `small_box_ratio` stat (share of boxes under 32 px, shown next to
  the tiny share but never scored) carried through the models, schema, Zod and the viewer. The README
  is filled in with a real cricket-ball vs COCO val2017 comparison and timings. Pages was enabled
  with the Actions source.
- **Why:** The PRD's success criteria: a live URL, a README a stranger can follow, a 10k-image timing
  and a real comparison.
- **What I learned:** A Pages site lives under `/<repo>/`, so Vite needs a base path or the page is
  blank. A `slow` marker keeps long tests out of normal runs. The profiler showed the first COCO scan
  was slow because Windows spends about 15 ms on each file's first open (20 images/s cold, 59 to 115
  warm), so always check where time goes before optimising. On the cricket-ball set no box is under
  16 px yet 53% are under 32 px, so the tiny share alone scored it a perfect 100; the under-32 px
  share is now shown beside it. Changing the 16 px threshold itself was rejected.
- **Tests:** engine 91 passed (4 symlink tests skipped locally, 1 slow test deselected); viewer 47
  passed; ruff, ESLint, tsc, `uv build` and the Vite build clean. 10,000 generated images scanned in
  241 s (target: under 600 s).
- **Results:** cricket ball 99.8 overall, COCO val2017 96.8 (see README). Two datasets and one run
  each: not enough to tune weights or thresholds.
- **Limits:** The first Pages deploy only happens after merge and is unverified. No laptop timing.
  Weights, the 16 px and blur thresholds and the score bands are still untuned.
- **Next:** MVP done per PRD once the live site is confirmed. Post-MVP: near-duplicate detection,
  train/val leakage, orphan labels, tuning on more datasets.

## Report lands in the dataset folder
- **What:** `dsc check <dataset>` now writes `<dataset>/report.json` by default; `-o` still overrides.
  An unwritable destination exits 1 with a hint to use `-o` instead of a traceback.
- **Why:** Users had to hunt for the report in whatever folder they ran the command from.
- **What I learned:** Writing happens after the scan, so the report is never scanned as part of the
  dataset. It adds one file to the dataset folder, which bends the "dataset is read-only" rule
  (nothing existing is modified or deleted); a read-only dataset needs `-o`.
- **Tests:** engine 93 passed, 4 skipped; ruff clean.
- **Next:** Decide whether a re-run should overwrite the old report (it does today).
