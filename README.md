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

[![CI/CD](https://github.com/eholt723/agentmesh/actions/workflows/ci.yml/badge.svg)](https://github.com/eholt723/agentmesh/actions/workflows/ci.yml)

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

| Layer | Responsibility |
|---|---|
| Browser | Renders result panels; streams SSE events via `useSSEStream.js` |
| FastAPI endpoint | Validates input, opens SSE response, fans out agent updates |
| LangGraph StateGraph | Compiles the agent graph; routes the conditional retry edge |
| Reviewer | Analyzes code; produces a structured issue list with line refs and severity |
| Fixer | Applies fixes; returns corrected code and a changelog; accepts evaluator feedback on retry |
| Evaluator | Scores the fix across correctness, completeness, and code quality; decides pass / fail / retry |

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

| Layer | Technology |
|---|---|
| Agent orchestration | LangGraph StateGraph |
| LLM | Groq — `llama-3.3-70b-versatile` |
| Backend | FastAPI, Python 3.11 |
| Schema validation | Pydantic v2, Pydantic Settings |
| Reliability | Tenacity (exponential backoff on all Groq calls) |
| Real-time | Server-Sent Events via `StreamingResponse` |
| Frontend | React 18, Vite 5, Tailwind CSS 3 |
| Syntax highlighting | highlight.js 11 (slimmed to 7 languages) |
| Hosting | Hugging Face Spaces (Docker SDK) |

---

## Deployment

Every push to `main` runs the CI/CD pipeline. If all unit tests pass, the workflow automatically deploys to Hugging Face Spaces — no manual push required. The live app is at [https://huggingface.co/spaces/eholt723/AgentMesh](https://huggingface.co/spaces/eholt723/AgentMesh). Cold starts on the free tier can take 1–3 minutes if the container has been idle.

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
│   ├── main.py              # FastAPI app, /review/stream endpoint, SSE streaming
│   ├── graph.py             # LangGraph StateGraph + conditional retry edge (_should_retry)
│   ├── models.py            # Pydantic schemas for AgentState and all agent outputs
│   ├── config.py            # Pydantic settings (GROQ_API_KEY, GROQ_MODEL, PORT)
│   ├── agents/
│   │   ├── reviewer.py      # Analyzes code; returns structured issue list via JSON mode
│   │   ├── fixer.py         # Applies fixes; parses XML response (_parse_fixer_response)
│   │   └── evaluator.py     # Scores fix; emits pass / fail / retry decision via JSON mode
│   └── requirements.txt
├── frontend/
│   ├── index.html
│   ├── vite.config.js       # Vite config + /review proxy to backend in dev
│   └── src/
│       ├── App.jsx           # Router, layout, dark mode state
│       ├── components/
│       │   ├── CodeInput.jsx       # Paste + file upload, language selector
│       │   ├── ReviewerPanel.jsx   # Issue list with severity badges
│       │   ├── FixerPanel.jsx      # Syntax-highlighted fixed code + changelog
│       │   ├── EvaluatorPanel.jsx  # Score rings, pass/fail verdict, retry indicator
│       │   └── ActivityLog.jsx     # Live agent handoff trace with elapsed timestamps
│       ├── hooks/
│       │   └── useSSEStream.js     # Fetch-based SSE reader; parses typed events
│       └── pages/
│           └── About.jsx           # /about route — pipeline overview and tech stack
├── tests/
│   ├── conftest.py          # Shared fixtures; injects dummy GROQ_API_KEY for unit tests
│   ├── test_pipeline.py     # CLI end-to-end runner; pretty-prints SSE stream
│   ├── unit/                # 54 unit tests — no API keys required
│   │   ├── test_models.py         # Pydantic schema validation
│   │   ├── test_fixer_parser.py   # _parse_fixer_response() including edge cases
│   │   ├── test_graph_routing.py  # _should_retry() across all decisions and iterations
│   │   └── test_api.py            # SSE endpoint with mocked graph
│   └── samples/             # Buggy code files used for testing (Python, JS)
├── .github/
│   └── workflows/
│       └── ci.yml           # GitHub Actions: runs unit tests, then deploys to HF Spaces on push to main
├── Dockerfile               # Multi-stage: Node build → Python runtime
├── pyproject.toml           # pytest config, asyncio_mode, dev dependencies
└── .env.example
```

---

## Design Decisions

- **Fixer uses XML tags instead of JSON mode.** The Reviewer and Evaluator both use `with_structured_output(..., method="json_mode")`, but the Fixer cannot — embedding source code inside a JSON string value reliably breaks because code contains unescaped quotes, backslashes, and multi-line constructs that corrupt the payload. Instead, the Fixer returns a free-form response and `_parse_fixer_response()` extracts content from `<fixed_code>` and `<changelog>` XML tags, which have no escaping requirements. The alternative (post-processing to escape before parsing) adds fragile string manipulation for no gain.

- **Frontend is bundled into the backend container as static files.** The Dockerfile builds the React/Vite frontend in a Node stage and copies the output into `backend/static/`, which FastAPI serves via `StaticFiles`. A separate container or CDN-hosted frontend makes sense in production but requires either a reverse proxy or CORS configuration. For a free-tier single-container deploy on Hugging Face Spaces, one server eliminates CORS, simplifies the deploy target, and means there's only one URL to manage.

- **The backend is fully stateless.** There's no database, no review history, and no per-user state. Every request is self-contained, which keeps cold starts fast and removes any storage dependency on the free tier. For a demo where each run is independent and users don't need to revisit past reviews, stateless is the right scope — adding persistence here would be complexity with no user-facing payoff.

---

## Future Improvements

- **Authentication and per-user rate limiting** — CORS is currently open (`allow_origins=["*"]`) with no API key or session layer; acceptable for a public demo, not for a multi-tenant deployment.
- **Token-by-token streaming within agents** — SSE events are emitted once per agent completion, not per token. True token streaming would require switching LangGraph stream mode and forwarding token chunks from Groq as they arrive.
- **Persistent review history** — results aren't stored; users can't revisit a prior run. A lightweight database layer would enable history, cross-run diffing, and shareable permalink URLs.
- **Async job mode for large inputs** — long-running reviews hold an SSE connection open for the full duration. A task queue with status polling would be more robust than a persistent HTTP stream for larger files or slower models.
- **Expanded language support in highlight.js** — currently registered for 7 languages to keep the bundle at 204 KB (down from 1095 KB). Supporting more languages would require weighing bundle growth against coverage for less common submissions.

---

## Portfolio Context

AgentMesh demonstrates a distinct architectural pattern from prior projects:

- **TraceAgent** — observable agentic research platform (AWS + CloudWatch)
- **ReconAgent** — autonomous research pipeline with SSE streaming
- **AgentFlow** — LangGraph document classification

AgentMesh adds: true multi-agent collaboration with structured inter-agent handoffs, an evaluation/retry loop with feedback propagation, and dual-mode code input — all streamed to the frontend in real time.
