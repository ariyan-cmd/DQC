# Dataset Readiness Checker (`dsc`)

Local-first Python CLI that scans a YOLO-format image dataset and writes an explainable
readiness `report.json`; a static React viewer displays it. Read PRD.md and ROADMAP.md first.
The owner is a student learning as they build: explain new concepts in 1-2 lines, keep diffs small.

## Stack
- engine/: Python 3.13, Typer, Pillow, NumPy (no OpenCV: blur is a few lines of NumPy), PyYAML, Pydantic v2, uv, pytest, ruff
- viewer/: Vite, React, TypeScript, Tailwind, Recharts, Zod, Vitest
- No backend, database, or auth. Hosting: GitHub Pages. CI: GitHub Actions.

## Structure
- engine/src/dsc/: cli.py, loader.py, models.py, scoring.py, report.py, checks/
- engine/tests/: pytest + make_fixture.py (tiny dataset with planted problems)
- viewer/src/: App.tsx, schema.ts, lib/, components/
- schema/report.schema.json: generated from Pydantic; the engine/viewer contract
- Supported layouts: images/<split> + labels/<split>; <split>/images + <split>/labels; flat
- DEVLOG.md: one entry per finished slice

## Commands
- Engine (cd engine): `uv sync` | `uv run dsc check <dataset> -o report.json`
- Test: `uv run pytest` | Lint: `uv run ruff check . && uv run ruff format --check .`
- Build: `uv build`
- Viewer (cd viewer): `npm install` | `npm run dev` | `npm test` | `npm run lint` | `npm run build`

## Code style
- Python: type hints everywhere, pathlib (never string paths), small functions, ruff-formatted
- TypeScript: strict mode, no `any`, function components
- Every check implements the Check protocol (check_sample, finalize) and has a pytest test
- Comments explain why, not what

## Git workflow
- One ROADMAP slice at a time on `feat/<name>`; never commit directly to main
- Conventional Commits: `feat(engine): ...`, `fix(viewer): ...`, `test:`, `docs:`, `chore:`
- Before finishing a slice: tests and lint pass, then append a DEVLOG.md entry
  (date, what, why, what was learned, tests, next)
- Explain the diff to the owner before merging; no features outside the current slice
- Ask before adding any dependency

## Secrets and security
- Never commit secrets; keep .env in .gitignore; no tokens, passwords or absolute paths in
  code, logs, reports or DEVLOG
- Dataset access is READ-ONLY: never modify or delete user files
- Resolve paths and refuse to leave the dataset root (watch symlinks)
- Parse YAML with yaml.safe_load only
- Keep Pillow decompression-bomb protection on; a bad file becomes an issue, never a crash
- report.json stores relative, forward-slash paths only
- Viewer treats report.json as untrusted: validate with Zod, render values as plain text,
  never use dangerouslySetInnerHTML