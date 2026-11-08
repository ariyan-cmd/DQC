"""PRD success criterion 4: a 10k-image scan finishes in under 10 minutes on a laptop CPU.

Slow, so it is skipped by default. Run it with:  uv run pytest -m slow -s
"""

import shutil
import time
from pathlib import Path

import pytest
from make_fixture import make_big_dataset

from dsc.report import build_report

IMAGES = 10_000
LIMIT_SECONDS = 600


@pytest.mark.slow
def test_10k_image_scan_finishes_in_under_10_minutes(tmp_path: Path) -> None:
    root = make_big_dataset(tmp_path / "big", IMAGES)
    try:
        start = time.perf_counter()
        report = build_report(root)
        elapsed = time.perf_counter() - start
    finally:
        shutil.rmtree(root)  # pytest keeps old temp dirs; this one is gigabytes
    print(f"\nscanned {IMAGES} images in {elapsed:.0f}s ({IMAGES / elapsed:.0f} images/s)")
    assert report.dataset.num_images == IMAGES
    assert report.issue_counts.get("corrupt_image", 0) == 0
    assert elapsed < LIMIT_SECONDS
