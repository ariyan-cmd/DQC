from pathlib import Path

from dsc.checks.base import Check
from dsc.checks.duplicates import DuplicateCheck
from dsc.checks.image import ImageCheck
from dsc.checks.labels import LabelCheck
from dsc.checks.small_objects import SmallObjectCheck
from dsc.loader import find_splits, iter_samples, read_classes, resolve_root
from dsc.models import DatasetInfo, Issue, Report, Score


def build_report(dataset: Path) -> Report:
    """Scan a dataset and describe it. Scoring and checks arrive in later slices."""
    root = resolve_root(dataset)
    splits = find_splits(root)
    issues: list[Issue] = []
    classes = read_classes(root, issues)
    small_objects = SmallObjectCheck(root)
    checks: list[Check] = [
        ImageCheck(root),
        DuplicateCheck(root),
        LabelCheck(root, len(classes)),
        small_objects,
    ]
    num_images = num_labels = 0
    for sample in iter_samples(root, splits, issues):
        num_images += 1
        num_labels += sample.label is not None
        for check in checks:
            issues.extend(check.check_sample(sample))
    for check in checks:
        issues.extend(check.finalize())
    return Report(
        dataset=DatasetInfo(
            name=root.name,
            num_images=num_images,
            num_labels=num_labels,
            classes=classes,
            splits=[s.name for s in splits if s.name],
        ),
        # Placeholder until Slice 5 adds real scoring.
        score=Score(overall=0, weights={}),
        issues=issues,
        stats=small_objects.stats(),
    )


def write_report(report: Report, output: Path) -> None:
    output.write_text(report.model_dump_json(indent=2), encoding="utf-8")
