---
title: AgentMesh
emoji: 🔗
colorFrom: gray
colorTo: blue
sdk: docker
app_port: 7860
pinned: false
---

# AgentMesh

[![CI](https://github.com/eholt723/agentmesh/actions/workflows/ci.yml/badge.svg)](https://github.com/eholt723/agentmesh/actions/workflows/ci.yml)

A full-stack multi-agent AI system that reviews submitted code, fixes identified issues, and evaluates the quality of the fix — streaming every agent decision and handoff to the browser in real time.

Three specialized agents collaborate via a [LangGraph](https://github.com/langchain-ai/langgraph) StateGraph. The Evaluator can reject the Fixer's output and trigger a second fix pass, making this a true multi-agent loop — not a single agent with multiple nodes.

---

## Architecture

```
Submitted Code
      │
      ▼
 ┌─────────┐      structured issue list
 │Reviewer │ ────────────────────────────┐
 └─────────┘                             │
                                         ▼
                                    ┌────────┐      fixed code + changelog
                                    │ Fixer  │ ────────────────────────────┐
                                    └────────┘                             │
                                       ▲                                   ▼
                                       │ retry (max 2)             ┌───────────┐
                                       └───────────────────────────│ Evaluator │
                                                                   └───────────┘
                                                                          │
                                                               pass / fail / retry
```

### Agents

| Agent | Input | Output |
|-------|-------|--------|
| **Reviewer** | Raw submitted code | Issue list — line ref, type, severity, explanation |
| **Fixer** | Code + issue list (+ evaluator feedback on retry) | Fixed code + changelog |
| **Evaluator** | Original code + issues + fixed code + changelog | Score (0–100) across 3 dimensions, pass/fail/retry decision |

**Evaluator scoring dimensions:**
- **Correctness** (40%) — did the fixes actually solve the issues?
- **Completeness** (40%) — were all critical and warning issues addressed?
- **Code Quality** (20%) — did the fixes introduce new problems?

If overall score is 50–69, the Evaluator triggers a retry back to the Fixer with specific feedback. Capped at 2 fix passes.

---

## Tech Stack

**Backend**
- Python 3.11, FastAPI, LangGraph
- Groq (llama-3.3-70b-versatile) via `langchain-groq`
- SSE streaming via `StreamingResponse`
- Tenacity retry on all Groq calls
- Stateless — no database, no sessions

**Frontend**
- React 18, Vite, Tailwind CSS
- Syntax highlighting via highlight.js (core only — 6 languages)
- Fetch-based SSE reader with file upload support

**Deployment**
- Multi-stage Docker build (Vite frontend bundled into FastAPI static dir)
- Hugging Face Spaces (Docker SDK), port 7860

---

## Running Locally

**Prerequisites:** Python 3.11+, Node 18+, a [Groq API key](https://console.groq.com)

```bash
# 1. Clone
git clone https://github.com/eholt723/agentmesh.git
cd agentmesh

# 2. Configure
cp .env.example .env
# edit .env and add your GROQ_API_KEY

# 3. Backend
cd backend
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8000 --reload

# 4. Frontend (separate terminal, dev mode with hot reload)
cd frontend
npm install
npm run dev                      # proxies /review → localhost:8000
```

Open `http://localhost:5173` for the dev server, or `http://localhost:8000` to use the production build.

**Build frontend for production:**
```bash
cd frontend && npm run build     # outputs to backend/static/
```

---

## Running Tests

A CLI test script streams the full pipeline and pretty-prints each agent's output.

```bash
# Start the backend first, then from the project root:
cd backend

# Default sample (divide by zero / bare except)
python ../tests/test_pipeline.py

# SQL injection sample
python ../tests/test_pipeline.py --file ../tests/samples/sql_injection.py

# JavaScript memory leak sample
python ../tests/test_pipeline.py --file ../tests/samples/memory_leak.js --language javascript
```

Sample files are in [`tests/samples/`](tests/samples/) — each is a small code snippet with deliberate bugs across different severity levels and issue types.

---

## SSE Event Types

The `/review/stream` endpoint emits these events in order:

| Event | Emitted when |
|-------|-------------|
| `reviewing` | Reviewer agent completes — includes full issue list |
| `fixing` | Fixer agent completes — includes fixed code and changelog |
| `evaluating` | Evaluator agent completes — includes scores and decision |
| `complete` | Graph finishes (pass or fail, max iterations reached) |
| `error` | Any unhandled exception during the pipeline |

On a retry, you'll see a second `fixing` event followed by a second `evaluating` event before `complete`.

---

## Input Modes

The `/review/stream` endpoint accepts two input formats:

**JSON body:**
```json
POST /review/stream
Content-Type: application/json

{ "code": "...", "language": "python" }
```

**File upload:**
```
POST /review/stream
Content-Type: multipart/form-data

file=<code file>
language=python
```

`language` defaults to `"auto"` — the Reviewer agent will detect it from the code.

---

## Project Structure

```
agentmesh/
├── backend/
│   ├── main.py              # FastAPI app, /review/stream endpoint
│   ├── graph.py             # LangGraph StateGraph + conditional retry edge
│   ├── models.py            # Pydantic schemas for state and all agent outputs
│   ├── config.py            # Pydantic settings (GROQ_API_KEY, GROQ_MODEL, PORT)
│   ├── agents/
│   │   ├── reviewer.py
│   │   ├── fixer.py
│   │   └── evaluator.py
│   └── requirements.txt
├── frontend/
│   └── src/
│       ├── App.jsx
│       ├── components/
│       │   ├── CodeInput.jsx       # paste + file upload, language selector
│       │   ├── ReviewerPanel.jsx   # issue list with severity badges
│       │   ├── FixerPanel.jsx      # syntax-highlighted fixed code + changelog
│       │   ├── EvaluatorPanel.jsx  # score rings, pass/fail verdict, retry state
│       │   └── ActivityLog.jsx     # live agent handoff trace
│       └── hooks/
│           └── useSSEStream.js
├── tests/
│   ├── test_pipeline.py     # CLI end-to-end test, pretty-prints SSE stream
│   └── samples/             # buggy code files for testing
├── Dockerfile               # multi-stage: Node build → Python runtime
└── .env.example
```

---

## Portfolio Context

AgentMesh demonstrates a distinct architectural pattern from prior projects:

- **TraceAgent** — observable agentic research platform (AWS + CloudWatch)
- **ReconAgent** — autonomous research pipeline with SSE streaming
- **AgentFlow** — LangGraph document classification

AgentMesh adds: true multi-agent collaboration with structured inter-agent handoffs, an evaluation/retry loop with feedback propagation, and dual-mode code input — all streamed to the frontend in real time.
