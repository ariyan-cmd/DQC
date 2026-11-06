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


def run(tmp_path: Path, text: str | None, classes: int = 2) -> list[Issue]:
    """Check one image `img.png` whose label is `lbl.txt` containing `text` (None = no label)."""
    root = resolve_root(tmp_path)
    label = None
    if text is not None:
        label = root / "lbl.txt"
        label.write_text(text, encoding="utf-8")
    return LabelCheck(root, classes).check_sample(Sample(root / "img.png", label, ""))


def kinds(issues: list[Issue]) -> list[tuple[str, str, str]]:
    return [(i.type, i.severity, i.file) for i in issues]


def test_missing_label_points_at_the_image(tmp_path: Path) -> None:
    assert kinds(run(tmp_path, None)) == [("missing_label", "warning", "img.png")]


@pytest.mark.parametrize("text", ["", "\n \n"])
def test_empty_label_is_info(tmp_path: Path, text: str) -> None:
    assert kinds(run(tmp_path, text)) == [("empty_label", "info", "lbl.txt")]


def test_valid_label_has_no_issues(tmp_path: Path) -> None:
    assert run(tmp_path, "0 0.5 0.5 0.2 0.2\n1 0.3 0.3 0.1 0.1\n") == []


@pytest.mark.parametrize(
    ("line", "expected"),
    [
        ("0 0.5 0.5 0.2", "malformed_label_line"),
        ("2 0.5 0.5 0.2 0.2", "invalid_class_id"),  # only classes 0 and 1 exist
        ("-1 0.5 0.5 0.2 0.2", "invalid_class_id"),
        ("0.5 0.5 0.5 0.2 0.2", "invalid_class_id"),
        ("0 0.5 0.5 0 0.2", "zero_size_box"),
        ("0 0.5 0.5 -0.1 0.2", "zero_size_box"),
        ("0 0.95 0.5 0.2 0.2", "box_out_of_bounds"),  # right edge at 1.05
        ("0 0.5 0.02 0.2 0.1", "box_out_of_bounds"),  # top edge at -0.03
        ("0 1.5 0.5 0.1 0.1", "box_out_of_bounds"),
    ],
)
def test_each_box_problem_is_reported(tmp_path: Path, line: str, expected: str) -> None:
    assert kinds(run(tmp_path, line + "\n")) == [(expected, "error", "lbl.txt")]


def test_box_touching_the_edges_is_fine(tmp_path: Path) -> None:
    assert run(tmp_path, "0 0.5 0.5 1 1\n0 0.1 0.1 0.2 0.2000000001\n") == []


def test_problems_are_grouped_per_type_with_count_and_first_line(tmp_path: Path) -> None:
    issues = run(tmp_path, "0 0.5 0.5 0.2 0.2\n0 0.5 0.5 0 0\nbad\n0 0.5 0.5 0 0\n")
    assert [(i.type, i.detail.split(": ")[1]) for i in issues] == [
        ("zero_size_box", "2 line(s), first at line 2"),
        ("malformed_label_line", "1 line(s), first at line 3"),
    ]


def test_without_class_list_only_the_id_shape_is_checked(tmp_path: Path) -> None:
    assert run(tmp_path, "99 0.5 0.5 0.2 0.2\n", classes=0) == []
    assert kinds(run(tmp_path, "-1 0.5 0.5 0.2 0.2\n", classes=0)) == [
        ("invalid_class_id", "error", "lbl.txt")
    ]


def test_unreadable_label_is_an_error_not_a_crash(tmp_path: Path) -> None:
    root = resolve_root(tmp_path)
    (root / "lbl.txt").write_bytes(b"\xff\xfe\x00\x80")
    issues = LabelCheck(root, 2).check_sample(Sample(root / "img.png", root / "lbl.txt", ""))
    assert kinds(issues) == [("malformed_label_line", "error", "lbl.txt")]
