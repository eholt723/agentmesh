import json
import os
from typing import AsyncGenerator

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles

from graph import graph
from models import AgentState

app = FastAPI(title="AgentMesh")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Map LangGraph node names to SSE event types
NODE_EVENT_MAP = {
    "reviewer": "reviewing",
    "fixer": "fixing",
    "evaluator": "evaluating",
}


def _sse(event_type: str, data: dict) -> str:
    payload = json.dumps({"type": event_type, "data": data})
    return f"data: {payload}\n\n"


def _serialize_state_update(node_name: str, update: dict) -> dict:
    """Convert Pydantic models in state updates to JSON-serializable dicts."""
    result = {}
    for key, value in update.items():
        if hasattr(value, "model_dump"):
            result[key] = value.model_dump()
        else:
            result[key] = value
    return result


async def _stream_review(code: str, language: str) -> AsyncGenerator[str, None]:
    initial_state: AgentState = {
        "code": code,
        "language": language if language != "auto" else "",
        "reviewer_output": None,
        "fixer_output": None,
        "evaluator_output": None,
        "iteration": 0,
        "final_status": "pending",
    }

    try:
        async for event in graph.astream(initial_state, stream_mode="updates"):
            for node_name, update in event.items():
                event_type = NODE_EVENT_MAP.get(node_name, node_name)
                data = _serialize_state_update(node_name, update)
                yield _sse(event_type, data)

        yield _sse("complete", {"message": "Review cycle complete"})

    except Exception as e:
        yield _sse("error", {"message": str(e)})


@app.post("/review/stream")
async def review_stream(request: Request):
    content_type = request.headers.get("content-type", "")

    if "multipart/form-data" in content_type:
        form = await request.form()
        file = form.get("file")
        if file is None:
            return StreamingResponse(
                iter([_sse("error", {"message": "No file provided"})]),
                media_type="text/event-stream",
            )
        code = (await file.read()).decode("utf-8", errors="replace")
        language = form.get("language", "auto")
    else:
        body = await request.json()
        code = body.get("code", "")
        language = body.get("language", "auto")

    if not code.strip():
        return StreamingResponse(
            iter([_sse("error", {"message": "No code provided"})]),
            media_type="text/event-stream",
        )

    return StreamingResponse(
        _stream_review(code, language),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


# Serve bundled frontend in production
static_dir = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(static_dir):
    app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")
