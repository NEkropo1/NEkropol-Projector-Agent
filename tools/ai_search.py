from openai import OpenAI
from app.settings import settings

_client = None


def client() -> OpenAI:
    global _client
    if _client is None:
        _client = OpenAI(api_key=settings.openai_api_key, base_url=settings.openai_base_url or None)
    return _client


def web_search_preview(query: str, model: str | None = None) -> dict:
    mdl = model or settings.openai_model_gpt
    resp = client().responses.create(
        model=mdl,
        input=query,
        tools=[{"type": "web_search_preview"}],
    )
    
    # prefer SDK's output_text; fallback reconstruct
    out_text = getattr(resp, "output_text", None)
    if out_text is None:
        try:
            blocks = resp.output[0].content if hasattr(resp, "output") else []
            pieces = []
            for b in blocks:
                if b.get("type") in ("output_text", "text") and "text" in b:
                    pieces.append(b["text"])
            out_text = "\n".join([p for p in pieces if p])
        except Exception:
            out_text = ""
    return {"output_text": out_text, "raw": resp.model_dump() if hasattr(resp, "model_dump") else resp}
