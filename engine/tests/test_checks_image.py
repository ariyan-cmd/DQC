from pathlib import Path

import pytest
from PIL import Image

from dsc.checks.image import ImageCheck
from dsc.loader import Sample, resolve_root


def run(tmp_path: Path, name: str) -> list[tuple[str, str]]:
    root = resolve_root(tmp_path)
    issues = ImageCheck(root).check_sample(Sample(root / name, None, ""))
    assert all(i.file == name for i in issues)
    return [(i.type, i.severity) for i in issues]


def save(tmp_path: Path, name: str, size: tuple[int, int]) -> None:
    Image.new("RGB", size, (1, 2, 3)).save(tmp_path / name)


def test_good_image_has_no_issues(tmp_path: Path) -> None:
    save(tmp_path, "ok.png", (64, 64))
    assert run(tmp_path, "ok.png") == []


def test_tiny_image_is_a_warning(tmp_path: Path) -> None:
    save(tmp_path, "tiny.png", (4, 100))
    assert run(tmp_path, "tiny.png") == [("tiny_resolution", "warning")]


def test_truncated_image_is_corrupt(tmp_path: Path) -> None:
    save(tmp_path, "full.png", (64, 64))
    data = (tmp_path / "full.png").read_bytes()
    (tmp_path / "cut.png").write_bytes(data[: len(data) // 2])
    assert run(tmp_path, "cut.png") == [("corrupt_image", "error")]


def test_non_image_with_image_extension_is_corrupt(tmp_path: Path) -> None:
    (tmp_path / "fake.png").write_text("not an image", encoding="utf-8")
    assert run(tmp_path, "fake.png") == [("corrupt_image", "error")]


@pytest.mark.parametrize("pixel_limit", [100, 3000])  # 64*64=4096 is >2x and then 1x-2x
def test_decompression_bomb_guard_is_an_error(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, pixel_limit: int
) -> None:
    save(tmp_path, "big.png", (64, 64))
    monkeypatch.setattr(Image, "MAX_IMAGE_PIXELS", pixel_limit)
    assert run(tmp_path, "big.png") == [("image_too_large", "error")]
