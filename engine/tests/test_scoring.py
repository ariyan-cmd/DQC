from dsc.models import Issue, Severity, Stats
from dsc.scoring import SECTION_WEIGHTS, cap_issues, overall_score, score_sections

GOOD_STATS = Stats(box_size_histogram={"96+": 10}, tiny_box_ratio=0.0)


def issue(kind: str, section: str, severity: Severity = "error") -> Issue:
    return Issue(type=kind, severity=severity, section=section, file="x", detail="d")


def scores(issues: list[Issue], stats: Stats = GOOD_STATS, images: int = 100) -> dict[str, float]:
    return {s.name: s.score for s in score_sections(issues, stats, images)}


def test_clean_dataset_scores_100_everywhere() -> None:
    sections = score_sections([], GOOD_STATS, 100)
    assert [s.name for s in sections] == list(SECTION_WEIGHTS)
    assert all(s.score == 100 for s in sections)
    assert sections[0].reason == "no problems found (100 images)"
    assert overall_score(sections).overall == 100


def test_five_corrupt_images_in_a_hundred_scores_95() -> None:
    issues = [issue("corrupt_image", "Files")] * 5
    assert scores(issues)["Files"] == 95
    reason = score_sections(issues, GOOD_STATS, 100)[0].reason
    assert reason == "corrupt images: 5 (100 images)"


def test_warnings_count_half_and_info_counts_nothing() -> None:
    issues = [issue("missing_label", "Labels", "warning")] * 4 + [
        issue("empty_label", "Labels", "info")
    ] * 10
    assert scores(issues, images=10)["Labels"] == 80  # 4 x 0.5 / 10


def test_duplicates_are_warnings_that_still_count_fully() -> None:
    assert scores([issue("duplicate_image", "Duplicates", "warning")] * 10)["Duplicates"] == 90


def test_blur_warning_is_counted_but_does_not_lower_the_score() -> None:
    issues = [issue("blurry_objects", "Small-object quality", "warning")]
    section = score_sections(issues, GOOD_STATS, 10)[3]
    assert section.score == 100
    assert section.issue_count == 1


def test_unknown_issue_type_falls_back_to_its_severity() -> None:
    assert scores([issue("future_check", "Files", "warning")], images=2)["Files"] == 75


def test_score_never_goes_below_zero() -> None:
    assert scores([issue("corrupt_image", "Files")] * 50, images=10)["Files"] == 0


def test_issue_count_is_the_true_total_for_the_section() -> None:
    issues = [issue("corrupt_image", "Files")] * 3 + [issue("tiny_resolution", "Files", "warning")]
    assert score_sections(issues, GOOD_STATS, 100)[0].issue_count == 4


def test_small_object_score_is_one_minus_tiny_ratio_and_blur_is_not_scored() -> None:
    stats = Stats(
        box_size_histogram={"<8": 25, "96+": 75},
        tiny_box_ratio=0.25,
        small_box_ratio=0.5,
        blur_summary={"boxes_measured": 10.0, "median_sharpness": 50.0, "blurry_ratio": 0.9},
    )
    section = score_sections([], stats, 100)[3]
    assert section.score == 75  # the small (under 32 px) share does not change the score
    assert section.reason == (
        "25% of 100 boxes are under 16 px (50% are under 32 px); "
        "90% of measured boxes look blurry (not scored)"
    )


def test_no_boxes_scores_zero() -> None:
    section = score_sections([], Stats(), 100)[3]
    assert (section.score, section.reason) == (0, "no valid boxes found")


def test_empty_dataset_scores_zero_with_a_reason() -> None:
    sections = score_sections([], Stats(), 0)
    assert all((s.score, s.reason) == (0, "no images found") for s in sections)
    assert overall_score(sections).overall == 0


def test_cap_keeps_the_first_100_per_type_and_the_true_counts() -> None:
    many = [
        Issue(type="corrupt_image", severity="error", section="Files", file=f"{n}.png", detail="d")
        for n in range(150)
    ]
    few = [issue("tiny_resolution", "Files", "warning")] * 3
    kept, counts = cap_issues(many[:50] + few + many[50:])
    assert counts == {"corrupt_image": 150, "tiny_resolution": 3}
    assert [i.file for i in kept if i.type == "corrupt_image"] == [f"{n}.png" for n in range(100)]
    assert sum(i.type == "tiny_resolution" for i in kept) == 3


def test_overall_is_the_weighted_average_and_lists_its_weights() -> None:
    sections = score_sections([issue("corrupt_image", "Files")] * 50, GOOD_STATS, 100)
    score = overall_score(sections)
    assert sections[0].score == 50
    assert score.overall == 87.5  # 100 - 0.25 * 50
    assert score.weights == SECTION_WEIGHTS
    assert sum(score.weights.values()) == 1
