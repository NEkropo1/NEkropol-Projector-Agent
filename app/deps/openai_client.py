
from __future__ import annotations

import asyncio
from typing import Optional
from tenacity import retry, stop_after_attempt, wait_exponential

from openai import OpenAI
from app.settings import settings


_client: OpenAI | None = None


def get_client() -> OpenAI:
    global _client
    if _client is None:
        _client = OpenAI(
            api_key=settings.openai_api_key,
            base_url=settings.openai_base_url or None,
        )
    return _client


@retry(wait=wait_exponential(min=1, max=8), stop=stop_after_attempt(3))
def _chat_sync(
    messages: list[dict],
    model: str,
    max_tokens: int | None = None,
    temperature: float = 0.2,
    response_format: Optional[dict] = None,
) -> str:
    client = get_client()
    kwargs = dict(model=model, messages=messages, temperature=temperature)
    if max_tokens is not None:
        kwargs["max_tokens"] = max_tokens
    if response_format is not None:
        kwargs["response_format"] = response_format
    resp = client.chat.completions.create(**kwargs)
    return resp.choices[0].message.content or ""


async def chat(
    messages: list[dict],
    model: str | None = None,
    max_tokens: int | None = None,
    temperature: float = 0.2,
    response_format: Optional[dict] = None,
) -> str:
    """Async wrapper around sync OpenAI client to play nice with FastAPI."""
    mdl = model or settings.openai_model_gpt
    return await asyncio.to_thread(
        _chat_sync,
        messages,
        mdl,
        max_tokens,
        temperature,
        response_format,
    )
