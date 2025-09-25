from __future__ import annotations
from tenacity import retry, stop_after_attempt, wait_exponential
from openai import AsyncOpenAI
from app.settings import settings

_client: AsyncOpenAI | None = None


def get_client() -> AsyncOpenAI:
    global _client
    if _client is None:
        _client = AsyncOpenAI(
            api_key=settings.openai_api_key,
            base_url=settings.openai_base_url or None,
        )
    return _client


@retry(wait=wait_exponential(min=1, max=8), stop=stop_after_attempt(3))
async def chat(
    messages,
    model=None,
    max_tokens=None,
    temperature: float = 0.2,
    response_format=None,
) -> str:
    mdl = model or settings.openai_model_gpt
    client = get_client()
    resp = await client.chat.completions.create(
        model=mdl,
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
        response_format=response_format,
    )
    return resp.choices[0].message.content or ""
