import math
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path


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
