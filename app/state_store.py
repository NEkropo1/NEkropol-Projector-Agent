from __future__ import annotations
import asyncio, time, uuid
from typing import Optional, Dict, Any

_TTL_SECONDS = 3600  # 1h
_store: Dict[str, Dict[str, Any]] = {}
_lock = asyncio.Lock()


def _now() -> float:
    return time.time()


async def new_conversation(state: Dict[str, Any]) -> str:
    cid = uuid.uuid4().hex
    async with _lock:
        _store[cid] = {"state": state, "expires_at": _now() + _TTL_SECONDS}
    return cid


async def get_state(cid: str) -> Optional[Dict[str, Any]]:
    async with _lock:
        entry = _store.get(cid)
        if not entry:
            return None
        if entry["expires_at"] < _now():
            _store.pop(cid, None)
            return None
        # return a shallow copy to avoid accidental mutation
        return {**entry["state"]}


async def save_state(cid: str, state: Dict[str, Any]) -> bool:
    async with _lock:
        entry = _store.get(cid)
        if not entry:
            return False
        entry["state"] = state
        return True


async def close_conversation(cid: str) -> None:
    async with _lock:
        _store.pop(cid, None)


async def expires_at(cid: str) -> Optional[float]:
    async with _lock:
        entry = _store.get(cid)
        return entry["expires_at"] if entry else None
