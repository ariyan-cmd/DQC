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


BOUNDS_TOLERANCE = 1e-6  # exporters round coordinates, so allow a hair over the edge
DESCRIPTIONS = {
    "malformed_label_line": "not 'class x y w h' numbers",
    "invalid_class_id": "class id is not a whole number within the class list",
    "zero_size_box": "box width or height is 0 or negative",
    "box_out_of_bounds": "box extends outside the image",
}


def _out_of_bounds(box: Box) -> bool:
    low, high = -BOUNDS_TOLERANCE, 1 + BOUNDS_TOLERANCE
    return (
        box.x - box.w / 2 < low
        or box.x + box.w / 2 > high
        or box.y - box.h / 2 < low
        or box.y + box.h / 2 > high
    )


class LabelCheck:
    """Flags missing, empty and unreadable label files, and bad lines and boxes inside them."""

    def __init__(self, root: Path, num_classes: int) -> None:
        self.root = root
        self.num_classes = num_classes

    def _bad_class(self, cls: float) -> bool:
        # num_classes is 0 when data.yaml gave no names; then only the id's shape is checked.
        return not cls.is_integer() or cls < 0 or (0 < self.num_classes <= cls)

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
        # One issue per problem type per file keeps a badly broken file from flooding the report.
        found: dict[str, list[int]] = {}
        for number, box in lines:
            if box is None:
                found.setdefault("malformed_label_line", []).append(number)
                continue
            if self._bad_class(box.cls):
                found.setdefault("invalid_class_id", []).append(number)
            if box.w <= 0 or box.h <= 0:
                found.setdefault("zero_size_box", []).append(number)
            elif _out_of_bounds(box):
                found.setdefault("box_out_of_bounds", []).append(number)
        return [
            self._issue(
                sample.label,
                kind,
                "error",
                f"{DESCRIPTIONS[kind]}: {len(nums)} line(s), first at line {nums[0]}",
            )
            for kind, nums in found.items()
        ]

    def finalize(self) -> list[Issue]:
        return []
