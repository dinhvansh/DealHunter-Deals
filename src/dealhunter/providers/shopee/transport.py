import json
from typing import Any, Protocol

import httpx
from playwright.async_api import Browser, Playwright, async_playwright

from dealhunter.providers.errors import ProviderBlockedError, ProviderError


class JsonTransport(Protocol):
    async def get_json(
        self,
        url: str,
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]: ...

    async def aclose(self) -> None: ...


class HttpJsonTransport:
    def __init__(self, timeout: float = 30.0):
        self.client = httpx.AsyncClient(
            timeout=timeout,
            follow_redirects=True,
            headers={
                "accept": "application/json,text/plain,*/*",
                "accept-language": "vi-VN,vi;q=0.9,en;q=0.8",
                "user-agent": "Mozilla/5.0 DealHunter/0.1",
            },
        )

    async def get_json(
        self,
        url: str,
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        response = await self.client.get(url, params=params)
        if response.status_code in {403, 429}:
            raise ProviderBlockedError(f"provider returned HTTP {response.status_code}")
        response.raise_for_status()
        try:
            return response.json()
        except ValueError as exc:
            raise ProviderError("provider did not return JSON") from exc

    async def aclose(self) -> None:
        await self.client.aclose()


class PlaywrightJsonTransport:
    """Browser-backed public fetch transport; it does not bypass CAPTCHA/login challenges."""

    def __init__(self, base_url: str, timeout: float = 30.0):
        self.base_url = base_url.rstrip("/")
        self.timeout_ms = int(timeout * 1000)
        self._pw: Playwright | None = None
        self._browser: Browser | None = None
        self._page = None

    async def _ensure_page(self):
        if self._page:
            return self._page
        self._pw = await async_playwright().start()
        self._browser = await self._pw.chromium.launch(headless=True)
        context = await self._browser.new_context(locale="vi-VN")
        self._page = await context.new_page()
        self._page.set_default_timeout(self.timeout_ms)
        await self._page.goto(self.base_url, wait_until="domcontentloaded")
        return self._page

    async def get_json(
        self,
        url: str,
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        page = await self._ensure_page()
        request_url = str(httpx.URL(url, params=params))
        result = await page.evaluate(
            """async (url) => {
                const r = await fetch(url, {
                    credentials: 'include',
                    headers: {'accept': 'application/json,text/plain,*/*'}
                });
                return {status: r.status, text: await r.text()};
            }""",
            request_url,
        )
        if result["status"] in (403, 429):
            raise ProviderBlockedError(f"provider returned HTTP {result['status']}")
        if result["status"] >= 400:
            raise ProviderError(f"provider returned HTTP {result['status']}")
        try:
            return json.loads(result["text"])
        except json.JSONDecodeError as exc:
            raise ProviderError("provider did not return JSON") from exc

    async def aclose(self) -> None:
        if self._browser:
            await self._browser.close()
        if self._pw:
            await self._pw.stop()
