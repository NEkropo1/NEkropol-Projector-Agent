
from __future__ import annotations

from typing import TypedDict, List, Dict, Any

from langgraph.graph import StateGraph, END
from schemas.types import Mode, TraceStep


class GraphState(TypedDict, total=False):
    message: str
    image_url: str | None
    mode: Mode
    trace: List[TraceStep]
    persona_info: Dict[str, Any]
    output: str


def add_trace(state: GraphState, step: str, data: Dict[str, Any] | None = None) -> None:
    trace = state.get("trace") or []
    trace.append(TraceStep(step=step, data=data or {}).model_dump())
    state["trace"] = trace


def compile_graph(classify_node, handle_photo, handle_meta, handle_casual, handle_oos):
    g = StateGraph(GraphState)

    g.add_node("classify", classify_node)
    g.add_node("handle_photo", handle_photo)
    g.add_node("handle_meta", handle_meta)
    g.add_node("handle_casual", handle_casual)
    g.add_node("handle_oos", handle_oos)

    g.set_entry_point("classify")

    def branch(state: GraphState):
        mode = state.get("mode")
        if mode == "PERSON_PHOTO":
            return "handle_photo"
        if mode == "PERSON_METADATA":
            return "handle_meta"
        if mode == "CASUAL":
            return "handle_casual"
        return "handle_oos"

    g.add_conditional_edges("classify", branch)
    g.add_edge("handle_photo", END)
    g.add_edge("handle_meta", END)
    g.add_edge("handle_casual", END)
    g.add_edge("handle_oos", END)

    return g.compile()
