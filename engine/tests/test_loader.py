import inspect
from pathlib import Path

import pytest
from make_fixture import LAYOUTS, SPLITS, make_dataset

from dsc.loader import LayoutError, find_splits, iter_samples, resolve_root


@pytest.mark.parametrize("layout", LAYOUTS)
def test_all_layouts_load(tmp_path: Path, layout: str) -> None:
    root = resolve_root(make_dataset(tmp_path, layout))
    splits = find_splits(root)
    samples = list(iter_samples(splits))
    per_split = 2
    expected_splits = 1 if layout == "flat" else len(SPLITS)
    assert len(splits) == expected_splits
    assert len(samples) == per_split * expected_splits
    # image "a" has a label, image "b" does not
    assert sum(s.label is not None for s in samples) == expected_splits
    assert all((s.label is None) == (s.image.stem == "b") for s in samples)


def test_split_names(tmp_path: Path) -> None:
    root = resolve_root(make_dataset(tmp_path, "split_first"))
    assert [s.name for s in find_splits(root)] == sorted(SPLITS)


def test_iter_samples_is_lazy(tmp_path: Path) -> None:
    root = resolve_root(make_dataset(tmp_path, "flat"))
    assert inspect.isgenerator(iter_samples(find_splits(root)))


def test_unsupported_layout_is_an_error(tmp_path: Path) -> None:
    (tmp_path / "pictures").mkdir()
    with pytest.raises(LayoutError, match="not a supported layout"):
        find_splits(resolve_root(tmp_path))


def test_two_matching_layouts_is_an_error(tmp_path: Path) -> None:
    make_dataset(tmp_path, "images_labels")
    (tmp_path / "extra" / "images").mkdir(parents=True)
    (tmp_path / "extra" / "labels").mkdir()
    with pytest.raises(LayoutError, match="more than one layout"):
        find_splits(resolve_root(tmp_path))


def test_images_mixing_files_and_split_folders_is_an_error(tmp_path: Path) -> None:
    make_dataset(tmp_path, "images_labels")
    (tmp_path / "images" / "stray.png").write_bytes(b"")
    with pytest.raises(LayoutError, match="mixes"):
        find_splits(resolve_root(tmp_path))


def test_missing_folder_is_an_error(tmp_path: Path) -> None:
    with pytest.raises(LayoutError, match="not a folder"):
        resolve_root(tmp_path / "nope")
