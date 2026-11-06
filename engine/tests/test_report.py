from pathlib import Path

from make_fixture import make_dataset, plant_image_problems, plant_label_problems

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
