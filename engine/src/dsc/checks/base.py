from typing import Protocol

from dsc.loader import Sample
from dsc.models import Issue


class Check(Protocol):
    """check_sample runs once per image; finalize runs after the last one."""

    def check_sample(self, sample: Sample) -> list[Issue]: ...

    def finalize(self) -> list[Issue]: ...
