from pathlib import Path

from PIL import Image

from dsc.checks.small_objects import SmallObjectCheck, bucket
from dsc.loader import Sample, resolve_root


def run(tmp_path: Path, label_text: str | None, size: int = 100) -> SmallObjectCheck:
    """Scan one `size`x`size` image `img.png` with the given label text."""
    root = resolve_root(tmp_path)
    Image.new("RGB", (size, size), (9, 9, 9)).save(root / "img.png")
    label = None
    if label_text is not None:
        label = root / "lbl.txt"
        label.write_text(label_text, encoding="utf-8")
    check = SmallObjectCheck(root)
    check.check_sample(Sample(root / "img.png", label, ""))
    return check


def test_bucket_edges() -> None:
    assert [bucket(s) for s in (0, 7.9, 8, 15.9, 16, 31.9, 32, 95.9, 96, 500)] == [
        "<8", "<8", "8-16", "8-16", "16-32", "16-32", "32-96", "32-96", "96+", "96+",
    ]  # fmt: skip


def test_histogram_and_tiny_ratio(tmp_path: Path) -> None:
    labels = (
        "0 0.5 0.5 0.05 0.05\n"  # 5 px
        "0 0.5 0.5 0.10 0.10\n"  # 10 px
        "0 0.5 0.5 0.20 0.20\n"  # 20 px
        "0 0.5 0.5 0.50 0.50\n"  # 50 px
        "0 0.5 0.5 1.00 1.00\n"  # 100 px
        "bad line\n"  # malformed: not counted
        "0 0.5 0.5 0 0.2\n"  # zero-size: not counted
    )
    stats = run(tmp_path, labels).stats()
    assert stats.box_size_histogram == {"<8": 1, "8-16": 1, "16-32": 1, "32-96": 1, "96+": 1}
    assert stats.tiny_box_ratio == 2 / 5


def test_size_uses_pixels_not_fractions(tmp_path: Path) -> None:
    # the same 0.1 fraction is 10 px on a 100 px image but 50 px on a 500 px image
    assert run(tmp_path, "0 0.5 0.5 0.1 0.1\n", size=500).stats().tiny_box_ratio == 0.0


def test_no_boxes_means_zero_ratio(tmp_path: Path) -> None:
    for text in (None, "", "bad\n"):
        assert run(tmp_path, text).stats().tiny_box_ratio == 0.0


def test_unreadable_image_is_skipped_without_crashing(tmp_path: Path) -> None:
    root = resolve_root(tmp_path)
    (root / "img.png").write_text("not an image", encoding="utf-8")
    (root / "lbl.txt").write_text("0 0.5 0.5 0.1 0.1\n", encoding="utf-8")
    check = SmallObjectCheck(root)
    assert check.check_sample(Sample(root / "img.png", root / "lbl.txt", "")) == []
    assert check.stats().tiny_box_ratio == 0.0
