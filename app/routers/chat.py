
from __future__ import annotations

from fastapi import APIRouter
from agents.base import compile_graph
from agents.projector_agent import (
    node_classify, node_handle_photo, node_handle_meta, node_handle_casual, node_handle_oos
)
from schemas.types import ChatRequest, ChatResponse


router = APIRouter()


graph = compile_graph(
    classify_node=node_classify,
    handle_photo=node_handle_photo,
    handle_meta=node_handle_meta,
    handle_casual=node_handle_casual,
    handle_oos=node_handle_oos,
)


@router.post("/chat", response_model=ChatResponse)
async def chat_endpoint(req: ChatRequest):
    init_state = {
        "message": req.message,
        "image_url": str(req.image_url) if req.image_url else None,
        "trace": [],
    }
    result = await graph.ainvoke(init_state)
    return ChatResponse(
        mode=result.get("mode", "OUT_OF_SCOPE"),
        output=result.get("output", ""),
        trace=result.get("trace", []),
    )
