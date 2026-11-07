from pathlib import Path

from make_fixture import (
    make_dataset,
    plant_image_problems,
    plant_label_problems,
    plant_small_object_problems,
)

from dsc.report import build_report


def test_scan_finds_exactly_the_planted_image_problems(tmp_path: Path) -> None:
    root = make_dataset(tmp_path / "ds", "flat")
    plant_image_problems(root)
    report = build_report(root)
    # label issues (planted images have no labels) are covered by the label test
    found = sorted((i.type, i.section, i.file) for i in report.issues if i.section != "Labels")
    assert found == [
        ("corrupt_image", "Files", "images/corrupt.png"),
        ("duplicate_image", "Duplicates", "images/dup.png"),
        ("tiny_resolution", "Files", "images/tiny.png"),
    ]
    assert report.dataset.num_images == 5


def test_scan_finds_exactly_the_planted_label_problems(tmp_path: Path) -> None:
    root = make_dataset(tmp_path / "ds", "flat")
    plant_label_problems(root)
    report = build_report(root)
    found = sorted((i.type, i.section, i.file) for i in report.issues)
    assert found == [
        ("box_out_of_bounds", "Labels", "labels/outside.txt"),
        ("empty_label", "Labels", "labels/empty.txt"),
        ("invalid_class_id", "Labels", "labels/badclass.txt"),
        ("malformed_label_line", "Labels", "labels/malformed.txt"),
        ("missing_label", "Labels", "images/b.png"),  # from the base fixture
        ("zero_size_box", "Labels", "labels/zero.txt"),
    ]


def test_scan_finds_exactly_the_planted_small_object_problems(tmp_path: Path) -> None:
    root = make_dataset(tmp_path / "ds", "flat")
    plant_small_object_problems(root)
    report = build_report(root)
    small = [(i.type, i.file) for i in report.issues if i.section == "Small-object quality"]
    assert small == [("blurry_objects", "images/soft.png")]
    # boxes: a.png 12.8 px (base fixture), small 5 px, soft 100 px, mid 20 px
    stats = report.stats
    assert stats.box_size_histogram == {"<8": 1, "8-16": 1, "16-32": 1, "32-96": 0, "96+": 1}
    assert stats.tiny_box_ratio == 0.5
    # measured: a.png, soft, mid (small is under 8 px); only soft is blurry
    assert stats.blur_summary["boxes_measured"] == 3
    assert stats.blur_summary["blurry_ratio"] == 1 / 3
