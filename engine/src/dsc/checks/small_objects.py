import math
import statistics
from pathlib import Path

import numpy as np
from numpy.typing import NDArray
from PIL import Image

from dsc.checks.labels import Box, parse_label_file
from dsc.loader import Sample, relpath
from dsc.models import Issue, Stats

TINY_PX = 16  # placeholder: a box whose typical side is under this is "tiny"
# Upper edge of each bucket in pixels; 32 and 96 are the COCO small/medium/large cut points.
BUCKET_EDGES = [(8, "<8"), (16, "8-16"), (32, "16-32"), (96, "32-96")]
LAST_BUCKET = "96+"
BLUR_MIN_PX = 8  # smaller crops give a noisy sharpness score, so they are not measured
BLUR_THRESHOLD = 100.0  # placeholder: Laplacian variance below this counts as blurry


def box_size_px(box: Box, width: int, height: int) -> float:
    """Typical side length: the square root of the box area in pixels."""
    return math.sqrt(box.w * width * box.h * height)


def bucket(size: float) -> str:
    return next((label for edge, label in BUCKET_EDGES if size < edge), LAST_BUCKET)


def laplacian_variance(gray: NDArray[np.float32]) -> float:
    """Sharpness score: edges make the Laplacian vary a lot, a blurry area keeps it near zero."""
    centre = gray[1:-1, 1:-1]
    laplacian = gray[:-2, 1:-1] + gray[2:, 1:-1] + gray[1:-1, :-2] + gray[1:-1, 2:] - 4 * centre
    return float(laplacian.var())


class SmallObjectCheck:
    """Collects box-size statistics and in-box sharpness (blur is a warning, never an error)."""

    def __init__(self, root: Path) -> None:
        self.root = root
        self.histogram = dict.fromkeys([label for _, label in BUCKET_EDGES] + [LAST_BUCKET], 0)
        self.total = 0
        self.tiny = 0
        self.scores: list[float] = []  # one sharpness score per measured box

    def _valid_boxes(self, label: Path) -> list[Box]:
        try:
            boxes = [box for _, box in parse_label_file(label)]
        except (OSError, UnicodeDecodeError):
            return []  # LabelCheck reports unreadable labels
        # Malformed and zero-size boxes are LabelCheck's job; they have no size to measure.
        return [b for b in boxes if b is not None and b.w > 0 and b.h > 0]

    def _sharpness(self, img: Image.Image, boxes: list[Box]) -> list[float]:
        width, height = img.size
        big = [b for b in boxes if min(b.w * width, b.h * height) >= BLUR_MIN_PX]
        limit = Image.MAX_IMAGE_PIXELS
        if not big or (limit and width * height > limit):
            return []  # nothing to measure, or ImageCheck already rejects this size
        gray = np.asarray(img.convert("L"))
        scores = []
        for b in big:
            x0, x1 = round((b.x - b.w / 2) * width), round((b.x + b.w / 2) * width)
            y0, y1 = round((b.y - b.h / 2) * height), round((b.y + b.h / 2) * height)
            crop = gray[max(0, y0) : min(height, y1), max(0, x0) : min(width, x1)]
            if crop.shape[0] >= 3 and crop.shape[1] >= 3:  # boxes mostly off-image can be empty
                scores.append(laplacian_variance(crop.astype(np.float32)))
        return scores

    def check_sample(self, sample: Sample) -> list[Issue]:
        if sample.label is None:
            return []
        boxes = self._valid_boxes(sample.label)
        if not boxes:
            return []
        scores: list[float] = []
        try:
            with Image.open(sample.image) as img:  # open() reads the header only
                for box in boxes:
                    size = box_size_px(box, *img.size)
                    self.histogram[bucket(size)] += 1
                    self.total += 1
                    self.tiny += size < TINY_PX
                scores = self._sharpness(img, boxes)
        except Exception:  # unreadable images are reported by ImageCheck
            return []
        self.scores.extend(scores)
        if scores and (median := statistics.median(scores)) < BLUR_THRESHOLD:
            return [
                Issue(
                    type="blurry_objects",
                    severity="warning",
                    section="Small-object quality",
                    file=relpath(self.root, sample.image),
                    detail=f"median sharpness {median:.0f} over {len(scores)} box(es) "
                    f"is below {BLUR_THRESHOLD:.0f}",
                )
            ]
        return []

    def finalize(self) -> list[Issue]:
        return []

    def stats(self) -> Stats:
        ratio = self.tiny / self.total if self.total else 0.0
        blur: dict[str, float] = {}
        if self.scores:
            blur = {
                "boxes_measured": float(len(self.scores)),
                "median_sharpness": statistics.median(self.scores),
                "blurry_ratio": sum(s < BLUR_THRESHOLD for s in self.scores) / len(self.scores),
            }
        return Stats(box_size_histogram=self.histogram, tiny_box_ratio=ratio, blur_summary=blur)
