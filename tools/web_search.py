
from __future__ import annotations


def search_public_info(query: str) -> dict:
    """
    TODO: Wire a real search provider (Bing/SerpAPI) and cache_db.
    Return minimal structured info usable by the projector.
    """
    return {"query": query, "hits": []}
