from pathlib import Path

from dsc.checks.duplicates import DuplicateCheck
from dsc.loader import Sample, resolve_root


def test_only_later_copies_are_flagged(tmp_path: Path) -> None:
    root = resolve_root(tmp_path)
    (root / "a.png").write_bytes(b"same")
    (root / "b.png").write_bytes(b"other")
    (root / "c.png").write_bytes(b"same")
    check = DuplicateCheck(root)
    issues = [
        i
        for n in ("a.png", "b.png", "c.png")
        for i in check.check_sample(Sample(root / n, None, ""))
    ]
    assert [(i.type, i.section, i.file, i.detail) for i in issues] == [
        ("duplicate_image", "Duplicates", "c.png", "byte-identical to a.png")
    ]


def test_unreadable_file_is_skipped_not_a_crash(tmp_path: Path) -> None:
    root = resolve_root(tmp_path)
    assert DuplicateCheck(root).check_sample(Sample(root / "missing.png", None, "")) == []
