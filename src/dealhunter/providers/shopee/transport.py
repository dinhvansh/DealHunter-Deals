import json
from pathlib import Path
from typing import Any, Protocol

import httpx
from playwright.async_api import BrowserContext, Playwright, async_playwright

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
        try:
            response = await self.client.get(url, params=params)
        except httpx.HTTPError as exc:
            raise ProviderError(f"provider request failed: {type(exc).__name__}: {exc}") from exc

        if response.status_code in {403, 429}:
            raise ProviderBlockedError(f"provider returned HTTP {response.status_code}")
        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            raise ProviderError(f"provider returned HTTP {response.status_code}") from exc
        try:
            return response.json()
        except ValueError as exc:
            raise ProviderError("provider did not return JSON") from exc

    async def aclose(self) -> None:
        await self.client.aclose()


class ChromeJsonTransport:
    """Google Chrome Stable transport with a persistent browser profile.

    This transport uses Playwright only as the controller. Browser execution is delegated to
    branded Google Chrome via ``channel='chrome'`` (or an explicit Chrome executable path).
    It does not bypass CAPTCHA, login challenges, or marketplace access controls.
    """

    def __init__(
        self,
        base_url: str,
        timeout: float = 30.0,
        profile_dir: str = "./data/chrome-profile",
        headless: bool = True,
        executable_path: str | None = None,
    ):
        self.base_url = base_url.rstrip("/")
        self.timeout_ms = int(timeout * 1000)
        self.profile_dir = Path(profile_dir)
        self.headless = headless
        self.executable_path = executable_path
        self._pw: Playwright | None = None
        self._context: BrowserContext | None = None
        self._page = None

    async def _ensure_page(self):
        if self._page:
            return self._page

        self.profile_dir.mkdir(parents=True, exist_ok=True)
        self._pw = await async_playwright().start()

        launch_kwargs: dict[str, Any] = {
            "user_data_dir": str(self.profile_dir),
            "headless": self.headless,
            "locale": "vi-VN",
        }
        if self.executable_path:
            launch_kwargs["executable_path"] = self.executable_path
        else:
            launch_kwargs["channel"] = "chrome"

        try:
            self._context = await self._pw.chromium.launch_persistent_context(**launch_kwargs)
        except Exception as exc:
            await self._pw.stop()
            self._pw = None
            raise ProviderError(
                "Google Chrome Stable could not be launched. Install Chrome on an amd64/x86_64 "
                "host or set DEALHUNTER_CHROME_EXECUTABLE_PATH."
            ) from exc

        self._page = self._context.pages[0] if self._context.pages else await self._context.new_page()
        self._page.set_default_timeout(self.timeout_ms)
        try:
            await self._page.goto(self.base_url, wait_until="domcontentloaded")
        except Exception as exc:
            await self.aclose()
            raise ProviderError(
                f"Google Chrome launched but Shopee bootstrap navigation failed: "
                f"{type(exc).__name__}: {exc}"
            ) from exc
        return self._page

    async def get_json(
        self,
        url: str,
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        page = await self._ensure_page()
        request_url = str(httpx.URL(url, params=params))
        try:
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
        except Exception as exc:
            raise ProviderError(
                f"Google Chrome provider request failed: {type(exc).__name__}: {exc}"
            ) from exc

        if result["status"] in (403, 429):
            raise ProviderBlockedError(f"provider returned HTTP {result['status']}")
        if result["status"] >= 400:
            raise ProviderError(f"provider returned HTTP {result['status']}")
        try:
            return json.loads(result["text"])
        except json.JSONDecodeError as exc:
            raise ProviderError("provider did not return JSON") from exc

    async def aclose(self) -> None:
        if self._context:
            await self._context.close()
            self._context = None
            self._page = None
        if self._pw:
            await self._pw.stop()
            self._pw = None


# Backward-compatible name. Browser-backed collection now uses Google Chrome Stable.
PlaywrightJsonTransport = ChromeJsonTransport
