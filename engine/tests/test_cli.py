import json
from pathlib import Path

import pytest
from make_fixture import LAYOUTS, make_dataset
from typer.testing import CliRunner

from dsc.cli import app
from dsc.models import Report


@pytest.mark.parametrize("layout", LAYOUTS)
def test_check_writes_valid_report(tmp_path: Path, layout: str) -> None:
    dataset = make_dataset(tmp_path / "ds", layout)
    out = tmp_path / "report.json"
    result = CliRunner().invoke(app, ["check", str(dataset), "-o", str(out)])
    assert result.exit_code == 0
    report = Report.model_validate_json(out.read_text(encoding="utf-8"))
    assert report.dataset.name == "ds"
    assert report.dataset.classes == ["cat", "dog"]
    assert report.dataset.num_images == (2 if layout == "flat" else 4)
    # image "b" has no label in the fixture; nothing else is wrong
    assert {i.type for i in report.issues} == {"missing_label"}


def test_report_has_no_absolute_paths(tmp_path: Path) -> None:
    dataset = make_dataset(tmp_path / "ds", "flat", data_yaml=None)
    out = tmp_path / "report.json"
    CliRunner().invoke(app, ["check", str(dataset), "-o", str(out)])
    assert str(tmp_path) not in out.read_text(encoding="utf-8")
    assert json.loads(out.read_text(encoding="utf-8"))["issues"][0]["file"] == "data.yaml"


def test_check_does_not_modify_dataset(tmp_path: Path) -> None:
    dataset = make_dataset(tmp_path / "ds", "split_first")
    before = sorted((p.relative_to(dataset), p.stat().st_mtime_ns) for p in dataset.rglob("*"))
    CliRunner().invoke(app, ["check", str(dataset), "-o", str(tmp_path / "r.json")])
    after = sorted((p.relative_to(dataset), p.stat().st_mtime_ns) for p in dataset.rglob("*"))
    assert before == after


def test_unsupported_layout_exits_2_without_report(tmp_path: Path) -> None:
    (tmp_path / "ds" / "pictures").mkdir(parents=True)
    out = tmp_path / "report.json"
    result = CliRunner().invoke(app, ["check", str(tmp_path / "ds"), "-o", str(out)])
    assert result.exit_code == 2
    assert "not a supported layout" in result.output
    assert str(tmp_path) not in result.output
    assert not out.exists()
