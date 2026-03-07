from typing import List, Literal, Optional
from pydantic import BaseModel
from typing_extensions import TypedDict


class Issue(BaseModel):
    line_ref: str
    issue_type: str
    severity: Literal["critical", "warning", "suggestion"]
    explanation: str


class ReviewerOutput(BaseModel):
    language: str
    issues: List[Issue]
    summary: str


class FixEntry(BaseModel):
    issue_ref: str
    change_made: str


class FixerOutput(BaseModel):
    fixed_code: str
    changelog: List[FixEntry]


class DimensionScore(BaseModel):
    score: int
    notes: str


class EvaluatorOutput(BaseModel):
    correctness: DimensionScore
    completeness: DimensionScore
    code_quality: DimensionScore
    overall_score: int
    decision: Literal["pass", "fail", "retry"]
    feedback: str


class AgentState(TypedDict):
    code: str
    language: str
    reviewer_output: Optional[ReviewerOutput]
    fixer_output: Optional[FixerOutput]
    evaluator_output: Optional[EvaluatorOutput]
    iteration: int
    final_status: str
