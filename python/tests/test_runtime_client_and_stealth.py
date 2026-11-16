import hashlib

import pytest
from scrapagents.runtime_client import InMemoryRuntimeClient
from scrapagents.stealth.base import ObscuraConfig
from scrapagents.stealth.playwright_obscura import (
    PlaywrightObscuraRouter,
    _abort_static,
    detect_block,
    should_block_static,
)


def test_in_memory_client_hashes_like_the_runtime():
    client = InMemoryRuntimeClient()
    receipt = client.ingest("demo", "records", [b"hello ", b"world"])
    assert receipt.sha256 == hashlib.sha256(b"hello world").hexdigest()
    assert receipt.size_bytes == 11
    assert client.objects[receipt.object_key] == b"hello world"


def test_obscura_is_mandatory_unless_explicitly_disabled():
    with pytest.raises(RuntimeError):
        ObscuraConfig.from_env({})
    assert not ObscuraConfig.from_env({"OBSCURA_REQUIRED": "0"}).uses_obscura
    config = ObscuraConfig.from_env(
        {"OBSCURA_CDP_URL": "ws://obscura:9222", "OBSCURA_CDP_TOKEN": "t" * 32}
    )
    assert config.cdp_url == "ws://obscura:9222"
    assert config.cdp_token == "t" * 32
    assert config.uses_obscura


def test_should_block_static_assets():
    assert should_block_static("image", "https://service.most.gov.cn/ui/a.png")
    assert should_block_static("stylesheet", "https://service.most.gov.cn/ui/a")
    assert should_block_static("font", "https://service.most.gov.cn/ui/a")
    assert should_block_static("other", "https://service.most.gov.cn/ui/a.css?v=1")
    assert should_block_static("other", "https://service.most.gov.cn/ui/a.WOFF2")
    assert not should_block_static("document", "https://service.most.gov.cn/kjjh_tztg/index.html")
    assert not should_block_static("script", "https://service.most.gov.cn/ui/jquery.min.js")


class _Route:
    def __init__(self, resource_type: str, url: str) -> None:
        self.request = type("Req", (), {"resource_type": resource_type, "url": url})()
        self.action = None

    def abort(self) -> None:
        self.action = "abort"

    def continue_(self) -> None:
        self.action = "continue"


def test_abort_static_handler():
    image = _Route("image", "https://service.most.gov.cn/ui/a.png")
    document = _Route("document", "https://service.most.gov.cn/kjjh_tztg/index.html")
    _abort_static(image)
    _abort_static(document)
    assert image.action == "abort"
    assert document.action == "continue"


def test_fetch_installs_static_route_when_enabled():
    class _Page:
        def __init__(self) -> None:
            self.patterns: list[str] = []

        def route(self, pattern: str, handler: object) -> None:
            self.patterns.append(pattern)
            assert handler is _abort_static

        def goto(self, url: str, timeout: float, wait_until: str) -> None:
            assert url == "https://service.most.gov.cn/kjjh_tztg/index.html"
            assert timeout == 90_000
            assert wait_until == "domcontentloaded"
            return None

        def content(self) -> str:
            return "<html></html>"

        def close(self) -> None:
            return None

    page = _Page()
    router = PlaywrightObscuraRouter(ObscuraConfig())
    router._start = lambda: type("Ctx", (), {"new_page": lambda _self: page})()  # type: ignore[method-assign]
    router.enable_static_blocking()
    snapshot = router.fetch(
        "https://service.most.gov.cn/kjjh_tztg/index.html", timeout_seconds=90
    )
    assert page.patterns == ["**/*"]
    assert snapshot.status is None
    assert snapshot.html == "<html></html>"


def test_detect_block():
    assert detect_block(200, "<div class='g-recaptcha'></div>") == "captcha"
    assert detect_block(200, "<script src='https://geetest.com/v4.js'></script>") == "captcha"
    assert detect_block(200, "<div>请完成安全验证后继续</div>") == "captcha"
    assert detect_block(403, "") == "waf"
    assert detect_block(200, "<title>Just a moment...</title>") == "waf"
    assert detect_block(200, "<h2>网站防火墙拦截通知</h2>") == "waf"
    assert detect_block(200, "<p>您的访问过于频繁，已被系统暂时限制</p>") == "waf"
    assert detect_block(200, "<p>ok</p>") is None


def test_obscura_config_timeout_and_locale():
    config = ObscuraConfig.from_env(
        {
            "OBSCURA_REQUIRED": "0",
            "OBSCURA_TIMEOUT_SECONDS": "60.0",
            "OBSCURA_LOCALE": "zh-CN",
            "OBSCURA_ACCEPT_LANGUAGE": "zh-CN,zh;q=0.9",
        }
    )
    assert config.timeout_seconds == 60.0
    assert config.locale == "zh-CN"
    assert config.accept_language == "zh-CN,zh;q=0.9"


def test_decode_html_encodings():
    from scrapagents.stealth import decode_html, detect_charset

    utf8_bytes = "<h1>中华人民共和国科学技术部</h1>".encode()
    assert "科学技术部" in decode_html(utf8_bytes, "text/html; charset=utf-8")
    assert detect_charset(utf8_bytes, "text/html; charset=utf-8") == "utf-8"

    gbk_html = "<html><head><meta charset='gb2312'></head><body><h1>科技创新</h1></body></html>"
    gbk_bytes = gbk_html.encode("gb18030")
    assert "科技创新" in decode_html(gbk_bytes)
    assert detect_charset(gbk_bytes) == "gb2312"

    raw_gbk = "科技创新".encode("gb18030")
    assert "科技创新" in decode_html(raw_gbk)
