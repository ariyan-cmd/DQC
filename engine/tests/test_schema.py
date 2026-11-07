import json
from pathlib import Path

from dsc.schema import schema_text

SCHEMA_FILE = Path(__file__).resolve().parents[2] / "schema" / "report.schema.json"


def test_committed_schema_matches_the_models() -> None:
    committed = SCHEMA_FILE.read_text(encoding="utf-8")
    assert committed == schema_text(), (
        "models changed: run `cd engine && uv run python -m dsc.schema`"
    )


def test_schema_describes_the_report_contract() -> None:
    schema = json.loads(schema_text())
    assert {
        "schema_version",
        "dataset",
        "score",
        "sections",
        "issues",
        "issue_counts",
        "stats",
    } <= set(schema["properties"])
    assert schema["$defs"]["Issue"]["properties"]["severity"]["enum"] == [
        "error",
        "warning",
        "info",
    ]
