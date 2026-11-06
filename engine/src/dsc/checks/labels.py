import math
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path

from dsc.loader import Sample, relpath
from dsc.models import Issue, Severity


@dataclass(frozen=True)
class Box:
    """One YOLO label line: class id, then centre x/y and width/height as 0-1 fractions."""

    cls: float  # float so a bad id like 1.5 is parsed and reported, not lost
    x: float
    y: float
    w: float
    h: float


def _parse_line(parts: list[str]) -> Box | None:
    if len(parts) != 5:  # also rejects segmentation polygons (out of MVP scope)
        return None
    try:
        values = [float(p) for p in parts]
    except ValueError:
        return None
    # float() accepts "nan" and "inf"; neither is a usable coordinate
    return Box(*values) if all(math.isfinite(v) for v in values) else None


def parse_label_file(path: Path) -> Iterator[tuple[int, Box | None]]:
    """Yield (line number, box) for each non-blank line; box is None if the line is malformed.

    Raises OSError or UnicodeDecodeError if the file cannot be read as text.
    """
    with path.open(encoding="utf-8") as f:
        for number, line in enumerate(f, start=1):
            parts = line.split()
            if parts:
                yield number, _parse_line(parts)


class LabelCheck:
    """Flags missing, empty and unreadable label files (box checks are added below)."""

    def __init__(self, root: Path) -> None:
        self.root = root

    def _issue(self, path: Path, kind: str, severity: Severity, detail: str) -> Issue:
        return Issue(
            type=kind,
            severity=severity,
            section="Labels",
            file=relpath(self.root, path),
            detail=detail,
        )

    def check_sample(self, sample: Sample) -> list[Issue]:
        if sample.label is None:
            # Valid for background images, so only a warning.
            return [self._issue(sample.image, "missing_label", "warning", "no label file")]
        try:
            lines = list(parse_label_file(sample.label))
        except (OSError, UnicodeDecodeError):
            detail = "label file could not be read as text"
            return [self._issue(sample.label, "malformed_label_line", "error", detail)]
        if not lines:
            return [self._issue(sample.label, "empty_label", "info", "label file has no boxes")]
        return []

    def finalize(self) -> list[Issue]:
        return []
