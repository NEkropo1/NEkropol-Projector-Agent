from __future__ import annotations
import asyncio
from contextlib import asynccontextmanager
from typing import Optional
from playwright.async_api import async_playwright, Browser, BrowserContext, Page, TimeoutError as PWTimeoutError


class PlaywrightClient:
    def __init__(
            self,
            headless: bool = True,
            max_pages: int = 8,
            user_agent: Optional[str] = None,
            proxy: Optional[str] = None,
            default_timeout_ms: int = 12000
    ) -> None:
        self._headless = headless
        self._max_pages = max_pages
        self._user_agent = user_agent
        self._proxy = proxy
        self._default_timeout_ms = default_timeout_ms
        self._pw = None
        self._browser: Optional[Browser] = None
        self._ctx: Optional[BrowserContext] = None
        self._sem = asyncio.Semaphore(max_pages)

    async def start(self) -> None:
        if self._browser:
            return

        self._pw = await async_playwright().start()
        launch_args = dict(headless=self._headless, args=["--disable-dev-shm-usage", "--no-sandbox"])
        if self._proxy:
            launch_args["proxy"] = {"server": self._proxy}
        self._browser = await self._pw.chromium.launch(**launch_args)
        ctx_args = {"user_agent": self._user_agent} if self._user_agent else {}
        self._ctx = await self._browser.new_context(**ctx_args)

    async def stop(self) -> None:
        if self._ctx: await self._ctx.close(); self._ctx = None
        if self._browser: await self._browser.close(); self._browser = None
        if self._pw: await self._pw.stop(); self._pw = None

    @asynccontextmanager
    async def page(self) -> Page:
        if not self._ctx: await self.start()
        assert self._ctx
        await self._sem.acquire()
        page = await self._ctx.new_page()
        page.set_default_timeout(self._default_timeout_ms)
        try:
            yield page
        finally:
            await page.close()
            self._sem.release()

    async def goto(self, page: Page, url: str, total_timeout_s: int = 20) -> None:
        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=total_timeout_s * 1000)
            try:
                await page.wait_for_load_state("networkidle", timeout=min(4000, total_timeout_s * 1000))
            except PWTimeoutError:
                pass
        except PWTimeoutError:
            return
