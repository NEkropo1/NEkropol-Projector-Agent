from typing import List, Dict
import httpx
from bs4 import BeautifulSoup

DEFAULT_HEADERS = {"User-Agent": "ProjectorBot/0.1 (+https://example.invalid)",
                   "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"}
TIMEOUT = httpx.Timeout(10.0, read=15.0)


def fetch_visible_text(url: str, max_chars: int = 15000) -> str:
    with httpx.Client(follow_redirects=True, timeout=TIMEOUT, headers=DEFAULT_HEADERS) as client:
        response = client.get(url)
        response.raise_for_status()
        html = response.text

    soup = BeautifulSoup(html, "lxml")
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()
    for tag in soup.select("header, footer, nav, form, aside"):
        tag.decompose()

    text = " ".join(soup.get_text(" ").split())
    return text[:max_chars]


def provider_search(query: str, k: int = 5) -> List[Dict[str, str]]:
    # stub — return [{title, url, snippet}, ...] when you wire a provider
    return []


def cheap_gather(query: str, k: int = 5, max_chars_per_page: int = 8000) -> Dict[str, str]:
    hits = provider_search(query, k=k) or []
    out: Dict[str, str] = {}
    for h in hits[:k]:
        url = h.get("url")
        if not url:
            continue

        try:
            out[url] = fetch_visible_text(url, max_chars=max_chars_per_page)
        except Exception:
            continue

    return out
