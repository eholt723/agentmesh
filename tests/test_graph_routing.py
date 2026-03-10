"""
Unit tests for the LangGraph routing logic in graph.py.

_should_retry() is the conditional edge function that decides whether
the evaluator's decision triggers another fix pass or terminates the graph.
Tests cover all decision values and the max-iteration boundary.
"""

import pytest

from graph import _should_retry
from models import AgentState, DimensionScore, EvaluatorOutput


# ------------------------------
# Helpers
# ------------------------------

def _make_state(decision: str, iteration: int) -> AgentState:
    """Build a minimal AgentState with only the fields _should_retry reads."""
    evaluator_output = EvaluatorOutput(
        correctness=DimensionScore(score=70, notes="ok"),
        completeness=DimensionScore(score=70, notes="ok"),
        code_quality=DimensionScore(score=70, notes="ok"),
        overall_score=70,
        decision=decision,
        feedback="test feedback",
    )
    return {
        "code": "x = 1",
        "language": "python",
        "reviewer_output": None,
        "fixer_output": None,
        "evaluator_output": evaluator_output,
        "iteration": iteration,
        "final_status": "pending",
    }


# ------------------------------
# Pass decision
# ------------------------------

class TestShouldRetryPass:
    def test_pass_at_iteration_0_returns_end(self):
        assert _should_retry(_make_state("pass", 0)) == "end"

    def test_pass_at_iteration_1_returns_end(self):
        assert _should_retry(_make_state("pass", 1)) == "end"

    def test_pass_at_iteration_2_returns_end(self):
        assert _should_retry(_make_state("pass", 2)) == "end"


# ------------------------------
# Fail decision
# ------------------------------

class TestShouldRetryFail:
    def test_fail_at_iteration_0_returns_end(self):
        # fail means the fix is fundamentally broken — do not retry
        assert _should_retry(_make_state("fail", 0)) == "end"

    def test_fail_at_iteration_1_returns_end(self):
        assert _should_retry(_make_state("fail", 1)) == "end"


# ------------------------------
# Retry decision
# ------------------------------

class TestShouldRetryRetry:
    def test_retry_at_iteration_0_returns_retry(self):
        assert _should_retry(_make_state("retry", 0)) == "retry"

    def test_retry_at_iteration_1_returns_retry(self):
        assert _should_retry(_make_state("retry", 1)) == "retry"

    def test_retry_at_max_iteration_returns_end(self):
        # iteration == 2 means two fix passes have already run — stop looping
        assert _should_retry(_make_state("retry", 2)) == "end"

    def test_retry_beyond_max_iteration_returns_end(self):
        # Defensive: should never be > 2 in practice, but routing must not loop forever
        assert _should_retry(_make_state("retry", 3)) == "end"


# ------------------------------
# Iteration boundary
# ------------------------------

class TestIterationBoundary:
    def test_max_fix_passes_is_two(self):
        """Confirm the boundary value: iteration < 2 allows retry."""
        assert _should_retry(_make_state("retry", 1)) == "retry"
        assert _should_retry(_make_state("retry", 2)) == "end"

    def test_all_decisions_at_max_iteration_return_end(self):
        for decision in ("pass", "fail", "retry"):
            result = _should_retry(_make_state(decision, 2))
            assert result == "end", f"Expected 'end' for decision={decision!r} at max iteration"
