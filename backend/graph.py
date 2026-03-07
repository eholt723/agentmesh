from langgraph.graph import END, StateGraph

from agents.evaluator import evaluator_node
from agents.fixer import fixer_node
from agents.reviewer import reviewer_node
from models import AgentState


def _should_retry(state: AgentState) -> str:
    if state["evaluator_output"].decision == "retry" and state["iteration"] < 2:
        return "retry"
    return "end"


def build_graph():
    workflow = StateGraph(AgentState)

    workflow.add_node("reviewer", reviewer_node)
    workflow.add_node("fixer", fixer_node)
    workflow.add_node("evaluator", evaluator_node)

    workflow.set_entry_point("reviewer")
    workflow.add_edge("reviewer", "fixer")
    workflow.add_edge("fixer", "evaluator")
    workflow.add_conditional_edges(
        "evaluator",
        _should_retry,
        {"retry": "fixer", "end": END},
    )

    return workflow.compile()


graph = build_graph()
