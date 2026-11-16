"""Robust HTML/text encoding utilities for international character sets.

Supports UTF-8, GBK, GB18030, Big5, and common fallbacks.
"""

from __future__ import annotations

import re

CHARSET_RE = re.compile(r"charset\s*=\s*['\"]?([\w-]+)", re.IGNORECASE)


def detect_charset(body: bytes, content_type: str | None = None) -> str | None:
    """Extract charset from Content-Type header or HTML meta tag."""
    if content_type:
        match = CHARSET_RE.search(content_type)
        if match:
            return match.group(1).strip().lower()

    # Search in the first 2048 bytes of the body for <meta charset="...">
    head = body[:2048].decode("ascii", errors="ignore")
    match = CHARSET_RE.search(head)
    if match:
        return match.group(1).strip().lower()
    return None


def decode_html(body: bytes, content_type: str | None = None) -> str:
    """Decode raw HTML bytes using detected charset, UTF-8, GB18030, or fallback."""
    if not body:
        return ""

    charset = detect_charset(body, content_type)
    if charset:
        normalized = "gb18030" if charset in {"gb2312", "gbk"} else charset
        try:
            return body.decode(normalized)
        except (LookupError, UnicodeDecodeError):
            pass

    # Try UTF-8 first
    try:
        return body.decode("utf-8")
    except UnicodeDecodeError:
        pass

    # Try GB18030 for CJK characters
    try:
        return body.decode("gb18030")
    except UnicodeDecodeError:
        pass

    # Fallback to UTF-8 with replacement
    return body.decode("utf-8", errors="replace")
