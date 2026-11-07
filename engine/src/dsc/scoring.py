from collections import Counter

from dsc.checks.small_objects import TINY_PX
from dsc.models import Issue, Score, Section, Stats

# The four report sections, in display order, with their share of the overall score.
# Placeholder weights: arbitrary until tuned on real datasets.
SECTION_WEIGHTS = {"Files": 0.25, "Labels": 0.35, "Duplicates": 0.15, "Small-object quality": 0.25}

# How much one issue counts against its section. By severity, with a few exceptions.
SEVERITY_WEIGHT = {"error": 1.0, "warning": 0.5, "info": 0.0}
WEIGHT_OVERRIDES = {
    "duplicate_image": 1.0,  # a warning, but every copy is wasted compute
    "blurry_objects": 0.0,  # blur is a noisy heuristic, so it is shown but never scored
    "data_yaml_unreadable": 0.0,  # config problems, not dataset problems
    "data_yaml_no_names": 0.0,
}

# Wording for the reason text. Counts are per issue, and one label file is one issue.
PHRASES = {
    "corrupt_image": "corrupt images",
    "image_too_large": "oversized images",
    "tiny_resolution": "very small images",
    "path_outside_root": "paths outside the dataset folder (skipped)",
    "duplicate_image": "duplicate images",
    "missing_label": "images without a label file",
    "empty_label": "empty label files",
    "malformed_label_line": "label files with malformed lines",
    "invalid_class_id": "label files with invalid class ids",
    "box_out_of_bounds": "label files with boxes outside the image",
    "zero_size_box": "label files with zero-size boxes",
    "data_yaml_missing": "missing data.yaml",
    "data_yaml_unreadable": "unreadable data.yaml",
    "data_yaml_no_names": "data.yaml without class names",
}


def issue_weight(issue: Issue) -> float:
    return WEIGHT_OVERRIDES.get(issue.type, SEVERITY_WEIGHT[issue.severity])


def _issue_based(name: str, issues: list[Issue], num_images: int) -> Section:
    """Score = 100 minus the share of images hit, so 5 bad images in 100 scores 95."""
    mine = [i for i in issues if i.section == name]
    penalty = sum(issue_weight(i) for i in mine) / num_images
    counts = Counter(i.type for i in mine)
    problems = [f"{PHRASES.get(t, t)}: {n}" for t, n in counts.most_common()]
    reason = "; ".join(problems) if problems else "no problems found"
    return Section(
        name=name,
        score=round(100 * (1 - min(1.0, penalty)), 1),
        reason=f"{reason} ({num_images} images)",
        issue_count=len(mine),
    )


def _small_objects(name: str, issues: list[Issue], stats: Stats) -> Section:
    boxes = sum(stats.box_size_histogram.values())
    if boxes == 0:
        return Section(name=name, score=0.0, reason="no valid boxes found", issue_count=0)
    reason = f"{stats.tiny_box_ratio:.0%} of {boxes} boxes are under {TINY_PX} px"
    blur = stats.blur_summary
    if blur:
        reason += f"; {blur['blurry_ratio']:.0%} of measured boxes look blurry (not scored)"
    return Section(
        name=name,
        score=round(100 * (1 - stats.tiny_box_ratio), 1),
        reason=reason,
        issue_count=sum(i.section == name for i in issues),
    )


def score_sections(issues: list[Issue], stats: Stats, num_images: int) -> list[Section]:
    """Score from the full, uncapped issue list so the issue cap never changes a score."""
    if num_images == 0:
        return [
            Section(name=n, score=0.0, reason="no images found", issue_count=0)
            for n in SECTION_WEIGHTS
        ]
    sections = []
    for name in SECTION_WEIGHTS:
        if name == "Small-object quality":
            sections.append(_small_objects(name, issues, stats))
        else:
            sections.append(_issue_based(name, issues, num_images))
    return sections


def overall_score(sections: list[Section]) -> Score:
    total = sum(SECTION_WEIGHTS[s.name] * s.score for s in sections)
    return Score(overall=round(total, 1), weights=dict(SECTION_WEIGHTS))
