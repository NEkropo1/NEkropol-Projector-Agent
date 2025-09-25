import re
from typing import List
from urllib.parse import urljoin, urlparse
from playwright.async_api import Page


async def get_visible_text(page: Page, max_chars: int = 20000) -> str:
    js = """
    (() => {
      const rm = sel => document.querySelectorAll(sel).forEach(n => n.remove());
      rm('script,style,noscript,template,iframe,header,footer,nav,form,aside,svg');
      const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
      const chunks = [];
      while (walker.nextNode()) {
        const t = walker.currentNode.textContent;
        if (t && t.trim()) chunks.push(t.trim());
      }
      return chunks.join(' ');
    })()
    """
    txt = await page.evaluate(js)
    txt = re.sub(r"\s+", " ", txt or "").strip()
    return txt[:max_chars]


async def get_links(page: Page, base_url: str, link_css: str = "a", same_host_only: bool = False) -> List[str]:
    hrefs = await page.eval_on_selector_all(link_css, "els => els.map(e => e.getAttribute('href')).filter(Boolean)")
    urls, seen = [], set()
    base_host = urlparse(base_url).netloc
    for h in hrefs:
        u = urljoin(base_url, h)
        if same_host_only and urlparse(u).netloc != base_host:
            continue
        if u not in seen:
            seen.add(u)
            urls.append(u)
    return urls
