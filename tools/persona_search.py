from __future__ import annotations
import asyncio
from urllib.parse import urljoin
from typing import List, Dict, Any, Optional

from app import settings
from browser.manager import PlaywrightClient
from browser.extract import get_visible_text
from browser.relevance import score_relevance

import httpx

_GOOGLE = settings.google_url

MIN_W = 160
MIN_H = 160
MAX_AR = 3.5  # aspect ratio fence for sprites/banners


async def _google_urls(query: str, max_results: int = 5) -> List[str]:
    pc = PlaywrightClient(max_pages=3)
    await pc.start()
    try:
        async with pc.page() as p:
            await pc.goto(p, f"{_GOOGLE}{query}", total_timeout_s=15)
            hrefs = await p.eval_on_selector_all(
                "a", "els => els.map(e => e.getAttribute('href')).filter(Boolean)"
            )

        urls: List[str] = []
        for h in hrefs:
            if h.startswith("/url?q="):
                real = h.split("/url?q=")[1].split("&")[0]
                if "google.com" not in real:
                    urls.append(real)

        # dedupe preserving order
        seen, out = set(), []
        for u in urls:
            if u not in seen:
                seen.add(u); out.append(u)
        return out[:max_results]
    finally:
        await pc.stop()


async def _best_image_on_page(page, base_url: str) -> Optional[str]:
    # 1) meta images
    meta_img = await page.evaluate("""
    () => {
      const pick = (sel) => {
        const el = document.querySelector(sel);
        if (!el) return null;
        return el.getAttribute('content') || el.getAttribute('value') || null;
      };
      return pick('meta[property="og:image"]') ||
             pick('meta[name="og:image"]') ||
             pick('meta[name="twitter:image"]') ||
             pick('meta[property="twitter:image"]');
    }
    """)
    if meta_img:
        return urljoin(base_url, meta_img)

    # 2) gather candidates (img + srcset)
    candidates = await page.evaluate("""
    () => {
      const urls = new Set();
      const imgs = Array.from(document.images || []);
      imgs.forEach(img => {
        if (img.src) urls.add(img.src);
        // srcset parsing
        if (img.srcset) {
          img.srcset.split(',').forEach(s => {
            const u = s.trim().split(' ')[0];
            if (u) urls.add(u);
          });
        }
      });
      // <source srcset> inside <picture>
      document.querySelectorAll('source[srcset]').forEach(s => {
        s.srcset.split(',').forEach(t => {
          const u = t.trim().split(' ')[0];
          if (u) urls.add(u);
        });
      });

      // Collect render metrics to filter junk
      const scored = [];
      imgs.forEach(img => {
        const w = img.naturalWidth || img.width || 0;
        const h = img.naturalHeight || img.height || 0;
        const ar = h > 0 ? (w / h) : 0;
        if (w >= 80 && h >= 80) { // very loose, we’ll tighten host-side
          scored.push({url: img.src, w, h, ar});
        }
      });
      return {urls: Array.from(urls), scored};
    }
    """)

    # normalize + filter by size/aspect
    scored = []
    for it in (candidates.get("scored") or []):
        u = urljoin(base_url, it["url"])
        w, h, ar = int(it["w"]), int(it["h"]), float(it["ar"] or 0)
        if w >= MIN_W and h >= MIN_H and 0.1 <= ar <= MAX_AR and not u.startswith("data:"):
            scored.append((u, w * h))
    if scored:
        # pick the largest pixel area
        scored.sort(key=lambda x: x[1], reverse=True)
        return scored[0][0]

    # fallback: first absolute URL that looks like an image
    for raw in (candidates.get("urls") or []):
        if raw and not raw.startswith("data:"):
            return urljoin(base_url, raw)
    return None


def _head_ok(url: str, min_bytes: int = 5_000, timeout: float = 6.0) -> bool:
    try:
        with httpx.Client(timeout=timeout, follow_redirects=True) as c:
            r = c.head(url)
            if r.status_code >= 400:
                return False
            clen = r.headers.get("Content-Length")
            if clen and clen.isdigit():
                return int(clen) >= min_bytes
            return True
    except Exception:
        return False


async def _page_text_and_image(pc: PlaywrightClient, url: str, timeout_s: int = 15) -> Dict[str, Any]:
    async with pc.page() as p:
        await pc.goto(p, url, total_timeout_s=timeout_s)
        text = await get_visible_text(p)
        img = await _best_image_on_page(p, url)
        if img and not _head_ok(img):
            img = None
        return {"url": url, "text": text, "img": img}


async def persona_search_bundle(query: str, max_results: int = 5, timeout_s: int = 20) -> Dict[str, Any]:
    urls = await _google_urls(query, max_results=max_results)
    pc = PlaywrightClient(max_pages=min(6, max_results))
    await pc.start()
    try:
        tasks = [asyncio.create_task(_page_text_and_image(pc, u, timeout_s)) for u in urls]
        pages = await asyncio.gather(*tasks)

        texts = [p["text"] for p in pages]
        scores = score_relevance(query, texts)
        ranked = sorted(
            [{"url": p["url"], "text": t, "img": p["img"], "score": float(s)}
             for p, t, s in zip(pages, texts, scores)],
            key=lambda d: d["score"], reverse=True,
        )

        best_img = next((d["img"] for d in ranked if d["img"]), None)

        bullets = []
        for d in ranked[:5]:
            snippet = d["text"][:300].replace("\n", " ")
            bullets.append(f"- {d['url']} :: {snippet}")
        context = "\n".join(bullets)[:4000]

        return {"docs": ranked, "context": context, "image_url": best_img}
    finally:
        await pc.stop()
