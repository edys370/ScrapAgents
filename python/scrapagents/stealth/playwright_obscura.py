"""``StealthRouter`` backed by playwright (sync API) and ``ObscuraConfig``."""

from __future__ import annotations

import logging
from types import TracebackType
from typing import Any

from scrapagents.stealth.base import ObscuraConfig, PageSnapshot

logger = logging.getLogger(__name__)

# Images, stylesheets and fonts. The HTML the extractors parse does not need them, and a
# truncated asset download is a common way gov.cn closes the connection mid-body.
_STATIC_TYPES = frozenset({"image", "stylesheet", "font"})
_STATIC_SUFFIXES = (".png", ".jpg", ".jpeg", ".gif", ".svg", ".css", ".woff", ".woff2")

CAPTCHA_MARKERS = (
    "g-recaptcha",
    "h-captcha",
    "cf-turnstile",
    "captcha-delivery",
    "geetest",
    "安全验证",
    "滑动验证",
    "验证码",
    "sec-defend",
    "validatecaptcha",
    "images-amazon.com/captcha",
    "robot check",
)
WAF_MARKERS = (
    "just a moment...",
    "attention required",
    "access denied",
    "request unsuccessful",
    "safedog",
    "网站防火墙",
    "您的访问过于频繁",
    "访问拦截",
    "访问受限",
    "403 forbidden",
    "awswaf",
    "token.awswaf.com",
    "challenge-container",
)


def should_block_static(resource_type: str, url: str) -> bool:
    """True for images, stylesheets and fonts the page does not need in order to be parsed."""
    if resource_type in _STATIC_TYPES:
        return True
    path = url.lower().split("?", 1)[0].split("#", 1)[0]
    return path.endswith(_STATIC_SUFFIXES)


def _abort_static(route: Any) -> None:
    request = route.request
    if should_block_static(request.resource_type, request.url):
        route.abort()
        return
    route.continue_()


def detect_block(status: int | None, html: str) -> str | None:
    """Classify an anti-bot barrier from the response, or ``None`` when the page looks open."""

    lowered = html.lower()
    if any(marker in lowered for marker in CAPTCHA_MARKERS):
        return "captcha"
    if status in (403, 429) or any(marker in lowered for marker in WAF_MARKERS):
        return "waf"
    return None


class PlaywrightObscuraRouter:
    """Playwright connected to Obscura over CDP. playwright is imported lazily.

    With ``OBSCURA_CDP_URL`` the browser is the remote Obscura instance and is never closed by us
    (only the pages and the connection). Without it (``OBSCURA_REQUIRED=0``, local development) a
    local Chromium is launched instead.
    """

    def __init__(self, config: ObscuraConfig | None = None) -> None:
        self._config = config or ObscuraConfig.from_env()
        self._playwright: Any = None
        self._browser: Any = None
        self._context: Any = None
        self._block_static = False

    def enable_static_blocking(self) -> None:
        """Abort images, stylesheets and fonts on later ``fetch`` calls."""
        self._block_static = True

    def _start(self) -> Any:
        if self._context is not None:
            return self._context
        try:
            from playwright.sync_api import sync_playwright  # noqa: PLC0415
        except ImportError as exc:  # pragma: no cover - depends on the optional extra
            raise RuntimeError("playwright is missing: pip install '.[probes]'") from exc
        self._playwright = sync_playwright().start()
        if self._config.cdp_url:
            headers = (
                {"Authorization": f"Bearer {self._config.cdp_token}"}
                if self._config.cdp_token
                else None
            )
            self._browser = self._playwright.chromium.connect_over_cdp(
                self._config.cdp_url, headers=headers
            )
        else:  # local development only (OBSCURA_REQUIRED=0)
            self._browser = self._playwright.chromium.launch(headless=True)
        # Sites with incomplete or corporate TLS chains (e.g. CAF) fail navigation unless TLS
        # errors are ignored at the browser context. Recorded for H1; never a bypass of WAF/captcha.
        context_args: dict[str, Any] = {"ignore_https_errors": True}
        if self._config.user_agent:
            context_args["user_agent"] = self._config.user_agent
        if self._config.locale:
            context_args["locale"] = self._config.locale
        default_lang = (
            self._config.accept_language
            or "zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7,es;q=0.6"
        )
        context_args["extra_http_headers"] = {"Accept-Language": default_lang}
        self._context = self._browser.new_context(**context_args)
        return self._context

    def fetch(self, url: str, *, timeout_seconds: float | None = None) -> PageSnapshot:
        effective_timeout = (
            timeout_seconds
            if timeout_seconds is not None
            else self._config.timeout_seconds
        )
        page = self._start().new_page()
        try:
            if self._block_static:
                try:
                    page.route("**/*", _abort_static)
                except Exception as exc:  # noqa: BLE001 - Obscura may not implement Fetch interception
                    logger.warning("Static-resource blocking is unavailable: %s", exc)
                    self._block_static = False
            response = page.goto(
                url, timeout=effective_timeout * 1000, wait_until="domcontentloaded"
            )
            status = response.status if response else None
            content_type = response.headers.get("content-type") if response else None
            html = page.content()
            try:
                body = response.body() if response else b""
            except Exception:
                body = html.encode("utf-8")
            return PageSnapshot(url, status, content_type, html, detect_block(status, html), body)
        finally:
            page.close()

    def close(self) -> None:
        if self._context is not None:
            self._context.close()
        if self._browser is not None:
            self._browser.close()  # over CDP this disconnects; the remote Obscura keeps running
        if self._playwright is not None:
            self._playwright.stop()
        self._playwright = self._browser = self._context = None

    def __enter__(self) -> PlaywrightObscuraRouter:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        self.close()
