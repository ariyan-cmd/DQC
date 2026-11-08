# dsc: Dataset Readiness Checker

> Know if your object-detection dataset is safe to train on, before you burn hours of GPU time.

[![CI](https://github.com/ariyan-cmd/DQC/actions/workflows/ci.yml/badge.svg)](https://github.com/ariyan-cmd/DQC/actions/workflows/ci.yml)
![License: MIT](https://img.shields.io/badge/license-MIT-blue)
![Python 3.13](https://img.shields.io/badge/python-3.13-blue)

**[Live viewer demo](https://ariyan-cmd.github.io/DQC/)** · [Sample report](https://ariyan-cmd.github.io/DQC/sample-report.json)

## Why
Object-detection datasets often hide corrupt files, exact duplicates, broken labels and tiny or
blurry objects. These silently waste training runs, and there is no quick, explainable check
before training that looks at small objects in particular. `dsc` scans a YOLO-format dataset
locally, writes a `report.json` with an overall readiness score and four sub-scores that each give
a plain-English reason, and lists the exact files behind every problem.

## What it checks
| Section | Checks |
|---|---|
| Files | corrupt/unreadable images, oversized images (decompression-bomb guard), tiny resolution |
| Labels | missing/empty label files, malformed lines, invalid class IDs, out-of-bounds and zero-size boxes |
| Duplicates | byte-identical images (SHA-256) |
| Small-object quality | tiny-box ratio, share of boxes under 32 px, box-size histogram, in-box blur (shown, never scored) |

## Quick start
```bash
git clone https://github.com/ariyan-cmd/DQC.git && cd DQC/engine
uv sync
uv run dsc check /path/to/dataset -o report.json
```
`uv` installs the right Python (3.13) for you. Then open the [viewer](https://ariyan-cmd.github.io/DQC/)
and drag in `report.json`, or press "Load sample report" first to see what a report looks like.
Your images never leave your machine: the engine runs locally and the viewer only reads the JSON.

## Supported dataset layouts
```
1. images/<split>/ + labels/<split>/      2. <split>/images/ + <split>/labels/      3. images/ + labels/
   (images/train, labels/train)              (Roboflow export: train/images)           (flat, no splits)
```
Anything else, or a folder that matches more than one layout, stops with a clear error instead of a
guess. Class names are read from `data.yaml` (with `yaml.safe_load`).

## How the score works
Every issue has a weight, and each section's score is the share of images left unaffected:

```
section score = 100 x (1 - min(1, sum of issue weights / number of images))
overall       = weighted average of the four section scores
```

| Issue weight | Applies to |
|---|---|
| 1.0 | errors: corrupt or oversized image, malformed line, invalid class ID, out-of-bounds or zero-size box, path outside the dataset; and duplicate images |
| 0.5 | warnings: very small image, image without a label file |
| 0 | info and hints: empty label file, blurry objects, `data.yaml` problems |

| Section | Share of overall | How it is scored |
|---|---|---|
| Files | 25% | issue weights above |
| Labels | 35% | issue weights above |
| Duplicates | 15% | issue weights above |
| Small-object quality | 25% | `100 x (1 - tiny box ratio)`; a box is tiny under 16 px; the share under 32 px (COCO's "small") and blur are shown but not scored |

A dataset with no images scores 0 everywhere, and so does one with no valid boxes in Small-object
quality. The report lists at most 100 issues per type but keeps the true counts, and scores always use
the true counts. The weights, the 16 px threshold, the blur threshold and the viewer's Good / Needs
work / Poor bands (80 and 50) are untuned starting points, so treat the score as a guide.

## Example: Roboflow cricket-ball dataset vs COCO val2017
Two real datasets, one scan each with `dsc check`:
[cricket ball](https://universe.roboflow.com/oliver-harding/cricket-ball-fi5pe/dataset/1) (Roboflow
Universe, by Oliver Harding, CC BY 4.0, YOLO export) and the 5,000-image COCO val2017 set. COCO's
labels are JSON, so `scripts/coco_to_yolo.py` converted them first: crowd regions are skipped, nothing
else is clipped or dropped, and the 48 images with no objects get an empty label file.

| | Cricket ball | COCO val2017 |
|---|---|---|
| Images / classes | 478 / 1 | 5,000 / 80 |
| Boxes | 478 | 36,335 |
| **Overall score** | **99.8** | **96.8** |
| Files / Labels | 100 / 100 | 100 / 100 |
| Duplicates | 99.0 (5 exact copies) | 100 |
| Small-object quality | 100.0 | 87.4 |
| Boxes under 16 px (scored) | 0% | 12.6% |
| Boxes under 32 px (shown, not scored) | 52.7% | 31.5% |
| Boxes that look blurry (hint) | 60% | 1.4% |

What this shows, and what it does not:
- Both datasets are clean on files and labels: no corrupt images, invalid class IDs or out-of-bounds boxes.
  COCO's 48 empty label files are valid "background" images and cost nothing.
- The 5 cricket-ball duplicates come from Roboflow's augmentation, which exports several variants of a photo.
- **The tiny-box share alone hides how small the cricket balls are.** None is under 16 px, so that
  section scores 100, yet 53% of the boxes are under 32 px, against 32% for COCO. That is why the report
  prints the under-32 px share next to the score.
- Blur flags 60% of cricket-ball boxes and 1.4% of COCO's. The flagged boxes are small, smooth objects,
  so size and content are mixed into this number. It stays a hint and is never scored.
- This is a demonstration of the report, not a ranking. COCO is 80 classes and mostly larger objects,
  and the score says nothing about how hard either dataset is to learn. Two datasets and one run each
  is far too little to tune the weights or thresholds.

## Performance
- **10,000 images:** 241 s (41 images/s) on 10,000 generated 640x480 JPEGs, so the "under 10 minutes"
  goal is met. Measured on a Windows desktop with 24 logical CPUs; the engine itself is single-threaded.
- **Real photos:** the 5,000 COCO images took 44 to 85 s on repeat scans (59 to 115 images/s), so 10,000
  real photos is roughly 1.5 to 3 minutes. The very first scan of freshly downloaded files took 4 min 4 s
  (20 images/s) because Windows spends about 15 ms checking each file the first time it is opened.
- I did not measure a laptop. Run `uv run pytest -m slow -s` from `engine/` to time your own machine.

## Limitations
- YOLO-format image datasets only (more formats planned)
- Exact duplicates only (near-duplicates planned)
- Label files that have no matching image are not reported yet
- Segmentation (polygon) label lines count as malformed; only box labels are supported
- Blur is a heuristic, shown as a hint, not a verdict, and is noisy on small boxes
- The score is a guide: it is not validated against model accuracy

## Roadmap
See [ROADMAP.md](ROADMAP.md). Next: near-duplicate detection and train/val leakage checks.

## Development
```bash
# engine (from engine/)
uv sync
uv run pytest                       # fast tests
uv run pytest -m slow -s            # 10k-image timing test
uv run ruff check . && uv run ruff format --check .
uv run python -m dsc.schema         # regenerate ../schema/report.schema.json

# viewer (from viewer/)
npm install
npm run dev | npm test | npm run lint | npm run build
```
`schema/report.schema.json` is generated from the engine's models and is the contract the viewer
checks against. `viewer/public/sample-report.json` was produced by the engine from the planted-problem
test fixture.

## Security
- Read-only scanning: dataset files are never modified, and no paths outside the dataset folder are read
- No uploads and no server; the viewer treats `report.json` as untrusted (validated with Zod, shown as plain text)
- Safe YAML parsing and Pillow's decompression-bomb protection stay on; a bad file becomes an issue, never a crash

## License
[MIT](LICENSE)
