from __future__ import annotations
from datetime import datetime, timezone
from typing import Dict, Any
from agents.base import compile_graph
from agents.projector_agent import (
    node_classify, node_handle_photo, node_handle_meta, node_handle_casual, node_handle_oos
)
from app import state_store

graph = compile_graph(
    classify_node=node_classify,
    handle_photo=node_handle_photo,
    handle_meta=node_handle_meta,
    handle_casual=node_handle_casual,
    handle_oos=node_handle_oos,
)


# TODO: to tools
def _dt_from_ts(ts: float | None):
    return datetime.fromtimestamp(ts, tz=timezone.utc) if ts else None


async def run_new(message: str, image_url: str | None) -> Dict[str, Any]:
    init_state = {"message": message, "image_url": image_url, "trace": []}
    result = await graph.ainvoke(init_state)

    cid, exp = None, None
    if result.get("next_action") in {"need_better_photo", "ask_for_more_details"}:
        cid = await state_store.new_conversation(result)
        exp = _dt_from_ts(await state_store.expires_at(cid))

    return {**result, "conversation_id": cid, "expires_at": exp}


async def continue_conversation(cid: str, message: str | None, image_url: str | None) -> Dict[str, Any]:
    state = await state_store.get_state(cid)
    if not state:
        raise ValueError("Conversation not found or expired")

    if state.get("next_action") == "need_better_photo" and not image_url:
        raise ValueError("Expected an image_url for better photo")

    if message:
        state["message"] = message
    if image_url:
        state["image_url"] = image_url

    result = await graph.ainvoke(state)
    next_action = result.get("next_action")

    if next_action in (None, "none"):
        await state_store.close_conversation(cid)
        exp = None
    else:
        await state_store.save_state(cid, result)
        exp = _dt_from_ts(await state_store.expires_at(cid))

    return {**result, "conversation_id": cid, "expires_at": exp}
