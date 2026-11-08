from pathlib import Path

from make_fixture import (
    make_dataset,
    noise_image,
    plant_image_problems,
    plant_label_problems,
    plant_small_object_problems,
)

from dsc.report import build_report
from dsc.scoring import SECTION_WEIGHTS


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
    assert stats.tiny_box_ratio == 0.5  # 12.8 and 5 px are under 16
    assert stats.small_box_ratio == 0.75  # 12.8, 5 and 20 px are under 32; only 100 px is not
    # measured: a.png, soft, mid (small is under 8 px); only soft is blurry
    assert stats.blur_summary["boxes_measured"] == 3
    assert stats.blur_summary["blurry_ratio"] == 1 / 3


def test_planted_image_problems_produce_the_expected_scores(tmp_path: Path) -> None:
    root = make_dataset(tmp_path / "ds", "flat")
    plant_image_problems(root)  # 5 images; a.png has one 12.8 px (tiny) box
    report = build_report(root)
    got = {s.name: (s.score, s.issue_count) for s in report.sections}
    assert got == {
        "Files": (70.0, 2),  # (corrupt 1 + very small 0.5) / 5 images
        "Labels": (60.0, 4),  # 4 images without labels, 0.5 each
        "Duplicates": (80.0, 1),
        "Small-object quality": (0.0, 0),  # the only box is tiny
    }
    assert report.score.overall == 50.5  # 0.25*70 + 0.35*60 + 0.15*80 + 0.25*0
    assert report.score.weights == SECTION_WEIGHTS
    assert report.issue_counts == {
        "corrupt_image": 1,
        "tiny_resolution": 1,
        "duplicate_image": 1,
        "missing_label": 4,
    }


def test_issue_list_is_capped_but_scores_use_the_true_counts(tmp_path: Path) -> None:
    root = make_dataset(tmp_path / "ds", "flat")
    for n in range(120):  # 120 images with no label file
        noise_image(1000 + n).save(root / "images" / f"x{n}.png")
    report = build_report(root)
    assert report.issue_counts["missing_label"] == 121  # b.png plus the 120 new ones
    assert sum(i.type == "missing_label" for i in report.issues) == 100
    labels = next(s for s in report.sections if s.name == "Labels")
    assert labels.issue_count == 121
    assert labels.score == round(100 * (1 - 0.5 * 121 / 122), 1)
