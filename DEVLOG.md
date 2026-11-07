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
