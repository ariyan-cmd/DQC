import inspect
from pathlib import Path

import pytest
from make_fixture import LAYOUTS, SPLITS, make_dataset

from dsc.loader import LayoutError, find_splits, iter_samples, read_classes, resolve_root
from dsc.models import Issue


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


def _classes(tmp_path: Path, yaml_text: str | None) -> tuple[list[str], list[Issue]]:
    root = resolve_root(make_dataset(tmp_path, "flat", data_yaml=yaml_text))
    issues: list[Issue] = []
    return read_classes(root, issues), issues


def test_classes_from_list(tmp_path: Path) -> None:
    assert _classes(tmp_path, "names: [cat, dog]\n") == (["cat", "dog"], [])


def test_classes_from_numbered_mapping(tmp_path: Path) -> None:
    assert _classes(tmp_path, "names:\n  1: dog\n  0: cat\n") == (["cat", "dog"], [])


def test_missing_data_yaml_is_an_info_issue(tmp_path: Path) -> None:
    classes, issues = _classes(tmp_path, None)
    assert classes == []
    assert [(i.type, i.severity) for i in issues] == [("data_yaml_missing", "info")]


@pytest.mark.parametrize("text", ["names: [", "just a string", "names: 5"])
def test_bad_data_yaml_is_a_warning(tmp_path: Path, text: str) -> None:
    classes, issues = _classes(tmp_path, text)
    assert classes == []
    assert [i.severity for i in issues] == ["warning"]


def test_yaml_cannot_run_code(tmp_path: Path) -> None:
    marker = tmp_path / "pwned.txt"
    path_tag = "!!python/object/apply:pathlib.Path"
    evil = f'names: {path_tag}.touch [{path_tag} ["{marker.as_posix()}"]]\n'
    classes, issues = _classes(tmp_path, evil)
    assert classes == []
    assert issues[0].type == "data_yaml_unreadable"
    assert not marker.exists()


def test_missing_folder_is_an_error(tmp_path: Path) -> None:
    with pytest.raises(LayoutError, match="not a folder"):
        resolve_root(tmp_path / "nope")
