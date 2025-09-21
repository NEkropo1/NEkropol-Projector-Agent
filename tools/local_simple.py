
from __future__ import annotations
import re


def answer_casual(message: str) -> str:
    msg = message.strip().lower()

    # ultra basic
    if any(g in msg for g in ["hi", "hello", "hey"]):
        return "Hey. I'm the Projector engine. Drop a photo or a name and I'll riff."

    if "how are you" in msg:
        return "Functional. Waiting for a face, a name, or a myth to project onto."

    m = re.search(r"weather in ([a-zA-Z\s]+)", msg)
    if m:
        city = m.group(1).strip().title()
        return f"Local path only — no live weather yet. Pretend {city} is 22°C and moody."

    return "Casual path engaged. Ask me about a person — photo or name — and I'll project."
