import pytest
from pydantic import ValidationError

from dsc.models import DatasetInfo, Issue, Report, Score


def make_report() -> Report:
    return Report(
        dataset=DatasetInfo(name="d", num_images=1, num_labels=0, classes=["a"], splits=[]),
        score=Score(overall=0, weights={}),
        issues=[Issue(type="t", severity="info", section="Files", file="a.png", detail="x")],
    )


def test_report_round_trips_through_json() -> None:
    report = make_report()
    assert Report.model_validate_json(report.model_dump_json()) == report


def test_schema_version_defaults_to_1() -> None:
    assert make_report().schema_version == "1"


def test_issue_rejects_unknown_severity() -> None:
    with pytest.raises(ValidationError):
        Issue(type="t", severity="fatal", section="Files", file="a.png", detail="x")
