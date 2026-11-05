from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path

import yaml

from dsc.models import Issue, Severity

IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}


class LayoutError(Exception):
    """The dataset folder is not a supported layout (or not a folder at all)."""


@dataclass(frozen=True)
class Split:
    name: str  # "" for the flat layout
    images_dir: Path
    labels_dir: Path  # may not exist; images then simply have no label


@dataclass(frozen=True)
class Sample:
    image: Path
    label: Path | None
    split: str


def resolve_root(path: Path) -> Path:
    root = path.resolve()
    if not root.is_dir():
        raise LayoutError("dataset path is not a folder")
    return root


def _subdirs(path: Path) -> list[Path]:
    return sorted(p for p in path.iterdir() if p.is_dir())


def _images_labels_layout(root: Path) -> list[Split] | None:
    """Layouts 1 and 3: root/images + root/labels, with or without split folders."""
    images, labels = root / "images", root / "labels"
    if not (images.is_dir() and labels.is_dir()):
        return None
    subdirs = _subdirs(images)
    if not subdirs:
        return [Split("", images, labels)]
    if any(p.is_file() for p in images.iterdir()):
        raise LayoutError("images/ mixes split folders and image files")
    return [Split(d.name, d, labels / d.name) for d in subdirs]


def _split_first_layout(root: Path) -> list[Split] | None:
    """Layout 2 (Roboflow): root/<split>/images + root/<split>/labels."""
    splits = [
        Split(d.name, d / "images", d / "labels")
        for d in _subdirs(root)
        if (d / "images").is_dir() and (d / "labels").is_dir()
    ]
    return splits or None


def find_splits(root: Path) -> list[Split]:
    """Pick the one matching layout; never guess when zero or several match."""
    matches = [m for m in (_images_labels_layout(root), _split_first_layout(root)) if m]
    if len(matches) != 1:
        reason = "matches more than one layout" if matches else "is not a supported layout"
        raise LayoutError(f"dataset {reason}; expected images/+labels/ or <split>/images+labels")
    return matches[0]


def _yaml_issue(kind: str, severity: Severity, detail: str) -> Issue:
    return Issue(type=kind, severity=severity, section="Labels", file="data.yaml", detail=detail)


def _class_names(names: object) -> list[str] | None:
    """YOLO writes names as a list, or as a {0: 'cat', 1: 'dog'} mapping."""
    if isinstance(names, list):
        return [str(n) for n in names]
    if isinstance(names, dict) and all(isinstance(k, int) for k in names):
        return [str(names[k]) for k in sorted(names)]
    return None


def read_classes(root: Path, issues: list[Issue]) -> list[str]:
    """Class names from data.yaml; problems become issues, never crashes."""
    path = root / "data.yaml"
    if not path.is_file():
        issues.append(_yaml_issue("data_yaml_missing", "info", "data.yaml not found"))
        return []
    try:
        # safe_load only builds plain data; yaml.load could run code from the file.
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (yaml.YAMLError, OSError, UnicodeDecodeError):
        issues.append(
            _yaml_issue("data_yaml_unreadable", "warning", "data.yaml could not be parsed")
        )
        return []
    classes = _class_names(data.get("names") if isinstance(data, dict) else None)
    if classes is None:
        issues.append(_yaml_issue("data_yaml_no_names", "warning", "data.yaml has no usable names"))
        return []
    return classes


def iter_samples(splits: list[Split]) -> Iterator[Sample]:
    """Yield one image at a time so big datasets never sit in memory."""
    for split in splits:
        for image in sorted(split.images_dir.iterdir()):
            if image.suffix.lower() not in IMAGE_EXTS or not image.is_file():
                continue
            label = split.labels_dir / f"{image.stem}.txt"
            yield Sample(image, label if label.is_file() else None, split.name)
