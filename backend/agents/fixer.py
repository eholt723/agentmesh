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

Respond with valid JSON matching this schema:
{
  "fixed_code": "<the complete fixed source code, exactly as it should appear in the file>",
  "changelog": [
    {"issue_ref": "<e.g. CRITICAL L12>", "change_made": "<description of what was changed and why>"}
  ]
}"""

SYSTEM_PROMPT_RETRY = """You are an expert software engineer fixing code issues. This is a RETRY pass.

A previous fix attempt was evaluated and found insufficient. You must address the evaluator's feedback
in addition to the original reviewer issues.

Fix ALL critical and warning issues and address the evaluator's specific concerns.

Respond with valid JSON matching this schema:
{
  "fixed_code": "<the complete fixed source code, exactly as it should appear in the file>",
  "changelog": [
    {"issue_ref": "<reference to the original issue>", "change_made": "<description of what was changed and why>"}
  ]
}"""


@retry(stop=stop_after_attempt(2), wait=wait_exponential(multiplier=2, min=5, max=60))
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
        reasoning_effort="low",
        include_reasoning=False,
    ).with_structured_output(FixerOutput, method="json_mode")

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
