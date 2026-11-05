# dsc: Dataset Readiness Checker

> Know if your object-detection dataset is safe to train on, before you burn hours of GPU time.

<!-- badges: CI status, license, Python version -->

**[Live viewer demo](#)** · [Sample report](#)

## Why
<!-- 3-4 sentences: your story, the research project, bad data wasting training runs. -->

## What it checks
| Section | Checks |
|---|---|
| Files | corrupt/unreadable images, tiny resolution |
| Labels | missing/empty label files, out-of-bounds and zero-size boxes, invalid class IDs |
| Duplicates | byte-identical images |
| Small-object quality | tiny-box ratio, box-size distribution, in-box blur (warning only) |

## Quick start
```bash
git clone <repo-url> && cd dataset-readiness/engine
uv sync
uv run dsc check /path/to/dataset -o report.json
```
Then open the [viewer](#) and drag in `report.json`. Your images never leave your machine.

## Supported dataset layouts
<!-- list the 3 layouts -->

## How the score works
<!-- weights table, penalty rule, why it is transparent -->

## Example: Roboflow cricket-ball dataset vs COCO val2017
<!-- results table + what you learned. Honest about limits. -->

## Limitations
- YOLO-format image datasets only (more formats planned)
- Exact duplicates only (near-duplicates planned)
- Blur check is a heuristic, shown as a warning, not a verdict
- The score is a guide: it is not yet validated against model accuracy

## Roadmap
<!-- link ROADMAP.md; near-duplicates and leakage next -->

## Development
<!-- engine and viewer commands, tests, lint -->

## Security
Read-only scanning, no uploads, report treated as untrusted in the viewer.

## License
<!-- MIT recommended -->