"""
Integration tests for the FastAPI /review/stream endpoint.

The LangGraph pipeline is mocked so these tests verify the API layer —
SSE formatting, event sequencing, input validation, and content-type
handling — without making any real LLM calls.
"""

import json
from unittest.mock import patch

import pytest
from httpx import ASGITransport, AsyncClient

from main import app
from models import DimensionScore, EvaluatorOutput, FixEntry, FixerOutput, Issue, ReviewerOutput


# ------------------------------
# Mock graph data
# ------------------------------

def _make_mock_astream(decision: str = "pass"):
    """Return an async generator that yields the three pipeline stage updates."""

    async def _astream(initial_state, stream_mode):
        reviewer_out = ReviewerOutput(
            language="python",
            issues=[
                Issue(
                    line_ref="L4",
                    issue_type="bug",
                    severity="critical",
                    explanation="Division by zero when b is 0",
                )
            ],
            summary="One critical bug found.",
        )
        yield {"reviewer": {"reviewer_output": reviewer_out, "language": "python"}}

        fixer_out = FixerOutput(
            fixed_code="def divide(a, b):\n    if b == 0:\n        raise ValueError('Cannot divide by zero')\n    return a / b\n",
            changelog=[FixEntry(issue_ref="CRITICAL L4", change_made="Added zero-division guard")],
        )
        yield {"fixer": {"fixer_output": fixer_out, "iteration": 1}}

        evaluator_out = EvaluatorOutput(
            correctness=DimensionScore(score=95, notes="Fix is correct"),
            completeness=DimensionScore(score=100, notes="All issues resolved"),
            code_quality=DimensionScore(score=90, notes="Clean implementation"),
            overall_score=96,
            decision=decision,
            feedback="Fix is excellent." if decision == "pass" else "Needs more work.",
        )
        yield {"evaluator": {"evaluator_output": evaluator_out, "final_status": "complete"}}

    return _astream


# ------------------------------
# Helpers
# ------------------------------

async def _collect_sse_events(client: AsyncClient, method: str, **kwargs) -> list[dict]:
    """Stream a request and collect all parsed SSE event payloads."""
    events = []
    async with client.stream(method, **kwargs) as response:
        buffer = ""
        async for chunk in response.aiter_text():
            buffer += chunk
            while "\n\n" in buffer:
                line, buffer = buffer.split("\n\n", 1)
                line = line.strip()
                if line.startswith("data: "):
                    events.append(json.loads(line[6:]))
    return events


# ------------------------------
# JSON body requests
# ------------------------------

class TestReviewStreamJSON:
    async def test_returns_200_with_sse_content_type(self):
        with patch("main.graph") as mock_graph:
            mock_graph.astream = _make_mock_astream()
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                async with client.stream("POST", "/review/stream", json={"code": "x = 1/0", "language": "python"}) as resp:
                    assert resp.status_code == 200
                    assert "text/event-stream" in resp.headers["content-type"]

    async def test_emits_reviewing_event(self):
        with patch("main.graph") as mock_graph:
            mock_graph.astream = _make_mock_astream()
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                events = await _collect_sse_events(client, "POST", url="/review/stream", json={"code": "x = 1/0", "language": "python"})

        types = [e["type"] for e in events]
        assert "reviewing" in types

    async def test_emits_fixing_event(self):
        with patch("main.graph") as mock_graph:
            mock_graph.astream = _make_mock_astream()
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                events = await _collect_sse_events(client, "POST", url="/review/stream", json={"code": "x = 1/0", "language": "python"})

        types = [e["type"] for e in events]
        assert "fixing" in types

    async def test_emits_evaluating_event(self):
        with patch("main.graph") as mock_graph:
            mock_graph.astream = _make_mock_astream()
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                events = await _collect_sse_events(client, "POST", url="/review/stream", json={"code": "x = 1/0", "language": "python"})

        types = [e["type"] for e in events]
        assert "evaluating" in types

    async def test_emits_complete_event_last(self):
        with patch("main.graph") as mock_graph:
            mock_graph.astream = _make_mock_astream()
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                events = await _collect_sse_events(client, "POST", url="/review/stream", json={"code": "x = 1/0", "language": "python"})

        assert events[-1]["type"] == "complete"

    async def test_event_sequence_order(self):
        with patch("main.graph") as mock_graph:
            mock_graph.astream = _make_mock_astream()
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                events = await _collect_sse_events(client, "POST", url="/review/stream", json={"code": "x = 1/0", "language": "python"})

        types = [e["type"] for e in events]
        assert types == ["reviewing", "fixing", "evaluating", "complete"]

    async def test_reviewing_event_contains_issues(self):
        with patch("main.graph") as mock_graph:
            mock_graph.astream = _make_mock_astream()
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                events = await _collect_sse_events(client, "POST", url="/review/stream", json={"code": "x = 1/0", "language": "python"})

        reviewing = next(e for e in events if e["type"] == "reviewing")
        issues = reviewing["data"]["reviewer_output"]["issues"]
        assert len(issues) == 1
        assert issues[0]["severity"] == "critical"

    async def test_evaluating_event_contains_score(self):
        with patch("main.graph") as mock_graph:
            mock_graph.astream = _make_mock_astream()
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                events = await _collect_sse_events(client, "POST", url="/review/stream", json={"code": "x = 1/0", "language": "python"})

        evaluating = next(e for e in events if e["type"] == "evaluating")
        eo = evaluating["data"]["evaluator_output"]
        assert isinstance(eo["overall_score"], int)
        assert 0 <= eo["overall_score"] <= 100
        assert eo["decision"] in ("pass", "retry", "fail")

    async def test_auto_language_accepted(self):
        with patch("main.graph") as mock_graph:
            mock_graph.astream = _make_mock_astream()
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                events = await _collect_sse_events(client, "POST", url="/review/stream", json={"code": "x = 1/0", "language": "auto"})

        assert any(e["type"] == "complete" for e in events)


# ------------------------------
# Input validation
# ------------------------------

class TestReviewStreamValidation:
    async def test_empty_code_returns_error_event(self):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            events = await _collect_sse_events(client, "POST", url="/review/stream", json={"code": "", "language": "python"})

        assert events[0]["type"] == "error"
        assert "code" in events[0]["data"]["message"].lower()

    async def test_whitespace_only_code_returns_error_event(self):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            events = await _collect_sse_events(client, "POST", url="/review/stream", json={"code": "   \n\t  ", "language": "python"})

        assert events[0]["type"] == "error"


# ------------------------------
# Multipart file upload
# ------------------------------

class TestReviewStreamFileUpload:
    async def test_file_upload_emits_pipeline_events(self, divide_by_zero_code):
        with patch("main.graph") as mock_graph:
            mock_graph.astream = _make_mock_astream()
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                events = await _collect_sse_events(
                    client,
                    "POST",
                    url="/review/stream",
                    files={"file": ("divide_by_zero.py", divide_by_zero_code.encode(), "text/plain")},
                    data={"language": "python"},
                )

        types = [e["type"] for e in events]
        assert "reviewing" in types
        assert "complete" in types

    async def test_missing_file_returns_error_event(self):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            # Force multipart/form-data by including a dummy file field that isn't named 'file'
            # so the endpoint enters the multipart branch but form.get("file") returns None
            events = await _collect_sse_events(
                client,
                "POST",
                url="/review/stream",
                files={"wrong_field": ("dummy.txt", b"", "text/plain")},
                data={"language": "python"},
            )

        assert events[0]["type"] == "error"
