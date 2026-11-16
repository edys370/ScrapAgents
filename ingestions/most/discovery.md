# Discovery: most

Phase 1. Written by `source-scout`. Evidence only, no design decisions.
Every `- Label:` line must be answered; `make status ID=most` lists what is missing.

## Source
- Institution / portal URL: Ministry of Science and Technology of the People's Republic of China (MOST / 中华人民共和国科学技术部). Institutional portal `https://www.most.gov.cn/index.html` (site code `bm06000001`). Primary public listing of science & technology funding / open-call notices (科技计划通知公告) is the National Science and Technology Management Information System public service platform `https://service.most.gov.cn/` (国家科技管理信息系统公共服务平台). Related surfaces: MOST portal notices `https://www.most.gov.cn/tztg/`, government service notices `https://fuwu.most.gov.cn/html/tztg/`, English mirror `https://en.most.gov.cn`.
- Access type (web): **No usable public machine-readable API** for funding opportunities was found. Probes of `robots.txt` / `sitemap.xml`, `data.most.gov.cn`, page HTML, and common list/search paths returned HTML only (no open JSON/XML catalog endpoints). The only non-page endpoint observed was `GET https://service.most.gov.cn/dlORwh/` (small HTML maintenance/login-mode fragment, not notice data). Full-text search is an HTML form at `https://service1.most.gov.cn/sousuonew/s.html`. Project application / unit registration requires authenticated sessions on `service1.most.gov.cn` / `service2.most.gov.cn`. **Acquisition path for public funding notices is therefore web / DOM scrape** through Obscura (`PlaywrightObscuraRouter`), primarily the iframe list `https://service.most.gov.cn/kjjh_tztg/` and detail pages under `/kjjh_tztg_all/YYYYMMDD/<id>.html`. Helper: `ingestions/most/probes/fetch_html.py` (2 s spacing).
- robots.txt and Terms of Service: **robots.txt** (probed 2026-11-12): `https://www.most.gov.cn/robots.txt` → HTTP `404` (HTML 404 page, not a robots policy); `https://fuwu.most.gov.cn/robots.txt` → `404`; `https://service.most.gov.cn/robots.txt` → probe `TimeoutError`. No `Sitemap` declaration; `https://www.most.gov.cn/sitemap.xml` → `404`. **网站声明** (probed 2026-11-12, `https://www.most.gov.cn/wzsm/`, HTTP `200`): quotes (translated sense retained in Chinese source) that portal content is supplied by MOST departments and partners; *"任何媒体、互联网站和商业机构不得利用本网站发布的内容进行商业性的原版原式地转载，也不得歪曲和篡改本网站所发布的内容。"* and *"任何媒体或互联网站不得擅自转载本网站提供的信息和服务内容，如需转载，必须获得科技部门户网站合法授权。"*; copyright claimed by MOST. **政府信息公开指南** (probed 2026-11-12, `https://www.most.gov.cn/xxgk/xinxifenlei/zfxxgkzn/`, HTTP `200`): names `www.most.gov.cn` as the first disclosure channel; applicants’ use of disclosed replies must comply with law and stated purpose. Listing/detail pages for 通知公告 were reachable anonymously with **no captcha / no WAF** in the probe table (`blocked_by: none`); some secondary hosts timed out without a block page.

## Probe evidence
Probes run through `scrapagents.stealth.PlaywrightObscuraRouter` (obscura.sh):
`make probe ID=most URL=<url>` appends the rows below.

| Date | URL | Status | Content type | Blocked by (captcha / waf / none) |
| :--- | :--- | :--- | :--- | :--- |
| 2026-11-12 | https://www.most.gov.cn/robots.txt | 404 | text/html | none |
| 2026-11-12 | https://www.most.gov.cn/index.html | 200 | text/html | none |
| 2026-11-12 | https://www.most.gov.cn/sitemap.xml | 404 | text/html | none |
| 2026-11-12 | https://www.most.gov.cn/wzsm/ | 200 | text/html | none |
| 2026-11-12 | https://www.most.gov.cn/xxgk/xinxifenlei/zfxxgkzn/ | 200 | text/html | none |
| 2026-11-12 | https://service.most.gov.cn/ | 200 | text/html | none |
| 2026-11-12 | https://service.most.gov.cn/index/global_nav.html | 200 | text/html | none |
| 2026-11-12 | https://fuwu.most.gov.cn/html/tztg/ | 200 | text/html | none |
| 2026-11-12 | https://www.most.gov.cn/tztg/ | 200 | text/html | none |
| 2026-11-12 | https://www.most.gov.cn/zxgz/ | 200 | text/html | none |
| 2026-11-12 | https://service.most.gov.cn/robots.txt | error | TimeoutError | none |
| 2026-11-12 | https://fuwu.most.gov.cn/robots.txt | 404 | text/html | none |
| 2026-11-12 | https://service.most.gov.cn/kjjh_tztg_all/ | 200 | text/html | none |
| 2026-11-12 | https://service.most.gov.cn/kjjh_tztg_all/20261112/5935.html | 200 | text/html | none |
| 2026-11-12 | https://service.most.gov.cn/dlORwh/ | 200 | text/html | none |
| 2026-11-12 | https://www.most.gov.cn/tztg/index.html | error | TimeoutError | none |
| 2026-11-12 | https://www.most.gov.cn/tztg/index_1.html | 200 | text/html | none |
| 2026-11-12 | https://www.most.gov.cn/tztg/202610/t20261014_197499.html | 200 | text/html | none |
| 2026-11-12 | https://service.most.gov.cn/index/ | 200 | text/html | none |
| 2026-11-12 | https://data.most.gov.cn/ | error | TimeoutError | none |
| 2026-11-12 | https://www.most.gov.cn/cxfw/ | 200 | text/html | none |
| 2026-11-12 | https://service.most.gov.cn/kjjh_tztg/ | 200 | text/html | none |
| 2026-11-12 | https://service.most.gov.cn/kjjh_tztg_all/?type=0 | 200 | text/html | none |
| 2026-11-12 | https://service.most.gov.cn/jhzxgs/ | error | TimeoutError | none |
| 2026-11-12 | https://service1.most.gov.cn/sousuonew/s.html | 200 | text/html | none |
| 2026-11-12 | https://service.most.gov.cn/kjjh_tztg/index_2.html | 200 | text/html | none |
| 2026-11-12 | https://service.most.gov.cn/kjjh_tztg/index_41.html | 200 | text/html | none |

## Structure found
- Endpoints or DOM entry points: (1) **Funding-notice list (iframe HTML table)** `GET https://service.most.gov.cn/kjjh_tztg/` (also `index.html`); parent shell `https://service.most.gov.cn/kjjh_tztg_all/?type=0` embeds that iframe under tab 通知公告 (nav also exposes `type=1` 地方动态 → `/kjjh_dfdt_all/`, `type=2` 工作动态 → `/kjjh_gzdt_all/`, `type=3` 申报文件). Each list row is a `<tr>` with ordinal, title (`div[onclick="window.parent.openW('/kjjh_tztg_all/YYYYMMDD/<id>.html')"]`), issuing unit, and date `YYYY-MM-DD`. (2) **Notice detail** e.g. `GET https://service.most.gov.cn/kjjh_tztg_all/20261112/5935.html` — HTML article (`article__title`, `article__subTitle` with 发布时间 / 来源, `article-body`); sample title: 关于对国家重点研发计划“粤港澳大湾区国际科技创新中心”重点专项 2026年度申报指南征求意见的通知 (2026-11-12, 广东省科学技术厅). (3) **MOST portal 通知通告** `https://www.most.gov.cn/tztg/` / `index_1.html` — mixed administrative notices (recruitment, budgets as PDF, some S&T calls) in `ul.info_list2`, not the dedicated 科技计划 catalogue. (4) **fuwu.most.gov.cn** `/html/tztg/` — separate政务服务 notice list. (5) **API hunt result:** no public JSON/XML open-data API for these notices; `dlORwh` is ops HTML only; `data.most.gov.cn` timed out; search is HTML `sousuonew/s.html`.
- Pagination and ordering: On `kjjh_tztg/`, footer text `共406条记录 1/41页` (page 2 and 41 confirmed). Static page files: `index.html` (page 1), `index_2.html` … `index_41.html`, ~10 rows per page, newest-first (page 1 dates around 2026-11-12 … 2026-10-30; page 41 dates back to 2015-04-10). MOST portal `/tztg/` uses client paginationjs with `total: 25` pages (mixed notice types).
- Authentication: None for the public notice list, detail pages, portal `tztg`, `wzsm`, or `sousuonew` search UI — all returned `200` to anonymous Obscura sessions. Login/register is required for **project application** and unit workflows (`service1` / `service2` login links on the service portal), not for reading 通知公告 HTML.
- Payload formats: HTML (`text/html`) for list and detail pages. Occasional PDF attachments on the MOST portal notice channel (e.g. 决算 PDFs under `/tztg/202608/*.pdf`). No JSON/XML dataset feed observed for funding notices. Under Invariant 4, HTML bypasses Apache Tika; only complex binaries (PDF/DOCX) would be triaged to Tika if attached payloads are later ingested.
- Estimated volume and change rate: **406** science-plan 通知公告 records on `service.most.gov.cn/kjjh_tztg/` across **41** pages (IDs in the high 5900s as of 2026-11-12). Several new notices appeared within days of the probe (e.g. 2026-11-12, 11-11, 11-10, 11-05, multiple on 2026-10-30), consistent with **bursty / near-daily** publication during open-call seasons rather than a fixed calendar. Archive depth back to ~2015. Secondary channels (`www.most.gov.cn/tztg/` ~25 pages; `fuwu.most.gov.cn/html/tztg/`) add overlapping or administrative notices at lower relevance for funding_opportunities.
<!-- Payload formats: JSON, XML, HTML, CSV, PDF or DOCX. -->
