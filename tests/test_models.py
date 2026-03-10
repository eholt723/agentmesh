"""
Unit tests for Pydantic models in models.py.

Verifies schema validation, enum constraints, and TypedDict structure
without touching the LLM or network.
"""

import pytest
from pydantic import ValidationError

from models import (
    AgentState,
    DimensionScore,
    EvaluatorOutput,
    FixEntry,
    FixerOutput,
    Issue,
    ReviewerOutput,
)


# ------------------------------
# Issue
# ------------------------------

class TestIssue:
    def test_valid_severities(self):
        for sev in ("critical", "warning", "suggestion"):
            issue = Issue(line_ref="L1", issue_type="bug", severity=sev, explanation="test")
            assert issue.severity == sev

    def test_invalid_severity_raises(self):
        with pytest.raises(ValidationError):
            Issue(line_ref="L1", issue_type="bug", severity="blocker", explanation="test")

    def test_missing_required_field_raises(self):
        with pytest.raises(ValidationError):
            Issue(line_ref="L1", issue_type="bug", severity="critical")  # missing explanation


# ------------------------------
# ReviewerOutput
# ------------------------------

class TestReviewerOutput:
    def test_valid_construction(self, sample_reviewer_output):
        assert sample_reviewer_output.language == "python"
        assert len(sample_reviewer_output.issues) == 1
        assert sample_reviewer_output.issues[0].severity == "critical"

    def test_empty_issues_list(self):
        ro = ReviewerOutput(language="javascript", issues=[], summary="No issues found")
        assert ro.issues == []

    def test_multiple_issues(self):
        issues = [
            Issue(line_ref="L3", issue_type="security", severity="critical", explanation="SQL injection"),
            Issue(line_ref="L10", issue_type="style", severity="suggestion", explanation="Use f-string"),
        ]
        ro = ReviewerOutput(language="python", issues=issues, summary="Two issues found")
        assert len(ro.issues) == 2
        assert ro.issues[0].severity == "critical"
        assert ro.issues[1].severity == "suggestion"


# ------------------------------
# FixerOutput
# ------------------------------

class TestFixerOutput:
    def test_valid_construction(self, sample_fixer_output):
        assert "def divide" in sample_fixer_output.fixed_code
        assert len(sample_fixer_output.changelog) == 1

    def test_empty_changelog(self):
        fo = FixerOutput(fixed_code="x = 1", changelog=[])
        assert fo.changelog == []

    def test_fix_entry_fields(self, sample_fixer_output):
        entry = sample_fixer_output.changelog[0]
        assert entry.issue_ref == "CRITICAL L12"
        assert "zero-division" in entry.change_made.lower()


# ------------------------------
# EvaluatorOutput
# ------------------------------

class TestEvaluatorOutput:
    def test_valid_pass_decision(self, sample_evaluator_output_pass):
        assert sample_evaluator_output_pass.decision == "pass"
        assert sample_evaluator_output_pass.overall_score == 96

    def test_valid_retry_decision(self, sample_evaluator_output_retry):
        assert sample_evaluator_output_retry.decision == "retry"
        assert sample_evaluator_output_retry.overall_score == 60

    def test_valid_fail_decision(self, sample_evaluator_output_fail):
        assert sample_evaluator_output_fail.decision == "fail"
        assert sample_evaluator_output_fail.overall_score == 36

    def test_invalid_decision_raises(self):
        with pytest.raises(ValidationError):
            EvaluatorOutput(
                correctness=DimensionScore(score=80, notes="ok"),
                completeness=DimensionScore(score=80, notes="ok"),
                code_quality=DimensionScore(score=80, notes="ok"),
                overall_score=80,
                decision="maybe",  # not a valid literal
                feedback="test",
            )

    def test_dimension_scores_present(self, sample_evaluator_output_pass):
        assert sample_evaluator_output_pass.correctness.score == 95
        assert sample_evaluator_output_pass.completeness.score == 100
        assert sample_evaluator_output_pass.code_quality.score == 90

    def test_model_dump_is_serializable(self, sample_evaluator_output_pass):
        import json
        dumped = sample_evaluator_output_pass.model_dump()
        # Should not raise — all fields must be JSON-serializable
        json.dumps(dumped)
        assert dumped["decision"] == "pass"
        assert dumped["correctness"]["score"] == 95


# ------------------------------
# AgentState
# ------------------------------

class TestAgentState:
    def test_minimal_valid_state(self):
        state: AgentState = {
            "code": "print('hello')",
            "language": "python",
            "reviewer_output": None,
            "fixer_output": None,
            "evaluator_output": None,
            "iteration": 0,
            "final_status": "pending",
        }
        assert state["iteration"] == 0
        assert state["final_status"] == "pending"

    def test_state_with_outputs(self, sample_reviewer_output, sample_fixer_output, sample_evaluator_output_pass):
        state: AgentState = {
            "code": "x = 1/0",
            "language": "python",
            "reviewer_output": sample_reviewer_output,
            "fixer_output": sample_fixer_output,
            "evaluator_output": sample_evaluator_output_pass,
            "iteration": 1,
            "final_status": "complete",
        }
        assert state["reviewer_output"].language == "python"
        assert state["fixer_output"].fixed_code is not None
        assert state["evaluator_output"].decision == "pass"
