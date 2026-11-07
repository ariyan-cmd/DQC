import math
from pathlib import Path

from PIL import Image

from dsc.checks.labels import Box, parse_label_file
from dsc.loader import Sample
from dsc.models import Issue, Stats

TINY_PX = 16  # placeholder: a box whose typical side is under this is "tiny"
# Upper edge of each bucket in pixels; 32 and 96 are the COCO small/medium/large cut points.
BUCKET_EDGES = [(8, "<8"), (16, "8-16"), (32, "16-32"), (96, "32-96")]
LAST_BUCKET = "96+"


def box_size_px(box: Box, width: int, height: int) -> float:
    """Typical side length: the square root of the box area in pixels."""
    return math.sqrt(box.w * width * box.h * height)


def bucket(size: float) -> str:
    return next((label for edge, label in BUCKET_EDGES if size < edge), LAST_BUCKET)


class SmallObjectCheck:
    """Collects box-size statistics. Blur is measured per box where the box is big enough."""

    def __init__(self, root: Path) -> None:
        self.root = root
        self.histogram = dict.fromkeys([label for _, label in BUCKET_EDGES] + [LAST_BUCKET], 0)
        self.total = 0
        self.tiny = 0

    def _valid_boxes(self, label: Path) -> list[Box]:
        try:
            boxes = [box for _, box in parse_label_file(label)]
        except (OSError, UnicodeDecodeError):
            return []  # LabelCheck reports unreadable labels
        # Malformed and zero-size boxes are LabelCheck's job; they have no size to measure.
        return [b for b in boxes if b is not None and b.w > 0 and b.h > 0]

    def check_sample(self, sample: Sample) -> list[Issue]:
        if sample.label is None:
            return []
        boxes = self._valid_boxes(sample.label)
        if not boxes:
            return []
        try:
            with Image.open(sample.image) as img:  # header only: no pixel decoding yet
                width, height = img.size
        except Exception:  # unreadable images are reported by ImageCheck
            return []
        for box in boxes:
            size = box_size_px(box, width, height)
            self.histogram[bucket(size)] += 1
            self.total += 1
            self.tiny += size < TINY_PX
        return []

    def finalize(self) -> list[Issue]:
        return []

    def stats(self) -> Stats:
        ratio = self.tiny / self.total if self.total else 0.0
        return Stats(box_size_histogram=self.histogram, tiny_box_ratio=ratio)
