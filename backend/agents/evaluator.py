from langchain_core.messages import HumanMessage, SystemMessage
from langchain_groq import ChatGroq
from tenacity import retry, stop_after_attempt, wait_exponential

from config import settings
from models import AgentState, EvaluatorOutput, Issue

SYSTEM_PROMPT = """You are a rigorous code review evaluator. Your job is to independently assess how well
a fixer addressed the issues identified by a reviewer.

Score three dimensions from 0-100:
- correctness: Did the fixes actually solve the identified issues? Are the fixes technically sound?
- completeness: Were all critical and warning issues addressed? Nothing left unresolved?
- code_quality: Did the fixes introduce any new bugs, regressions, or quality problems?

Overall score = weighted average (correctness 40%, completeness 40%, code_quality 20%).

Decision rules:
- "pass": overall_score >= 70 — fix is acceptable
- "retry": overall_score 50-69 — fixable problems, worth another attempt
- "fail": overall_score < 50 — fundamental problems with the fix

Provide specific, actionable feedback explaining your scores and what would need to change."""


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
async def _invoke_evaluator(llm, messages):
    return await llm.ainvoke(messages)


def _format_issues(issues: list[Issue]) -> str:
    lines = []
    for i, issue in enumerate(issues, 1):
        lines.append(
            f"{i}. [{issue.severity.upper()}] {issue.line_ref} — {issue.issue_type}: {issue.explanation}"
        )
    return "\n".join(lines)


async def evaluator_node(state: AgentState) -> dict:
    llm = ChatGroq(
        model=settings.groq_model,
        api_key=settings.groq_api_key,
    ).with_structured_output(EvaluatorOutput)

    issues_text = _format_issues(state["reviewer_output"].issues)
    changelog_text = "\n".join(
        f"- Fixed '{entry.issue_ref}': {entry.change_made}"
        for entry in state["fixer_output"].changelog
    )

    human_content = (
        f"Original code:\n```\n{state['code']}\n```\n\n"
        f"Reviewer issues:\n{issues_text}\n\n"
        f"Fixed code:\n```\n{state['fixer_output'].fixed_code}\n```\n\n"
        f"Fixer changelog:\n{changelog_text}"
    )

    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=human_content),
    ]

    result: EvaluatorOutput = await _invoke_evaluator(llm, messages)

    final_status = "complete" if result.decision in ("pass", "fail") else "retry"

    return {
        "evaluator_output": result,
        "final_status": final_status,
    }
