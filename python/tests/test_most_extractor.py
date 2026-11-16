"""Unit tests for the MOST kjjh_tztg listing/detail parser."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from scrapagents.extractors.most.extractor import (
    backoff_seconds,
    is_transient_fetch_error,
    listing_page_path,
    merge_listing_and_detail,
    parse_detail_page,
    parse_listing_footer,
    parse_listing_rows,
    run,
)
from scrapagents.stealth.base import PageSnapshot

FIXTURES = Path(__file__).parent / "fixtures" / "most"
SITE = "https://service.most.gov.cn"


def _read(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


def test_listing_page_path():
    assert listing_page_path("/kjjh_tztg/", 1) == "/kjjh_tztg/index.html"
    assert listing_page_path("/kjjh_tztg/", 2) == "/kjjh_tztg/index_2.html"
    assert listing_page_path("/kjjh_tztg", 41) == "/kjjh_tztg/index_41.html"


def test_parse_listing_footer_and_rows():
    html = _read("listing_page1.html")
    assert parse_listing_footer(html) == (406, 1, 41)
    rows = parse_listing_rows(
        html, listing_url=f"{SITE}/kjjh_tztg/index.html", site=SITE
    )
    assert len(rows) == 10
    first = rows[0]
    assert first["notice_id"] == "5935"
    assert first["publish_date"] == "2026-11-12"
    assert first["issuing_unit"] == "广东省科学技术厅"
    assert first["source_url"].endswith("/kjjh_tztg_all/20261112/5935.html")
    assert "粤港澳" in first["title"]


def test_parse_listing_page2():
    html = _read("listing_page2.html")
    assert parse_listing_footer(html) == (406, 2, 41)
    rows = parse_listing_rows(
        html, listing_url=f"{SITE}/kjjh_tztg/index_2.html", site=SITE
    )
    assert len(rows) == 10
    assert rows[0]["notice_id"] == "5924"


def test_parse_detail_and_merge():
    detail = parse_detail_page(_read("detail_5935.html"))
    assert detail["title"] and "粤港澳" in detail["title"]
    assert detail["issuing_unit"] == "广东省科学技术厅"
    assert detail["publish_date"] == "2026-11-12"
    assert detail["body_text"] and "公开公示" in detail["body_text"]

    listing = {
        "notice_id": "5935",
        "source_url": f"{SITE}/kjjh_tztg_all/20261112/5935.html",
        "title": "listing title",
        "issuing_unit": "广东省科学技术厅",
        "publish_date": "2026-11-12",
        "listing_url": f"{SITE}/kjjh_tztg/index.html",
    }
    record = merge_listing_and_detail(
        listing, detail, retrieved_at="2026-11-12T12:00:00Z"
    )
    assert record["notice_id"] == "5935"
    assert record["retrieved_at"] == "2026-11-12T12:00:00Z"
    assert set(record) == {
        "notice_id",
        "source_url",
        "title",
        "issuing_unit",
        "publish_date",
        "body_text",
        "listing_url",
        "retrieved_at",
    }


class _NavigationDeadline(Exception):
    """Stand-in for playwright._impl._errors.Error without importing playwright."""


_NavigationDeadline.__module__ = "playwright._impl._errors"


_LISTING_HTML = """
<html><body>
<tr>
<td class="table_gkgs_title">
<div onclick="openW('/kjjh_tztg_all/20261112/5935.html')" title="标题甲">标题甲</div>
</td>
<td class="table_gkgs_unit" title="单位甲"><div>单位甲</div></td>
<td class="table_gkgs_date">2026-11-12</td>
</tr>
共 1 条记录 1 / 1 页
</body></html>
"""


class _Router:
    def __init__(self, responses: list[PageSnapshot | Exception]) -> None:
        self._responses = list(responses)
        self.calls: list[tuple[str, float | None]] = []

    def fetch(self, url: str, *, timeout_seconds: float | None = None) -> PageSnapshot:
        self.calls.append((url, timeout_seconds))
        item = self._responses.pop(0)
        if isinstance(item, Exception):
            raise item
        return item

    def close(self) -> None:
        return None


class _Client:
    def __init__(self) -> None:
        self.payloads: list[bytes] = []

    def ingest(self, source: str, dataset: str, documents: list[bytes], **kwargs: object) -> None:
        assert source == "most"
        assert dataset == "funding_opportunities"
        self.payloads.extend(documents)


def _page(url: str, html: str, *, status: int = 200, blocked_by: str | None = None) -> PageSnapshot:
    return PageSnapshot(url, status, "text/html", html, blocked_by, html.encode())


def _acquisition(**overrides: object) -> dict:
    config: dict = {
        "site": SITE,
        "listing_base": "/kjjh_tztg/",
        "max_requests_per_run": 10,
        "request_timeout_seconds": 90,
        "request_max_attempts": 4,
        "retry_backoff_seconds": 2,
        "pause_seconds_min": 3,
        "pause_seconds_max": 7,
    }
    config.update(overrides)
    return config


def test_navigation_deadline_is_transient():
    exc = _NavigationDeadline(
        "Page.goto: Protocol error (Page.navigate): "
        "Network error: navigation exceeded 30000ms deadline"
    )
    assert is_transient_fetch_error(exc)
    assert is_transient_fetch_error(TimeoutError("timed out"))
    assert not is_transient_fetch_error(RuntimeError("blocked"))


def test_backoff_doubles_until_cap():
    assert backoff_seconds(1, base=2, cap=32) == 0
    assert backoff_seconds(2, base=2, cap=32) == 2
    assert backoff_seconds(3, base=2, cap=32) == 4
    assert backoff_seconds(4, base=2, cap=32) == 8
    assert backoff_seconds(8, base=2, cap=32) == 32


def test_fetch_retries_timeout_then_pauses_between_pages():
    listing = f"{SITE}/kjjh_tztg/index.html"
    detail = f"{SITE}/kjjh_tztg_all/20261112/5935.html"
    deadline = _NavigationDeadline("navigation exceeded 30000ms deadline")
    router = _Router(
        [
            _page(listing, _LISTING_HTML),
            deadline,
            _page(detail, "<html><body>ok</body></html>"),
        ]
    )
    slept: list[float] = []

    def uniform(lo: float, hi: float) -> float:
        assert (lo, hi) == (3.0, 7.0)
        return 5.0

    count = run(
        router,
        _Client(),
        acquisition=_acquisition(),
        ingest_date="2026-11-13",
        sleep=slept.append,
        uniform=uniform,
    )
    assert count == 1
    assert [timeout for _, timeout in router.calls] == [90.0, 90.0, 90.0]
    assert router.calls[1][0] == detail
    assert router.calls[2][0] == detail
    # First navigation has no pause. The detail waits 5 s, then 2 s before the retry.
    assert slept == [5.0, 2.0]


def test_fetch_does_not_retry_a_block_page():
    listing = f"{SITE}/kjjh_tztg/index.html"
    router = _Router([_page(listing, "<html>验证码</html>", status=200, blocked_by="captcha")])
    slept: list[float] = []
    with pytest.raises(RuntimeError, match="captcha"):
        run(
            router,
            _Client(),
            acquisition=_acquisition(),
            ingest_date="2026-11-13",
            sleep=slept.append,
            uniform=lambda _lo, _hi: 5.0,
        )
    assert len(router.calls) == 1
    assert slept == []


_BODY_TIMEOUT = (
    "Page.goto: Protocol error (Page.navigate): Network error: "
    "Failed to read body: error decoding response body: "
    "request or response body error: operation timed out"
)


def test_body_read_timeout_is_transient():
    assert is_transient_fetch_error(_NavigationDeadline(_BODY_TIMEOUT))


def test_detail_body_timeout_keeps_the_listing_record():
    listing = f"{SITE}/kjjh_tztg/index.html"
    detail = f"{SITE}/kjjh_tztg_all/20261112/5935.html"
    failure = _NavigationDeadline(_BODY_TIMEOUT)
    router = _Router([_page(listing, _LISTING_HTML), failure, failure, failure, failure])
    client = _Client()
    slept: list[float] = []
    count = run(
        router,
        client,
        acquisition=_acquisition(),
        ingest_date="2026-11-13",
        sleep=slept.append,
        uniform=lambda _lo, _hi: 5.0,
    )
    assert count == 1
    assert [url for url, _timeout in router.calls] == [listing, detail, detail, detail, detail]
    assert slept == [5.0, 2.0, 4.0, 8.0]
    record = json.loads(client.payloads[0])["records"][0]
    assert record["notice_id"] == "5935"
    assert record["title"] == "标题甲"
    assert record["body_text"] is None


def test_listing_body_timeout_stops_the_run():
    failure = _NavigationDeadline(_BODY_TIMEOUT)
    router = _Router([failure, failure, failure, failure])
    with pytest.raises(_NavigationDeadline):
        run(
            router,
            _Client(),
            acquisition=_acquisition(),
            ingest_date="2026-11-13",
            sleep=lambda _seconds: None,
            uniform=lambda _lo, _hi: 0.0,
        )


def test_detail_failure_limit_stops_the_run():
    listing = f"{SITE}/kjjh_tztg/index.html"
    failure = _NavigationDeadline(_BODY_TIMEOUT)
    router = _Router([_page(listing, _LISTING_HTML), failure, failure, failure, failure])
    with pytest.raises(RuntimeError, match="limit 0"):
        run(
            router,
            _Client(),
            acquisition=_acquisition(max_detail_failures=0),
            ingest_date="2026-11-13",
            sleep=lambda _seconds: None,
            uniform=lambda _lo, _hi: 0.0,
        )
