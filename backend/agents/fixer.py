from langchain_core.messages import HumanMessage, SystemMessage
from langchain_groq import ChatGroq
from tenacity import retry, stop_after_attempt, wait_exponential

from config import settings
from models import AgentState, FixerOutput, Issue

SYSTEM_PROMPT = """You are an expert software engineer tasked with fixing code issues identified by a code reviewer.

You will receive:
1. The original code
2. A list of issues found by the reviewer
3. Optionally, evaluator feedback from a previous fix attempt

Your job:
- Fix ALL critical and warning issues
- Address suggestions where practical
- Do not introduce new bugs or change working functionality
- For each fix, document what you changed and which issue it resolves

Return the complete fixed code (not just the changed parts) and a detailed changelog."""

SYSTEM_PROMPT_RETRY = """You are an expert software engineer fixing code issues. This is a RETRY pass.

A previous fix attempt was evaluated and found insufficient. You must address the evaluator's feedback
in addition to the original reviewer issues.

Fix ALL critical and warning issues and address the evaluator's specific concerns."""


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
async def _invoke_fixer(llm, messages):
    return await llm.ainvoke(messages)


def _format_issues(issues: list[Issue]) -> str:
    lines = []
    for i, issue in enumerate(issues, 1):
        lines.append(
            f"{i}. [{issue.severity.upper()}] {issue.line_ref} — {issue.issue_type}: {issue.explanation}"
        )
    return "\n".join(lines)


async def fixer_node(state: AgentState) -> dict:
    is_retry = state["iteration"] > 0
    system_prompt = SYSTEM_PROMPT_RETRY if is_retry else SYSTEM_PROMPT

    llm = ChatGroq(
        model=settings.groq_model,
        api_key=settings.groq_api_key,
    ).with_structured_output(FixerOutput)

    issues_text = _format_issues(state["reviewer_output"].issues)

    human_content = (
        f"Original code:\n```\n{state['code']}\n```\n\n"
        f"Reviewer issues to fix:\n{issues_text}"
    )

    if is_retry and state.get("evaluator_output"):
        human_content += (
            f"\n\nEvaluator feedback from previous fix attempt:\n"
            f"{state['evaluator_output'].feedback}\n\n"
            f"Previous overall score: {state['evaluator_output'].overall_score}/100\n"
            f"Address this feedback specifically in your revised fix."
        )

    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=human_content),
    ]

    result: FixerOutput = await _invoke_fixer(llm, messages)

    return {
        "fixer_output": result,
        "iteration": state["iteration"] + 1,
    }
