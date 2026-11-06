import warnings
from pathlib import Path

from PIL import Image

from dsc.loader import Sample, relpath
from dsc.models import Issue, Severity

MIN_SIDE = 32  # placeholder threshold in pixels; tune on real datasets


class ImageCheck:
    """Flags files Pillow cannot decode, oversized (bomb-like) files and tiny images."""

    def __init__(self, root: Path) -> None:
        self.root = root

    def _issue(self, sample: Sample, kind: str, severity: Severity, detail: str) -> Issue:
        return Issue(
            type=kind,
            severity=severity,
            section="Files",
            file=relpath(self.root, sample.image),
            detail=detail,
        )

    def check_sample(self, sample: Sample) -> list[Issue]:
        try:
            # Pillow only warns between 1x and 2x its pixel limit; make that an error too.
            with warnings.catch_warnings():
                warnings.simplefilter("error", Image.DecompressionBombWarning)
                with Image.open(sample.image) as img:
                    width, height = img.size
                    img.load()  # full decode: open() alone misses truncated files
        except (Image.DecompressionBombError, Image.DecompressionBombWarning):
            return [self._issue(sample, "image_too_large", "error", "too many pixels; skipped")]
        except Exception:  # any decode failure is a bad file, never a crash
            return [self._issue(sample, "corrupt_image", "error", "image could not be decoded")]
        if min(width, height) < MIN_SIDE:
            detail = f"{width}x{height} px is below the {MIN_SIDE} px minimum"
            return [self._issue(sample, "tiny_resolution", "warning", detail)]
        return []

    def finalize(self) -> list[Issue]:
        return []
