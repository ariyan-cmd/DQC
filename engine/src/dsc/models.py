from typing import Literal

from pydantic import BaseModel, Field

# Pydantic models validate data and turn into JSON; they define the report.json contract.
Severity = Literal["error", "warning", "info"]


class Issue(BaseModel):
    type: str
    severity: Severity
    section: str
    file: str  # relative, forward-slash path
    detail: str


class DatasetInfo(BaseModel):
    name: str
    num_images: int
    num_labels: int
    classes: list[str]
    splits: list[str]


class Score(BaseModel):
    overall: float
    weights: dict[str, float]


class Section(BaseModel):
    name: str
    score: float
    reason: str
    issue_count: int


class Stats(BaseModel):
    box_size_histogram: dict[str, int] = Field(default_factory=dict)
    tiny_box_ratio: float = 0.0  # share of boxes under 16 px; this one drives the score
    small_box_ratio: float = 0.0  # share under 32 px (COCO "small"); shown, never scored
    blur_summary: dict[str, float] = Field(default_factory=dict)


class Report(BaseModel):
    schema_version: str = "1"
    dataset: DatasetInfo
    score: Score
    sections: list[Section] = Field(default_factory=list)
    issues: list[Issue] = Field(default_factory=list)  # capped per type
    issue_counts: dict[str, int] = Field(default_factory=dict)  # true count per type, pre-cap
    stats: Stats = Field(default_factory=Stats)
