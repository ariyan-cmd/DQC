# PRD: Dataset Readiness Checker (`dsc`)

## Problem
Object-detection datasets often contain corrupt files, exact duplicates, broken labels, and
tiny or blurry objects. These silently waste training runs, and there is no quick, explainable
pre-training check focused on small objects.

## User
An ML student or researcher training a YOLO-style detector on a public or self-collected
dataset who wants to know if the data is safe to train on before spending compute.

## User stories (MVP)
1. Run `dsc check ./my_dataset` and get a `report.json` without uploading data anywhere.
2. See an overall readiness score plus four sub-scores, each with a plain-English reason.
3. See the exact files behind every problem so I can fix them.
4. See how many boxes are tiny and how blurry the objects are.
5. As a visitor, open the live site, click "Load sample report", and understand the product
   in 30 seconds.
6. Drag my own `report.json` into the viewer to browse it.

## Screens
- **Landing/upload:** pitch, "Load sample report", drag-and-drop, CLI quick-start snippet.
- **Report summary:** big overall score, four section cards (Files, Labels, Duplicates,
  Small-object quality) with score and reason.
- **Problem list:** filterable table (type, severity, file, detail) + box-size histogram.

## Data
No database. `report.json` only, versioned:
```json
{
  "schema_version": "1",
  "dataset": {"name": "", "num_images": 0, "num_labels": 0, "classes": [], "splits": []},
  "score": {"overall": 0, "weights": {}},
  "sections": [{"name": "", "score": 0, "reason": "", "issue_count": 0}],
  "issues": [{"type": "", "severity": "error|warning|info", "section": "", "file": "", "detail": ""}],
  "stats": {"box_size_histogram": {}, "tiny_box_ratio": 0, "blur_summary": {}}
}
```

## Supported dataset layouts (MVP)
1. `images/<split>/` + `labels/<split>/`
2. `<split>/images/` + `<split>/labels/` (Roboflow export)
3. flat `images/` + `labels/`
Anything else: a clear error, never a guess. `data.yaml` is read with `yaml.safe_load` for
class names.

## Functional requirements
- Read-only: never modify or delete user files.
- Streams files one at a time (10k+ images without loading all into memory).
- One bad file never crashes the scan; it becomes an issue.
- Paths in the report are relative with forward slashes. Issue lists capped per type
  (true counts kept).

## Security
- Viewer treats `report.json` as untrusted: validate with Zod, render as plain text only.
- No server, no uploads in the MVP.
- Path containment, safe YAML parsing, and decompression-bomb protection in the engine.

## Success criteria ("done")
1. A stranger opens the live URL, clicks "Load sample report", and sees a score and problem
   list with no instructions.
2. A stranger follows the README alone, runs `dsc check` on a YOLO dataset, and gets a valid
   `report.json`.
3. Engine tests on a fixture dataset with planted problems find exactly those problems.
4. A 10k-image scan finishes in under 10 minutes on a laptop CPU.
5. README includes a real comparison: a Roboflow cricket-ball dataset vs COCO val2017.

## Non-goals
Training, accounts, database, non-image data, modifying user files, GPU work, COCO/VOC
labels, near-duplicate detection (first post-MVP slice).