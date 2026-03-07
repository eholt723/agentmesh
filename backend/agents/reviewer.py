from langchain_core.messages import HumanMessage, SystemMessage
from langchain_groq import ChatGroq
from tenacity import retry, stop_after_attempt, wait_exponential

from config import settings
from models import AgentState, ReviewerOutput

SYSTEM_PROMPT = """You are an expert code reviewer with deep knowledge across all major programming languages.
Your job is to thoroughly analyze submitted code and identify all issues.

For each issue you find, provide:
- line_ref: specific line number or range (e.g. "L12", "L15-18", "L3")
- issue_type: category such as "bug", "security", "performance", "style", "code_smell", "logic_error"
- severity: "critical" (breaks functionality or security), "warning" (significant concern), or "suggestion" (improvement opportunity)
- explanation: clear, plain-English description of the problem and why it matters

Also detect the programming language of the submitted code.

Be thorough. Find real issues — do not invent problems that don't exist."""


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
async def _invoke_reviewer(llm, messages):
    return await llm.ainvoke(messages)


async def reviewer_node(state: AgentState) -> dict:
    llm = ChatGroq(
        model=settings.groq_model,
        api_key=settings.groq_api_key,
    ).with_structured_output(ReviewerOutput)

    language_hint = ""
    if state["language"] and state["language"] != "auto":
        language_hint = f"\nThe code is written in: {state['language']}"

    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=f"Review the following code:{language_hint}\n\n```\n{state['code']}\n```"),
    ]

    result: ReviewerOutput = await _invoke_reviewer(llm, messages)

    return {
        "reviewer_output": result,
        "language": result.language,
    }
