
from __future__ import annotations

import re
from typing import Optional
from schemas.types import Mode


PERSON_PHOTO_HINTS = (
    r"\b(photo|image|picture|pic|selfie)\b",
)

PERSON_META_HINTS = (
    r"\bwhat do you think of\b",
    r"\bwho is\b",
    r"\btell me about\b",
)


def classify(message: str, image_url: Optional[str]) -> Mode:
    # TODO: here we should implement small model/api call, to ensure we have right criteria, not just on re patterns
    # TODO: also we should ensure that it aligns with our OpenAPI structure,
    #  and we have enough info, or ask to give more info within template.
    #  If info is not enough, we need to ask for more info and provide expected structure
    msg = message.strip().lower()

    if image_url:
        return "PERSON_PHOTO"

    if any(re.search(p, msg) for p in PERSON_META_HINTS):
        # e.g. "what do you think of Vitalik" / "who is X"
        return "PERSON_METADATA"

    # super-basic casuals
    if any(x in msg for x in ["hi", "hello", "hey", "how are you", "weather"]):
        return "CASUAL"

    # Safety brake for everything else for now
    return "OUT_OF_SCOPE"
