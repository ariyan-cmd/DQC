"""Writes schema/report.schema.json, the contract between the engine and the viewer.

Run from engine/:  uv run python -m dsc.schema
"""

import json
import sys
from pathlib import Path

from dsc.models import Report


def schema_text() -> str:
    return json.dumps(Report.model_json_schema(), indent=2) + "\n"


if __name__ == "__main__":
    out = Path(sys.argv[1] if len(sys.argv) > 1 else "../schema/report.schema.json")
    out.write_text(schema_text(), encoding="utf-8", newline="\n")
    print(f"wrote {out.name}")
