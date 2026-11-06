import hashlib
from pathlib import Path

from dsc.loader import Sample, relpath
from dsc.models import Issue


class DuplicateCheck:
    """Flags images whose bytes are identical to an earlier image (exact, not near, copies)."""

    def __init__(self, root: Path) -> None:
        self.root = root
        self.first_seen: dict[str, str] = {}  # sha256 -> relative path of the first copy

    def check_sample(self, sample: Sample) -> list[Issue]:
        digest = hashlib.sha256()
        try:
            with sample.image.open("rb") as f:
                while chunk := f.read(1 << 20):  # 1 MiB at a time keeps memory flat
                    digest.update(chunk)
        except OSError:
            return []  # unreadable files are reported by ImageCheck
        rel = relpath(self.root, sample.image)
        first = self.first_seen.setdefault(digest.hexdigest(), rel)
        if first == rel:
            return []
        return [
            Issue(
                type="duplicate_image",
                severity="warning",
                section="Duplicates",
                file=rel,
                detail=f"byte-identical to {first}",
            )
        ]

    def finalize(self) -> list[Issue]:
        return []
