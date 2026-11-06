from pathlib import Path

import pytest

from dsc.checks.labels import Box, LabelCheck, parse_label_file
from dsc.loader import Sample, resolve_root
from dsc.models import Issue


def parse(tmp_path: Path, text: str) -> list[tuple[int, Box | None]]:
    path = tmp_path / "x.txt"
    path.write_text(text, encoding="utf-8")
    return list(parse_label_file(path))


def test_parses_valid_lines_and_skips_blank_ones(tmp_path: Path) -> None:
    assert parse(tmp_path, "0 0.5 0.5 0.2 0.1\n\n  \n1 0.1 0.2 0.3 0.4\n") == [
        (1, Box(0, 0.5, 0.5, 0.2, 0.1)),
        (4, Box(1, 0.1, 0.2, 0.3, 0.4)),
    ]


@pytest.mark.parametrize(
    "line",
    [
        "0 0.5 0.5 0.2",
        "0 0.5 0.5 0.2 0.1 0.3",
        "a 0.5 0.5 0.2 0.1",
        "0 nan 0.5 0.2 0.1",
        "0 inf 0 1 1",
    ],
)
def test_malformed_lines_are_none(tmp_path: Path, line: str) -> None:
    assert parse(tmp_path, line) == [(1, None)]


def test_empty_file_yields_nothing(tmp_path: Path) -> None:
    assert parse(tmp_path, "\n") == []


def test_non_text_file_raises(tmp_path: Path) -> None:
    path = tmp_path / "bin.txt"
    path.write_bytes(b"\xff\xfe\x00\x80")
    with pytest.raises(UnicodeDecodeError):
        list(parse_label_file(path))


def run(tmp_path: Path, text: str | None) -> list[Issue]:
    """Check one image `img.png` whose label is `lbl.txt` containing `text` (None = no label)."""
    root = resolve_root(tmp_path)
    label = None
    if text is not None:
        label = root / "lbl.txt"
        label.write_text(text, encoding="utf-8")
    return LabelCheck(root).check_sample(Sample(root / "img.png", label, ""))


def kinds(issues: list[Issue]) -> list[tuple[str, str, str]]:
    return [(i.type, i.severity, i.file) for i in issues]


def test_missing_label_points_at_the_image(tmp_path: Path) -> None:
    assert kinds(run(tmp_path, None)) == [("missing_label", "warning", "img.png")]


@pytest.mark.parametrize("text", ["", "\n \n"])
def test_empty_label_is_info(tmp_path: Path, text: str) -> None:
    assert kinds(run(tmp_path, text)) == [("empty_label", "info", "lbl.txt")]


def test_valid_label_has_no_issues(tmp_path: Path) -> None:
    assert run(tmp_path, "0 0.5 0.5 0.2 0.2\n1 0.3 0.3 0.1 0.1\n") == []


def test_unreadable_label_is_an_error_not_a_crash(tmp_path: Path) -> None:
    root = resolve_root(tmp_path)
    (root / "lbl.txt").write_bytes(b"\xff\xfe\x00\x80")
    issues = LabelCheck(root).check_sample(Sample(root / "img.png", root / "lbl.txt", ""))
    assert kinds(issues) == [("malformed_label_line", "error", "lbl.txt")]
