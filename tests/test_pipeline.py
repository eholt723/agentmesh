"""
AgentMesh — End-to-End Pipeline Test

Sends a sample code file to the /review/stream endpoint and prints
each SSE event as it arrives. Useful for verifying the full
Reviewer → Fixer → Evaluator pipeline locally.

Usage:
    cd agentmesh/backend
    python ../tests/test_pipeline.py
    python ../tests/test_pipeline.py --file ../tests/samples/sql_injection.py
    python ../tests/test_pipeline.py --file ../tests/samples/memory_leak.js --language javascript
"""

import argparse
import json
import sys
import urllib.request

# ------------------------------
# Config
# ------------------------------
BASE_URL = "http://localhost:8000"
DEFAULT_SAMPLE = "tests/samples/divide_by_zero.py"

EVENT_COLORS = {
    "reviewing":  "\033[94m",   # blue
    "fixing":     "\033[93m",   # yellow
    "evaluating": "\033[95m",   # magenta
    "complete":   "\033[92m",   # green
    "error":      "\033[91m",   # red
}
RESET = "\033[0m"
BOLD  = "\033[1m"


# ------------------------------
# Helpers
# ------------------------------
def color(event_type: str, text: str) -> str:
    return f"{EVENT_COLORS.get(event_type, '')}{text}{RESET}"


def print_event(event: dict) -> None:
    t = event.get("type", "unknown")
    data = event.get("data", {})

    print(f"\n{BOLD}{color(t, f'[ {t.upper()} ]')}{RESET}")

    if t == "reviewing":
        ro = data.get("reviewer_output", {})
        print(f"  Language : {data.get('language', ro.get('language', '?'))}")
        print(f"  Summary  : {ro.get('summary', '')}")
        for issue in ro.get("issues", []):
            sev = issue.get("severity", "").upper()
            print(f"  [{sev}] {issue.get('line_ref')} — {issue.get('issue_type')}: {issue.get('explanation')}")

    elif t == "fixing":
        fo = data.get("fixer_output", {})
        iteration = data.get("iteration", "?")
        print(f"  Pass     : {iteration}")
        print(f"  Changelog:")
        for entry in fo.get("changelog", []):
            print(f"    + {entry.get('change_made')} (resolves: {entry.get('issue_ref')})")

    elif t == "evaluating":
        eo = data.get("evaluator_output", {})
        decision = eo.get("decision", "?").upper()
        print(f"  Score    : {eo.get('overall_score')}/100  →  {color(t, decision)}")
        for dim in ("correctness", "completeness", "code_quality"):
            d = eo.get(dim, {})
            print(f"  {dim:<14}: {d.get('score')}/100 — {d.get('notes')}")
        print(f"  Feedback : {eo.get('feedback')}")

    elif t == "complete":
        print(f"  {color('complete', 'Review cycle finished.')}")

    elif t == "error":
        print(f"  {color('error', data.get('message', 'Unknown error'))}")


# ------------------------------
# Main
# ------------------------------
def main() -> None:
    parser = argparse.ArgumentParser(description="Test the AgentMesh review pipeline")
    parser.add_argument("--file", default=DEFAULT_SAMPLE, help="Path to code file to review")
    parser.add_argument("--language", default="auto", help="Language hint (default: auto)")
    parser.add_argument("--url", default=BASE_URL, help="Backend base URL")
    args = parser.parse_args()

    try:
        with open(args.file, "r") as f:
            code = f.read()
    except FileNotFoundError:
        print(f"Error: file not found: {args.file}", file=sys.stderr)
        sys.exit(1)

    print(f"{BOLD}AgentMesh Pipeline Test{RESET}")
    print(f"  File    : {args.file}")
    print(f"  Language: {args.language}")
    print(f"  Endpoint: {args.url}/review/stream")
    print("-" * 50)

    payload = json.dumps({"code": code, "language": args.language}).encode()
    req = urllib.request.Request(
        f"{args.url}/review/stream",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(req) as resp:
            buffer = ""
            for chunk in resp:
                buffer += chunk.decode("utf-8")
                while "\n\n" in buffer:
                    line, buffer = buffer.split("\n\n", 1)
                    line = line.strip()
                    if line.startswith("data: "):
                        try:
                            event = json.loads(line[6:])
                            print_event(event)
                        except json.JSONDecodeError:
                            pass
    except Exception as e:
        print(f"{color('error', 'Connection failed')}: {e}", file=sys.stderr)
        print("Is the backend running? cd backend && .venv/bin/uvicorn main:app --port 8000", file=sys.stderr)
        sys.exit(1)

    print(f"\n{'-' * 50}")
    print("Done.")


if __name__ == "__main__":
    main()
