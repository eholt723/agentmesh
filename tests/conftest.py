"""
Shared fixtures and path setup for all AgentMesh tests.

Sets GROQ_API_KEY before any backend modules are imported so that
config.py's Settings() instantiation does not fail in unit tests.
"""

import os
import sys

# ------------------------------
# Environment — must precede backend imports
# ------------------------------

os.environ.setdefault("GROQ_API_KEY", "test-key-unit-tests")
os.environ.setdefault("GROQ_MODEL", "llama-3.3-70b-versatile")

# Add backend/ to path so tests can import backend modules directly
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

# ------------------------------
# Shared fixtures
# ------------------------------

import pytest
from models import (
    DimensionScore,
    EvaluatorOutput,
    FixEntry,
    FixerOutput,
    Issue,
    ReviewerOutput,
)


@pytest.fixture
def sample_issue():
    return Issue(
        line_ref="L12",
        issue_type="bug",
        severity="critical",
        explanation="Division by zero when denominator is 0",
    )


@pytest.fixture
def sample_reviewer_output(sample_issue):
    return ReviewerOutput(
        language="python",
        issues=[sample_issue],
        summary="One critical bug found: unguarded division.",
    )


@pytest.fixture
def sample_fixer_output():
    return FixerOutput(
        fixed_code="def divide(a, b):\n    if b == 0:\n        raise ValueError('Cannot divide by zero')\n    return a / b\n",
        changelog=[
            FixEntry(issue_ref="CRITICAL L12", change_made="Added zero-division guard before dividing"),
        ],
    )


@pytest.fixture
def sample_evaluator_output_pass():
    return EvaluatorOutput(
        correctness=DimensionScore(score=95, notes="Fix correctly prevents ZeroDivisionError"),
        completeness=DimensionScore(score=100, notes="All issues addressed"),
        code_quality=DimensionScore(score=90, notes="Clean, readable fix"),
        overall_score=96,
        decision="pass",
        feedback="The fix is correct and complete.",
    )


@pytest.fixture
def sample_evaluator_output_retry():
    return EvaluatorOutput(
        correctness=DimensionScore(score=60, notes="Partial fix — error not propagated correctly"),
        completeness=DimensionScore(score=55, notes="Warning-level issues still unresolved"),
        code_quality=DimensionScore(score=70, notes="Acceptable quality"),
        overall_score=60,
        decision="retry",
        feedback="Address the unresolved warning-level issues before passing.",
    )


@pytest.fixture
def sample_evaluator_output_fail():
    return EvaluatorOutput(
        correctness=DimensionScore(score=30, notes="Fix introduces a new bug"),
        completeness=DimensionScore(score=40, notes="Critical issues remain"),
        code_quality=DimensionScore(score=45, notes="Code quality degraded"),
        overall_score=36,
        decision="fail",
        feedback="The fix is fundamentally incorrect.",
    )


@pytest.fixture
def divide_by_zero_code():
    return """\
def divide(a, b):
    return a / b

result = divide(10, 0)
print(result)
"""


@pytest.fixture
def sql_injection_code():
    return """\
import sqlite3

def get_user(username):
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    query = f"SELECT * FROM users WHERE username = '{username}'"
    cursor.execute(query)
    return cursor.fetchone()
"""
