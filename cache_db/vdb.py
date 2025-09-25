# cache_db/vdb.py
from __future__ import annotations

import os
import time
from typing import Optional

import chromadb
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

_DB_PATH = os.getenv("CACHE_DB_PATH", ".cache_db/chroma")
os.makedirs(_DB_PATH, exist_ok=True)

_client = chromadb.Client(chromadb.config.Settings(persist_directory=_DB_PATH))
_coll = _client.get_or_create_collection(name="persona_cache")


def _similarity(a: str, b: str) -> float:
    v = TfidfVectorizer(ngram_range=(1, 2))
    x = v.fit_transform([a, b])
    return float(cosine_similarity(x[0], x[1])[0, 0])


def get_cached_answer(query: str, thr: float = 0.80) -> Optional[dict]:
    ids = _coll.get(include=["documents", "metadatas"]).get("ids", [])
    docs = _coll.get(include=["documents", "metadatas"]).get("documents", [])
    metas = _coll.get(include=["documents", "metadatas"]).get("metadatas", [])
    best = (-1.0, None)
    for i, (doc, meta) in enumerate(zip(docs, metas)):
        sim = _similarity(query, meta.get("query", ""))
        if sim > best[0]: best = (sim, (ids[i], doc, meta))
    if best[0] >= thr and best[1]:
        _, (doc_id, doc, meta) = best
        return {"id": doc_id, "answer": doc, "meta": meta, "similarity": best[0]}
    return None


def put_cached_answer(query: str, answer: str, meta: dict) -> None:
    _coll.add(ids=[str(time.time())], documents=[answer], metadatas=[{"query": query, **meta}])
    _client.persist()
