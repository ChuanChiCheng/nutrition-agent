from dataclasses import dataclass
from datetime import datetime
from typing import Literal


TaskCategory = Literal[
    "nutrition",
    "preparation",
    "addons",
    "meal_logging",
    "corrections",
    "queries",
    "unanswerable",
]
TaskLabel = Literal["edge", "unanswerable"]


@dataclass(frozen=True)
class ExpectedChange:
    op: Literal["insert", "update", "delete"]
    entity: str
    match: dict
    values: dict


@dataclass(frozen=True)
class EvalTask:
    id: str
    category: TaskCategory
    labels: set[TaskLabel]
    fixture: dict
    request: str
    scripted_answers: list[str]
    approval: Literal["approve", "reject"] | None
    expected_changes: list[ExpectedChange]
    required_order: list[dict]
    reply_rubric: list[str]


@dataclass(frozen=True)
class EvalConfig:
    now: datetime
    model_id: str
    reasoning_effort: str | None
    max_model_calls: int
    max_tool_calls: int
    max_clarifications: int
    max_output_tokens: int
    timeout_seconds: int
    judge_model_id: str
    judge_parameters: dict
    task_version: str


@dataclass(frozen=True)
class EpisodeResult:
    task_id: str
    controller: str
    repeat: int
    status: str
    reply: str | None
    trace: list[dict]
    interactions: list[dict]
    final_state: dict
    turns: int
    model_calls: int
    tool_calls: int
    input_tokens: int
    output_tokens: int
    latency_ms: int
    error: str | None


@dataclass(frozen=True)
class GradePart:
    passed: bool
    reasons: list[str]


@dataclass(frozen=True)
class EpisodeGrade:
    passed: bool
    state: GradePart
    order: GradePart
    reply: GradePart


@dataclass(frozen=True)
class ScoredEpisode:
    task: EvalTask
    episode: EpisodeResult
    grade: EpisodeGrade


@dataclass(frozen=True)
class SuiteResult:
    status: Literal["complete", "incomplete"]
    episodes: list[EpisodeResult]
    error: str | None = None
