
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, HttpUrl, Field
from typing import Optional, Literal, List, Dict, Any


Mode = Literal["PERSON_PHOTO", "PERSON_METADATA", "CASUAL", "OUT_OF_SCOPE"]
NextAction = Literal["need_better_photo", "ask_for_more_details", "none"]


class ChatRequest(BaseModel):
    message: str
    image_url: Optional[HttpUrl] = None
    conversation_id: Optional[str] = None


class ChatContinueRequest(BaseModel):
    conversation_id: str
    message: Optional[str] = None
    image_url: Optional[HttpUrl] = None


class TraceStep(BaseModel):
    step: str
    data: Dict[str, Any] = Field(default_factory=dict)


class ChatResponse(BaseModel):
    mode: Mode
    output: str
    trace: List[TraceStep] = Field(default_factory=list)
    conversation_id: Optional[str] = None
    next_action: Optional[NextAction] = None
    expires_at: Optional[datetime] = None
