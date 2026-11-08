"""One-off helper: turn COCO val2017 into a YOLO-format dataset that `dsc check` can scan.

Not part of the dsc product (COCO labels are out of scope for the engine). It reads the COCO
files and never changes them; everything is written to a new folder, as a flat layout:
    <out>/images/*.jpg, <out>/labels/*.txt, <out>/data.yaml

Boxes are converted as they are: crowd regions are skipped, but nothing else is clipped or
dropped, so `dsc` sees exactly what the annotations say.

Usage:  python scripts/coco_to_yolo.py <instances_val2017.json> <val2017 folder> <out folder>
"""

import argparse
import json
import shutil
from pathlib import Path


def convert(annotations: Path, images_dir: Path, out: Path) -> tuple[int, int]:
    if out.exists() and any(out.iterdir()):
        raise SystemExit("output folder is not empty; choose a new one")
    data = json.loads(annotations.read_text(encoding="utf-8"))
    categories = sorted(data["categories"], key=lambda c: c["id"])
    class_index = {c["id"]: i for i, c in enumerate(categories)}
    images = {im["id"]: im for im in data["images"]}
    lines: dict[int, list[str]] = {image_id: [] for image_id in images}

    for ann in data["annotations"]:
        if ann.get("iscrowd"):  # a crowd is one region covering many objects, not one object
            continue
        im = images[ann["image_id"]]
        x, y, w, h = ann["bbox"]  # COCO: top-left corner plus size, in pixels
        W, H = im["width"], im["height"]
        centre_x, centre_y = (x + w / 2) / W, (y + h / 2) / H
        lines[im["id"]].append(
            f"{class_index[ann['category_id']]} {centre_x:.6f} {centre_y:.6f} {w / W:.6f} {h / H:.6f}"
        )

    (out / "images").mkdir(parents=True)
    (out / "labels").mkdir()
    for image_id, im in images.items():
        name = Path(im["file_name"])
        shutil.copy2(images_dir / name, out / "images" / name.name)
        # An empty label file is YOLO's way of saying "background image, no objects".
        body = "\n".join(lines[image_id]) + ("\n" if lines[image_id] else "")
        (out / "labels" / f"{name.stem}.txt").write_text(body, encoding="utf-8")

    names = json.dumps([c["name"] for c in categories])  # a JSON list is valid YAML
    (out / "data.yaml").write_text(f"names: {names}\n", encoding="utf-8")
    return len(images), sum(len(v) for v in lines.values())


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("annotations", type=Path)
    parser.add_argument("images", type=Path)
    parser.add_argument("out", type=Path)
    args = parser.parse_args()
    n_images, n_boxes = convert(args.annotations, args.images, args.out)
    print(f"wrote {n_images} images and {n_boxes} boxes")
