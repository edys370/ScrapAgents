"""DAAD extractor: listing-only HEI programmes from www.daad.de via Obscura → SourceRuntime."""

from __future__ import annotations

import argparse
import html as html_lib
import json
import logging
import os
import re
import sys
import time
from typing import Any
from urllib.parse import urljoin, urlparse

from scrapagents.contracts.loader import load_ingestion_config
from scrapagents.runtime_client import HttpRuntimeClient, RuntimeIngestError, SourceRuntimeClient
from scrapagents.stealth.base import ObscuraConfig, StealthRouter

logger = logging.getLogger(__name__)

SOURCE = "daad"
DATASET = "funding_programmes"
DEFAULT_USER_AGENT = "ScrapAgents-ingest-daad/0.1 (research; non-commercial)"
DEFAULT_SITE = "https://www.daad.de"
DEFAULT_LISTING_PATHS = (
    "/en/information-services-for-higher-education-institutions/",
    "/en/the-daad/what-we-do/sustainable-development/",
    "/en/information-services-for-higher-education-institutions/expertise-on-subjects-countries-regions/campus-initiative-international-academic-experts/",
    "/de/infos-services-fuer-hochschulen/weiterfuehrende-infos-zu-daad-foerderprogrammen/",
)

_TAG_RE = re.compile(r"<[^>]+>")
_ARTICLE_RE = re.compile(r"<article\b[^>]*>(.*?)</article>", re.IGNORECASE | re.DOTALL)
_H3_RE = re.compile(r"<h3\b[^>]*>(.*?)</h3>", re.IGNORECASE | re.DOTALL)
_P_RE = re.compile(r"<p\b[^>]*>(.*?)</p>", re.IGNORECASE | re.DOTALL)
_HREF_RE = re.compile(r'href=["\']([^"\']+)["\']', re.IGNORECASE)
_TITLE_RE = re.compile(r"<title\b[^>]*>(.*?)</title>", re.IGNORECASE | re.DOTALL)
_META_DESC_RE = re.compile(
    r'<meta\b[^>]+name=["\']description["\'][^>]+content=["\']([^"\']*)["\']',
    re.IGNORECASE,
)
_NUXT_RE = re.compile(
    r'<script[^>]+id=["\']__NUXT_DATA__["\'][^>]*>(.*?)</script>',
    re.IGNORECASE | re.DOTALL,
)
_NUXT_TYPED = frozenset(
    {
        "Reactive",
        "ShallowReactive",
        "Ref",
        "ShallowRef",
        "Set",
        "Map",
        "EmptyRef",
        "EmptyReactive",
    }
)


def _clean_text(raw: str) -> str:
    text = html_lib.unescape(_TAG_RE.sub(" ", raw))
    return re.sub(r"\s+", " ", text).strip()


def _slugify(title: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
    return slug[:80] or "programme"


def programme_slug_from_url(url: str, title: str) -> str:
    """Last meaningful path segment, or a title slug when the path is a language root."""
    path = urlparse(url).path.rstrip("/")
    segment = path.rsplit("/", 1)[-1] if path else ""
    if segment and segment not in {"en", "de", "es", "www.daad.de"}:
        return segment
    return _slugify(title)


def language_from_url(url: str) -> str:
    path = urlparse(url).path
    for code in ("en", "de", "es"):
        if path == f"/{code}" or path.startswith(f"/{code}/"):
            return code
    return "de"


def _resolve_nuxt(data: list[Any], idx: Any, *, seen: set[int] | None = None) -> Any:
    if seen is None:
        seen = set()
    if not isinstance(idx, int):
        return idx
    if idx in seen or idx < 0 or idx >= len(data):
        return None
    seen.add(idx)
    val = data[idx]
    if isinstance(val, dict):
        return {k: _resolve_nuxt(data, v, seen=seen.copy()) for k, v in val.items()}
    if isinstance(val, list):
        if len(val) >= 2 and isinstance(val[0], str) and val[0] in _NUXT_TYPED:
            return _resolve_nuxt(data, val[1], seen=seen.copy())
        return [_resolve_nuxt(data, v, seen=seen.copy()) for v in val]
    return val


def _topic_label_map(data: list[Any]) -> dict[str, str]:
    labels: dict[str, str] = {}
    for i, item in enumerate(data):
        if not isinstance(item, dict):
            continue
        if set(item.keys()) != {"filters", "results", "teaser", "translations"}:
            continue
        block = _resolve_nuxt(data, i)
        filters = block.get("filters") if isinstance(block, dict) else None
        if not isinstance(filters, list):
            continue
        for filt in filters:
            if not isinstance(filt, dict):
                continue
            if filt.get("name") != "topics" and filt.get("filterName") != "data.topicValues":
                continue
            for opt in filt.get("data") or []:
                if isinstance(opt, dict) and opt.get("value") is not None:
                    labels[str(opt["value"])] = str(opt.get("label") or "").strip()
    return labels


def parse_catalogue_nuxt(html: str, *, listing_url: str, site: str) -> list[dict[str, Any]]:
    """Parse DAAD A–Z HEI funding programmes from the Nuxt hydration payload."""
    match = _NUXT_RE.search(html)
    if not match:
        return []
    try:
        data = json.loads(match.group(1))
    except json.JSONDecodeError:
        return []
    if not isinstance(data, list):
        return []

    topic_labels = _topic_label_map(data)
    language = language_from_url(listing_url)
    records: list[dict[str, Any]] = []
    seen: set[str] = set()

    for i, item in enumerate(data):
        if not isinstance(item, dict):
            continue
        if not {"title", "teaserText", "link", "topicValues"} <= set(item.keys()):
            continue
        prog = _resolve_nuxt(data, i)
        if not isinstance(prog, dict):
            continue
        title = _clean_text(str(prog.get("title") or ""))
        if not title:
            continue
        link = prog.get("link") if isinstance(prog.get("link"), dict) else {}
        href = str(link.get("url") or "").strip()
        if not href:
            continue
        source_url = urljoin(site.rstrip("/") + "/", href.lstrip("/"))
        if urlparse(source_url).hostname not in {None, "www.daad.de", "daad.de"}:
            continue
        slug = programme_slug_from_url(source_url, title)
        programme_id = f"{language}:{slug}"
        if programme_id in seen:
            continue
        seen.add(programme_id)
        topics = prog.get("topicValues") or []
        focus_parts = [
            topic_labels.get(str(t), "").strip()
            for t in topics
            if topic_labels.get(str(t), "").strip()
        ]
        summary = _clean_text(str(prog.get("teaserText") or "")) or None
        records.append(
            {
                "programme_id": programme_id,
                "programme_slug": slug,
                "title": title,
                "summary": summary,
                "thematic_focus": "; ".join(focus_parts) if focus_parts else None,
                "language": language,
                "page_kind": "catalogue_programme",
                "publish_date": None,
                "source_url": source_url,
                "listing_url": listing_url,
            }
        )
    return records


def parse_teaser_articles(html: str, *, listing_url: str, site: str) -> list[dict[str, Any]]:
    """Parse English HEI overview teaser cards (`<article>` + h3 + first internal href)."""
    language = language_from_url(listing_url)
    records: list[dict[str, Any]] = []
    seen: set[str] = set()
    for block in _ARTICLE_RE.findall(html):
        h3 = _H3_RE.search(block)
        if not h3:
            continue
        title = _clean_text(h3.group(1))
        if not title:
            continue
        href = None
        for candidate in _HREF_RE.findall(block):
            if candidate.startswith("/_nuxt/") or candidate.startswith("#"):
                continue
            href = candidate
            break
        if not href:
            continue
        source_url = urljoin(site.rstrip("/") + "/", href)
        host = urlparse(source_url).hostname
        if host not in {None, "www.daad.de", "daad.de"}:
            continue
        slug = programme_slug_from_url(source_url, title)
        programme_id = f"{language}:{slug}"
        if programme_id in seen:
            continue
        seen.add(programme_id)
        paras = [_clean_text(p) for p in _P_RE.findall(block)]
        summary = None
        for p in paras:
            cleaned = p.lstrip("© ").strip()
            if cleaned and cleaned != title and cleaned.lower() != "mehr":
                summary = cleaned
                break
        records.append(
            {
                "programme_id": programme_id,
                "programme_slug": slug,
                "title": title,
                "summary": summary,
                "thematic_focus": title,
                "language": language,
                "page_kind": "thematic_initiative",
                "publish_date": None,
                "source_url": source_url,
                "listing_url": listing_url,
            }
        )
    return records


def parse_thematic_page(html: str, *, listing_url: str, site: str) -> list[dict[str, Any]]:
    """Emit one thematic_initiative record from a dedicated initiative listing page."""
    title_match = _TITLE_RE.search(html)
    title = _clean_text(title_match.group(1)) if title_match else ""
    title = re.sub(r"\s*-\s*DAAD\s*$", "", title).strip()
    if not title:
        return []
    desc_match = _META_DESC_RE.search(html)
    summary = _clean_text(desc_match.group(1)) if desc_match else None
    language = language_from_url(listing_url)
    if listing_url.startswith("http"):
        source_url = listing_url
    else:
        source_url = urljoin(site.rstrip("/") + "/", listing_url)
    slug = programme_slug_from_url(source_url, title)
    return [
        {
            "programme_id": f"{language}:{slug}",
            "programme_slug": slug,
            "title": title,
            "summary": summary or None,
            "thematic_focus": title,
            "language": language,
            "page_kind": "thematic_initiative",
            "publish_date": None,
            "source_url": source_url,
            "listing_url": source_url,
        }
    ]


def parse_listing_page(
    html: str, *, listing_url: str, site: str = DEFAULT_SITE
) -> list[dict[str, Any]]:
    """Route listing HTML to Nuxt catalogue, teaser cards, or page-level grain."""
    path = urlparse(listing_url).path.rstrip("/")
    if path.endswith("weiterfuehrende-infos-zu-daad-foerderprogrammen"):
        records = parse_catalogue_nuxt(html, listing_url=listing_url, site=site)
        return records or parse_teaser_articles(html, listing_url=listing_url, site=site)

    # English HEI hub: several teaser cards in <main>.
    if path.endswith("information-services-for-higher-education-institutions"):
        return parse_teaser_articles(html, listing_url=listing_url, site=site)

    # Dedicated initiative pages (campus / sustainable development): one grain per page.
    return parse_thematic_page(html, listing_url=listing_url, site=site)


def _dedupe(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    seen: set[str] = set()
    for record in records:
        key = str(record.get("programme_id") or "")
        if not key or key in seen:
            continue
        seen.add(key)
        out.append(record)
    return out


def run(
    router: StealthRouter,
    client: SourceRuntimeClient,
    *,
    acquisition: dict[str, Any],
    ingest_date: str,
) -> int:
    """Fetch the four listing pages, parse deterministically, stream JSON to Rust runtime."""
    site = str(acquisition.get("site", DEFAULT_SITE)).rstrip("/")
    paths = acquisition.get("listing_paths") or list(DEFAULT_LISTING_PATHS)
    delay = float(acquisition.get("min_seconds_between_requests", 3))
    timeout = float(acquisition.get("request_timeout_seconds", 30))
    max_requests = int(acquisition.get("max_requests_per_run", 4))

    records: list[dict[str, Any]] = []
    for index, path in enumerate(list(paths)[:max_requests]):
        if index > 0 and delay > 0:
            time.sleep(delay)
        listing_url = f"{site}/{str(path).lstrip('/')}"
        logger.info("Fetching DAAD listing: %s", listing_url)
        snapshot = router.fetch(listing_url, timeout_seconds=timeout)
        if snapshot.blocked_by:
            raise RuntimeError(
                f"Target blocked by {snapshot.blocked_by} (HTTP {snapshot.status}); the run stops."
            )
        if snapshot.status != 200:
            raise RuntimeError(f"{listing_url} answered {snapshot.status}.")
        records.extend(parse_listing_page(snapshot.html, listing_url=listing_url, site=site))

    records = _dedupe(records)
    document = json.dumps({"records": records}, sort_keys=True).encode("utf-8")
    client.ingest(
        SOURCE,
        DATASET,
        [document],
        content_type="application/json",
        filename="funding_programmes.json",
        ingest_date=ingest_date,
    )
    return len(records)


def main(argv: list[str] | None = None) -> int:
    """CLI entry point executed by Airflow task."""
    parser = argparse.ArgumentParser(prog="daad-extractor", description=__doc__)
    parser.add_argument("--dataset", default=DATASET, help=f"dataset name, defaults to {DATASET!r}")
    parser.add_argument("--ingest-date", help="YYYY-MM-DD partition date")
    parser.add_argument(
        "--runtime-url", default=os.environ.get("RUNTIME_URL", "http://127.0.0.1:8088")
    )
    args = parser.parse_args(argv)
    if args.dataset != DATASET:
        print(f"error: unsupported daad dataset {args.dataset!r}", file=sys.stderr)
        return 2

    from scrapagents.runtime_client.client import today_utc
    from scrapagents.stealth.playwright_obscura import PlaywrightObscuraRouter

    logging.basicConfig(level=logging.INFO, format="%(message)s")
    config = load_ingestion_config(SOURCE)
    obscura = ObscuraConfig.from_env()
    user_agent = obscura.user_agent or DEFAULT_USER_AGENT
    obscura = ObscuraConfig(obscura.cdp_url, obscura.cdp_token, user_agent)

    with PlaywrightObscuraRouter(obscura) as router:
        try:
            runtime_client = HttpRuntimeClient(args.runtime_url)
            count = run(
                router,
                runtime_client,
                acquisition=config.get("acquisition", {}),
                ingest_date=args.ingest_date or today_utc(),
            )
            print(f"daad: ingested {count} records into dataset {DATASET}")
        except (RuntimeIngestError, OSError) as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
