from __future__ import annotations

from pathlib import Path

from app.deps.openai_client import chat
from app.settings import settings
from agents.router import classify as classify_message
from agents.base import GraphState, add_trace
from guards.photo_guard import image_has_person
from schemas.types import Mode

PROMPTS_DIR = Path(__file__).resolve().parent / "prompts"


def _load_text(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


SYSTEM_PROMPT = _load_text(PROMPTS_DIR / "projector_system.md")
PROJECT_PROMPT = _load_text(PROMPTS_DIR / "project_prompt.md")


async def node_classify(state: GraphState) -> GraphState:
    msg = state.get("message", "")
    image_url = state.get("image_url")
    mode: Mode = classify_message(msg, image_url)
    state["mode"] = mode
    add_trace(state, "classified", {"mode": mode})
    return state


async def _projector_call(prompt_user: str, image_url: str | None = None) -> str:
    system_text = SYSTEM_PROMPT.strip()
    if PROJECT_PROMPT.strip():
        system_text += "\n\n[Foundation]\n" + PROJECT_PROMPT.strip()

    messages = [
        {"role": "system", "content": system_text},
    ]

    if image_url:

        messages.append({
            "role": "user",
            "content": [
                {"type": "text", "text": prompt_user},
                {"type": "image_url", "image_url": {"url": image_url}},
            ]
        })
    else:
        messages.append({"role": "user", "content": prompt_user})

    result = await chat(messages, model=settings.openai_model_gpt, temperature=0.7)

    return result


async def node_handle_photo(state: GraphState) -> GraphState:
    msg = state.get("message", "")
    image_ref = state.get("image_url")

    ok = image_has_person(image_ref) if image_ref else False
    add_trace(state, "photo_validated", {"image_present": bool(image_ref), "has_person": ok})

    if not ok:
        state["output"] = (
            "I couldn’t confidently detect a person in that image. "
            "Share a clearer face photo (good lighting, front view), "
            "or tell me a bit more (name, role, nickname)."
        )
        state["next_action"] = "need_better_photo"
        return state

    add_trace(state, "projector_photo_start", {"image_url": image_ref})
    prompt = (
        "Given the image, play the Projector: speculate about this person's role, "
        "vibes, likely profession or archetype. Entertainment-only."
    )
    state["output"] = await _projector_call(f"{prompt}\n\nUser text: {msg}", image_url=image_ref)
    add_trace(state, "projector_photo_done", {})
    state["next_action"] = "none"  # explicit end-state
    return state


async def node_handle_meta(state: GraphState) -> GraphState:
    msg = state.get("message", "")
    add_trace(state, "projector_meta_start", {})
    # Later: enrich via search tool
    prompt_user = (
        "User gave a name/creds/nickname. Without external search, project "
        "entertaining inferences about likely roles/archetypes. "
        "Be explicit that this is playful speculation."
    )
    result = await _projector_call(prompt_user + "\n\nUser text: " + msg)
    state["output"] = result
    add_trace(state, "projector_meta_done", {})
    return state


async def node_handle_casual(state: GraphState) -> GraphState:
    # no OpenAI call — super cheap path; expand later to local embeddings/search
    from tools.local_simple import answer_casual
    msg = state.get("message", "")
    add_trace(state, "casual_start", {})
    state["output"] = answer_casual(msg)
    add_trace(state, "casual_done", {})
    return state


async def node_handle_oos(state: GraphState) -> GraphState:
    add_trace(state, "oos_start", {})
    state["output"] = (
        "I am NEkropol™ Agentic engine, built to create projector-style, entertainment-only takes.\n"
        "Your request is outside my scope. If you believe it isn't, provide a photo or clear persona info."
    )
    add_trace(state, "oos_done", {})
    return state
