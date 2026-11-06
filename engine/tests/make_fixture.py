"""Builds tiny YOLO datasets on disk for tests.

Each split gets two images: `a` has a label file, `b` does not. Later slices plant
more problems (corrupt files, bad boxes) by extending this module.
"""

from pathlib import Path

from PIL import Image

LAYOUTS = ("images_labels", "split_first", "flat")
SPLITS = ("train", "val")
DATA_YAML = "names:\n  - cat\n  - dog\n"


def _write_split(images_dir: Path, labels_dir: Path, seed: int = 0) -> None:
    images_dir.mkdir(parents=True, exist_ok=True)
    labels_dir.mkdir(parents=True, exist_ok=True)
    # 64 px clears the tiny-image check; a per-split colour keeps files from being duplicates.
    Image.new("RGB", (64, 64), (40 * seed + 10, 0, 255)).save(images_dir / "a.png")
    Image.new("RGB", (64, 64), (40 * seed + 10, 255, 0)).save(images_dir / "b.png")
    (labels_dir / "a.txt").write_text("0 0.5 0.5 0.2 0.2\n", encoding="utf-8")


def make_dataset(root: Path, layout: str, data_yaml: str | None = DATA_YAML) -> Path:
    """Create a dataset in `root` using one of LAYOUTS and return `root`."""
    if layout == "images_labels":
        for seed, split in enumerate(SPLITS):
            _write_split(root / "images" / split, root / "labels" / split, seed)
    elif layout == "split_first":
        for seed, split in enumerate(SPLITS):
            _write_split(root / split / "images", root / split / "labels", seed)
    elif layout == "flat":
        _write_split(root / "images", root / "labels")
    else:
        raise ValueError(f"unknown layout: {layout}")
    if data_yaml is not None:
        (root / "data.yaml").write_text(data_yaml, encoding="utf-8")
    return root
