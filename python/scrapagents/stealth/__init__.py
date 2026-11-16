"""Stealth browsing: playwright paired with obscura.sh (architectural invariant 3)."""

from scrapagents.stealth.base import ObscuraConfig, PageSnapshot, StealthRouter
from scrapagents.stealth.encoding import decode_html, detect_charset
from scrapagents.stealth.playwright_obscura import PlaywrightObscuraRouter

__all__ = [
    "ObscuraConfig",
    "PageSnapshot",
    "PlaywrightObscuraRouter",
    "StealthRouter",
    "decode_html",
    "detect_charset",
]
