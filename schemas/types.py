
from __future__ import annotations

from pydantic import BaseModel, HttpUrl, Field
from typing import Optional, Literal, List, Dict, Any


Mode = Literal["PERSON_PHOTO", "PERSON_METADATA", "CASUAL", "OUT_OF_SCOPE"]


class ChatRequest(BaseModel):
    message: str = Field(..., description="User text")
    image_url: Optional[HttpUrl] = Field(None, description="Optional image URL")


class TraceStep(BaseModel):
    step: str
    data: Dict[str, Any] = Field(default_factory=dict)


class ChatResponse(BaseModel):
    mode: Mode
    output: str
    trace: List[TraceStep] = Field(default_factory=list)
