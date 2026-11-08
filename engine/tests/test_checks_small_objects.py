from pathlib import Path

import numpy as np
from PIL import Image

from dsc.checks.small_objects import BLUR_THRESHOLD, SmallObjectCheck, bucket
from dsc.loader import Sample, resolve_root
from dsc.models import Issue


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
    assert stats.tiny_box_ratio == 2 / 5  # 5 and 10 px are under 16 px
    assert stats.small_box_ratio == 3 / 5  # 5, 10 and 20 px are under 32 px


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


def scan(
    tmp_path: Path, image: Image.Image, label_text: str
) -> tuple[SmallObjectCheck, list[Issue]]:
    root = resolve_root(tmp_path)
    image.save(root / "img.png")
    (root / "lbl.txt").write_text(label_text, encoding="utf-8")
    check = SmallObjectCheck(root)
    return check, check.check_sample(Sample(root / "img.png", root / "lbl.txt", ""))


def noise(size: int = 100) -> Image.Image:
    pixels = np.random.default_rng(0).integers(0, 256, (size, size, 3), dtype=np.uint8)
    return Image.fromarray(pixels)


def test_sharp_box_is_measured_and_not_flagged(tmp_path: Path) -> None:
    check, issues = scan(tmp_path, noise(), "0 0.5 0.5 0.5 0.5\n")
    assert issues == []
    summary = check.stats().blur_summary
    assert summary["boxes_measured"] == 1
    assert summary["blurry_ratio"] == 0.0
    assert summary["median_sharpness"] > BLUR_THRESHOLD


def test_flat_box_is_a_blurry_warning(tmp_path: Path) -> None:
    check, issues = scan(tmp_path, Image.new("RGB", (100, 100), (7, 7, 7)), "0 0.5 0.5 0.5 0.5\n")
    assert [(i.type, i.severity, i.section, i.file) for i in issues] == [
        ("blurry_objects", "warning", "Small-object quality", "img.png")
    ]
    assert check.stats().blur_summary["blurry_ratio"] == 1.0


def test_boxes_under_8_px_are_not_measured(tmp_path: Path) -> None:
    check, issues = scan(tmp_path, Image.new("RGB", (100, 100)), "0 0.5 0.5 0.07 0.07\n")
    assert issues == []
    assert check.stats().blur_summary == {}


def test_box_hanging_off_the_image_is_clipped_not_a_crash(tmp_path: Path) -> None:
    check, _ = scan(tmp_path, noise(), "0 0.95 0.95 0.4 0.4\n")  # 30 px of it is on the image
    assert check.stats().blur_summary["boxes_measured"] == 1


def test_box_almost_entirely_off_the_image_is_skipped(tmp_path: Path) -> None:
    check, _ = scan(tmp_path, noise(), "0 1.19 0.5 0.4 0.4\n")  # only 1 px column remains
    assert check.stats().blur_summary == {}


def test_truncated_image_keeps_size_stats_and_does_not_crash(tmp_path: Path) -> None:
    root = resolve_root(tmp_path)
    noise().save(root / "full.png")
    data = (root / "full.png").read_bytes()
    (root / "img.png").write_bytes(data[: len(data) // 2])
    (root / "lbl.txt").write_text("0 0.5 0.5 0.5 0.5\n", encoding="utf-8")
    check = SmallObjectCheck(root)
    assert check.check_sample(Sample(root / "img.png", root / "lbl.txt", "")) == []
    assert check.total == 1  # header was readable, pixels were not
    assert check.stats().blur_summary == {}
