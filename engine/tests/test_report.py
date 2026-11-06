from pathlib import Path

from make_fixture import make_dataset, plant_image_problems

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
