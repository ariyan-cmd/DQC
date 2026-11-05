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
