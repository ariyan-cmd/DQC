from pathlib import Path

import pytest

from dsc.checks.labels import Box, parse_label_file


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
