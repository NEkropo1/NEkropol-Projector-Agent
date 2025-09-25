from fastapi import APIRouter, HTTPException
import schemas
from app.services import conversation

router = APIRouter()


@router.post("/chat", response_model=schemas.types.ChatResponse)
async def chat_endpoint(req: schemas.types.ChatRequest):
    try:
        result = await conversation.run_new(req.message, str(req.image_url) if req.image_url else None)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    return schemas.types.ChatResponse(**result)


@router.post("/chat/continue", response_model=schemas.types.ChatResponse)
async def chat_continue(req: schemas.types.ChatContinueRequest):
    try:
        result = await conversation.continue_conversation(req.conversation_id, req.message, str(req.image_url) if req.image_url else None)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return schemas.types.ChatResponse(**result)