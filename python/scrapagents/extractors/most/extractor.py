"""MOST extractor: scrape 科技计划通知公告 from service.most.gov.cn via Obscura → SourceRuntime."""

from __future__ import annotations

import argparse
import html as html_lib
import json
import logging
import os
import random
import re
import sys
import time
from collections.abc import Callable
from datetime import UTC, datetime
from typing import Any
from urllib.parse import urljoin

from scrapagents.contracts.loader import load_ingestion_config
from scrapagents.runtime_client import HttpRuntimeClient, RuntimeIngestError, SourceRuntimeClient
from scrapagents.stealth.base import ObscuraConfig, PageSnapshot, StealthRouter

logger = logging.getLogger(__name__)

SOURCE = "most"
DATASET = "funding_opportunities"
DEFAULT_USER_AGENT = "ScrapAgents-ingest-most/0.1 (research; non-commercial)"
DEFAULT_SITE = "https://service.most.gov.cn"
DEFAULT_LISTING_BASE = "/kjjh_tztg/"
DEFAULT_TIMEOUT_SECONDS = 45.0
DEFAULT_MAX_ATTEMPTS = 3
DEFAULT_BACKOFF_SECONDS = 1.5
DEFAULT_BACKOFF_CAP_SECONDS = 15.0
DEFAULT_PAUSE_MIN_SECONDS = 1.0
DEFAULT_PAUSE_MAX_SECONDS = 2.5
# Gateway and rate-limit answers are retried. A captcha or WAF page is not.
RETRYABLE_STATUS = frozenset({408, 429, 500, 502, 503, 504})
_TRANSIENT_MARKERS = (
    "timeout",
    "timed out",
    "deadline",
    "exceeded",
    "net::",
    "connection",
    "econnreset",
    "econnrefused",
    "target closed",
    "temporarily unavailable",
    "failed to read body",
    "decoding response body",
)
DEFAULT_MAX_DETAIL_FAILURES = 20

_TAG_RE = re.compile(r"<[^>]+>")
_FOOTER_RE = re.compile(r"共\s*(\d+)\s*条记录\s*(\d+)\s*/\s*(\d+)\s*页")
_ROW_RE = re.compile(r"<tr\b[^>]*>(.*?)</tr>", re.IGNORECASE | re.DOTALL)
_OPENW_RE = re.compile(
    r"""openW\(\s*['"](/kjjh_tztg_all/(\d{8})/(\d+)\.html)['"]\s*\)""",
    re.IGNORECASE,
)
_TITLE_ATTR_RE = re.compile(r'title="([^"]+)"', re.IGNORECASE)
_UNIT_RE = re.compile(
    r'class=["\']table_gkgs_unit["\'][^>]*(?:title="([^"]*)")?[^>]*>(.*?)</td>',
    re.IGNORECASE | re.DOTALL,
)
_DATE_RE = re.compile(
    r'class=["\']table_gkgs_date["\'][^>]*>(.*?)</td>',
    re.IGNORECASE | re.DOTALL,
)
_ARTICLE_TITLE_RE = re.compile(
    r'<h1\b[^>]*class=["\'][^"\']*article__title[^"\']*["\'][^>]*>(.*?)</h1>',
    re.IGNORECASE | re.DOTALL,
)
_ARTICLE_SUB_RE = re.compile(
    r'<p\b[^>]*class=["\'][^"\']*article__subTitle[^"\']*["\'][^>]*>(.*?)</p>',
    re.IGNORECASE | re.DOTALL,
)
_ARTICLE_BODY_RE = re.compile(
    r'<div\b[^>]*class=["\'][^"\']*article-body[^"\']*["\'][^>]*>(.*?)</div>\s*</div>',
    re.IGNORECASE | re.DOTALL,
)
_CN_DATE_RE = re.compile(r"(\d{4})\s*年\s*(\d{1,2})\s*月\s*(\d{1,2})\s*日")
_ISO_DATE_RE = re.compile(r"\b(20\d{2}-\d{2}-\d{2})\b")


def _retryable_snapshot(url: str, snapshot: PageSnapshot) -> RuntimeError | None:
    """A transient HTTP answer worth another attempt. Captcha and WAF pages are final."""
    if snapshot.blocked_by == "captcha":
        return None
    if snapshot.blocked_by == "waf" and snapshot.status not in RETRYABLE_STATUS:
        return None
    if snapshot.status in RETRYABLE_STATUS:
        return RuntimeError(f"{url} answered {snapshot.status}.")
    return None


def _clean_text(raw: str) -> str:
    text = html_lib.unescape(_TAG_RE.sub(" ", raw))
    return re.sub(r"\s+", " ", text).strip()


def parse_listing_footer(html: str) -> tuple[int, int, int] | None:
    """Return (total_records, current_page, total_pages) from the listing footer, if present."""
    match = _FOOTER_RE.search(html)
    if not match:
        return None
    return int(match.group(1)), int(match.group(2)), int(match.group(3))


def listing_page_path(listing_base: str, page: int) -> str:
    """Static listing path for page N (1 → index.html, 2+ → index_N.html)."""
    base = listing_base if listing_base.endswith("/") else listing_base + "/"
    if page <= 1:
        return f"{base}index.html"
    return f"{base}index_{page}.html"


def _normalize_date(raw: str) -> str | None:
    text = _clean_text(raw)
    iso = _ISO_DATE_RE.search(text)
    if iso:
        return iso.group(1)
    cn = _CN_DATE_RE.search(text)
    if cn:
        return f"{int(cn.group(1)):04d}-{int(cn.group(2)):02d}-{int(cn.group(3)):02d}"
    return None


def parse_listing_rows(html: str, *, listing_url: str, site: str) -> list[dict[str, Any]]:
    """Parse notice rows from a kjjh_tztg listing page."""
    records: list[dict[str, Any]] = []
    seen: set[str] = set()
    for row_html in _ROW_RE.findall(html):
        openw = _OPENW_RE.search(row_html)
        if not openw:
            continue
        detail_path, ymd, notice_id = openw.group(1), openw.group(2), openw.group(3)
        if notice_id in seen:
            continue
        seen.add(notice_id)

        title = None
        title_block = re.search(
            r'class=["\']table_gkgs_title["\'][^>]*>(.*?)</td>',
            row_html,
            re.IGNORECASE | re.DOTALL,
        )
        if title_block:
            attr = _TITLE_ATTR_RE.search(title_block.group(1))
            if attr:
                title = html_lib.unescape(attr.group(1)).strip()
            else:
                title = _clean_text(title_block.group(1))

        issuing_unit = None
        unit_match = _UNIT_RE.search(row_html)
        if unit_match:
            issuing_unit = (unit_match.group(1) or "").strip() or _clean_text(unit_match.group(2))

        publish_date = None
        date_match = _DATE_RE.search(row_html)
        if date_match:
            publish_date = _normalize_date(date_match.group(1))
        if not publish_date and len(ymd) == 8:
            publish_date = f"{ymd[0:4]}-{ymd[4:6]}-{ymd[6:8]}"

        if not title or not issuing_unit or not publish_date:
            continue

        records.append(
            {
                "notice_id": notice_id,
                "source_url": urljoin(site.rstrip("/") + "/", detail_path.lstrip("/")),
                "title": title,
                "issuing_unit": issuing_unit,
                "publish_date": publish_date,
                "listing_url": listing_url,
                "detail_path": detail_path,
            }
        )
    return records


def parse_detail_page(html: str) -> dict[str, str | None]:
    """Extract title, issuing_unit, publish_date and body_text from a notice detail page."""
    title_match = _ARTICLE_TITLE_RE.search(html)
    title = _clean_text(title_match.group(1)) if title_match else None

    issuing_unit = None
    publish_date = None
    sub_match = _ARTICLE_SUB_RE.search(html)
    if sub_match:
        sub = _clean_text(sub_match.group(1))
        src = re.search(r"来源[:：]\s*(.+)$", sub)
        if src:
            issuing_unit = src.group(1).strip() or None
        publish_date = _normalize_date(sub)

    body_match = _ARTICLE_BODY_RE.search(html)
    body_text = _clean_text(body_match.group(1)) if body_match else None
    if body_text == "":
        body_text = None

    return {
        "title": title,
        "issuing_unit": issuing_unit,
        "publish_date": publish_date,
        "body_text": body_text,
    }


def is_transient_fetch_error(exc: BaseException) -> bool:
    """True for navigation timeouts and dropped connections. A block page is not an exception."""
    if isinstance(exc, (TimeoutError, ConnectionError)):
        return True
    if type(exc).__name__ in {"TimeoutError", "TargetClosedError"}:
        return True
    if not type(exc).__module__.startswith("playwright"):
        return False
    text = str(exc).lower()
    return any(marker in text for marker in _TRANSIENT_MARKERS)


def backoff_seconds(attempt: int, *, base: float, cap: float) -> float:
    """Wait before retry number ``attempt`` (2 → base, 3 → 2·base, …), capped."""
    if attempt < 2:
        return 0.0
    return min(cap, base * (2 ** (attempt - 2)))


def pause_seconds(
    minimum: float,
    maximum: float,
    *,
    uniform: Callable[[float, float], float] = random.uniform,
) -> float:
    """Random pause in ``[minimum, maximum]`` seconds. Zero when the window is empty."""
    lo, hi = (minimum, maximum) if minimum <= maximum else (maximum, minimum)
    if hi <= 0:
        return 0.0
    if lo == hi:
        return lo
    return uniform(lo, hi)


def merge_listing_and_detail(
    listing: dict[str, Any], detail: dict[str, str | None], *, retrieved_at: str
) -> dict[str, Any]:
    """Build a contracted record; listing fields win for date/unit when detail is sparse."""
    title = detail.get("title") or listing["title"]
    issuing_unit = detail.get("issuing_unit") or listing["issuing_unit"]
    publish_date = listing["publish_date"] or detail.get("publish_date")
    return {
        "notice_id": listing["notice_id"],
        "source_url": listing["source_url"],
        "title": title,
        "issuing_unit": issuing_unit,
        "publish_date": publish_date,
        "body_text": detail.get("body_text"),
        "listing_url": listing["listing_url"],
        "retrieved_at": retrieved_at,
    }


def run(
    router: StealthRouter,
    client: SourceRuntimeClient,
    *,
    acquisition: dict[str, Any],
    ingest_date: str,
    max_pages: int | None = None,
    sleep: Callable[[float], None] = time.sleep,
    uniform: Callable[[float, float], float] = random.uniform,
) -> int:
    """Walk all listing pages, fetch details, stream one JSON batch to Rust runtime."""
    site = str(acquisition.get("site", DEFAULT_SITE)).rstrip("/")
    listing_base = str(acquisition.get("listing_base", DEFAULT_LISTING_BASE))
    pause_min = float(acquisition.get("pause_seconds_min", DEFAULT_PAUSE_MIN_SECONDS))
    pause_max = float(acquisition.get("pause_seconds_max", DEFAULT_PAUSE_MAX_SECONDS))
    timeout = float(acquisition.get("request_timeout_seconds", DEFAULT_TIMEOUT_SECONDS))
    max_attempts = int(acquisition.get("request_max_attempts", DEFAULT_MAX_ATTEMPTS))
    backoff_base = float(acquisition.get("retry_backoff_seconds", DEFAULT_BACKOFF_SECONDS))
    backoff_cap = float(acquisition.get("retry_backoff_cap_seconds", DEFAULT_BACKOFF_CAP_SECONDS))
    max_requests = int(acquisition.get("max_requests_per_run", 550))
    max_detail_failures = int(
        acquisition.get("max_detail_failures", DEFAULT_MAX_DETAIL_FAILURES)
    )
    if max_attempts < 1:
        raise ValueError("request_max_attempts must be at least 1")
    if acquisition.get("block_static_resources", True):
        enable_blocking = getattr(router, "enable_static_blocking", None)
        if callable(enable_blocking):
            enable_blocking()

    requests_used = 0
    retrieved_at = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")

    def fetch(url: str, *, optional: bool = False) -> str | None:
        nonlocal requests_used
        last_error: BaseException | None = None
        for attempt in range(1, max_attempts + 1):
            if requests_used >= max_requests:
                raise RuntimeError(f"max_requests_per_run={max_requests} reached before {url}")
            if attempt == 1:
                if requests_used > 0:
                    pause = pause_seconds(pause_min, pause_max, uniform=uniform)
                    if pause > 0:
                        logger.info("Waiting %.1fs before the next MOST request", pause)
                        sleep(pause)
            else:
                wait = backoff_seconds(attempt, base=backoff_base, cap=backoff_cap)
                logger.warning(
                    "MOST fetch %s/%s failed for %s (%s); retrying in %.1fs",
                    attempt - 1,
                    max_attempts,
                    url,
                    last_error,
                    wait,
                )
                if wait > 0:
                    sleep(wait)
            logger.info("Fetching MOST page: %s (attempt %s/%s)", url, attempt, max_attempts)
            try:
                snapshot = router.fetch(url, timeout_seconds=timeout)
            except Exception as exc:  # noqa: BLE001 - playwright raises Error, not TimeoutError
                requests_used += 1
                transient = is_transient_fetch_error(exc)
                if attempt >= max_attempts or not transient:
                    if optional and transient:
                        logger.warning(
                            "MOST detail %s failed after %s attempts (%s); "
                            "continuing without body_text",
                            url,
                            attempt,
                            exc,
                        )
                        return None
                    raise
                last_error = exc
                continue
            requests_used += 1
            failure = _retryable_snapshot(url, snapshot)
            if failure is not None and attempt < max_attempts:
                last_error = failure
                continue
            if snapshot.blocked_by:
                raise RuntimeError(
                    f"Target blocked by {snapshot.blocked_by} "
                    f"(HTTP {snapshot.status}); the run stops."
                )
            if snapshot.status != 200:
                raise RuntimeError(f"{url} answered {snapshot.status}.")
            return snapshot.html
        raise RuntimeError(f"{url} failed after {max_attempts} attempts") from last_error

    first_path = listing_page_path(listing_base, 1)
    first_url = urljoin(site + "/", first_path.lstrip("/"))
    first_html = fetch(first_url)
    if not first_html:
        raise RuntimeError(f"{first_url} returned an empty page.")
    footer = parse_listing_footer(first_html)
    total_pages = footer[2] if footer else 1
    cfg_limit = acquisition.get("max_listing_pages")
    page_limit = max_pages if max_pages is not None else cfg_limit
    if page_limit and int(page_limit) > 0:
        total_pages = min(total_pages, int(page_limit))
        logger.info("MOST listing limited to %s recent pages (max_listing_pages)", total_pages)
    else:
        logger.info("MOST listing footer: %s → %s pages", footer, total_pages)

    listings: list[dict[str, Any]] = parse_listing_rows(
        first_html, listing_url=first_url, site=site
    )
    for page in range(2, total_pages + 1):
        path = listing_page_path(listing_base, page)
        listing_url = urljoin(site + "/", path.lstrip("/"))
        html = fetch(listing_url)
        if not html:
            raise RuntimeError(f"{listing_url} returned an empty page.")
        listings.extend(parse_listing_rows(html, listing_url=listing_url, site=site))

    # Dedupe by notice_id (keep first / newest listing appearance).
    by_id: dict[str, dict[str, Any]] = {}
    for item in listings:
        by_id.setdefault(item["notice_id"], item)
    listings = list(by_id.values())

    records: list[dict[str, Any]] = []
    skipped_details = 0
    empty_detail = {
        "title": None,
        "issuing_unit": None,
        "publish_date": None,
        "body_text": None,
    }
    for item in listings:
        detail_html = fetch(item["source_url"], optional=True)
        if detail_html is None:
            skipped_details += 1
            if skipped_details > max_detail_failures:
                raise RuntimeError(
                    f"{skipped_details} MOST detail pages failed "
                    f"(limit {max_detail_failures}); the run stops."
                )
            detail = empty_detail
        else:
            detail = parse_detail_page(detail_html)
        records.append(merge_listing_and_detail(item, detail, retrieved_at=retrieved_at))
    if skipped_details:
        logger.warning(
            "MOST ingested %s records with %s details missing body_text",
            len(records),
            skipped_details,
        )

    document = json.dumps({"records": records}, sort_keys=True, ensure_ascii=False).encode("utf-8")
    client.ingest(
        SOURCE,
        DATASET,
        [document],
        content_type="application/json",
        filename="funding_opportunities.json",
        ingest_date=ingest_date,
    )
    return len(records)


def main(argv: list[str] | None = None) -> int:
    """CLI entry point executed by Airflow task."""
    parser = argparse.ArgumentParser(prog="most-extractor", description=__doc__)
    parser.add_argument("--dataset", default=DATASET, help=f"dataset name, defaults to {DATASET!r}")
    parser.add_argument("--ingest-date", help="YYYY-MM-DD partition date")
    parser.add_argument(
        "--runtime-url", default=os.environ.get("RUNTIME_URL", "http://127.0.0.1:8088")
    )
    parser.add_argument(
        "--max-listing-pages",
        type=int,
        default=None,
        help="maximum listing pages to scan (overrides acquisition config)",
    )
    parser.add_argument(
        "--full-history",
        action="store_true",
        help="scan all listing pages (disables max_listing_pages limit)",
    )
    args = parser.parse_args(argv)
    if args.dataset != DATASET:
        print(f"error: unsupported most dataset {args.dataset!r}", file=sys.stderr)
        return 2

    from scrapagents.runtime_client.client import today_utc
    from scrapagents.stealth.playwright_obscura import PlaywrightObscuraRouter

    logging.basicConfig(level=logging.INFO, format="%(message)s")
    config = load_ingestion_config(SOURCE)
    obscura = ObscuraConfig.from_env()
    user_agent = obscura.user_agent or DEFAULT_USER_AGENT
    obscura = ObscuraConfig(obscura.cdp_url, obscura.cdp_token, user_agent)

    effective_pages = 0 if args.full_history else args.max_listing_pages

    with PlaywrightObscuraRouter(obscura) as router:
        try:
            runtime_client = HttpRuntimeClient(args.runtime_url)
            count = run(
                router,
                runtime_client,
                acquisition=config.get("acquisition", {}),
                ingest_date=args.ingest_date or today_utc(),
                max_pages=effective_pages,
            )
            print(f"most: ingested {count} records into dataset {DATASET}")
        except (RuntimeIngestError, OSError) as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
