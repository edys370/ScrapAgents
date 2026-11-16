# Assessment: most

Phase 2. Written by `source-assessor`. Closed by **Gate H1** (human sign-off in `state.yml`).
Every `- Label:` line must be answered; `make status ID=most` lists what is missing.

## Viability
- Legal / ToS risk: **Medium–High — Gate H1 must decide.** Evidence (`discovery.md`, probed 2026-11-12): `robots.txt` on `www.most.gov.cn` and `fuwu.most.gov.cn` returned HTTP `404` (no crawl policy); `service.most.gov.cn/robots.txt` timed out — absence of robots rules is **not** a licence. The **网站声明** (`https://www.most.gov.cn/wzsm/`, HTTP `200`) states that media, internet sites and commercial entities **must not** use portal content for **commercial verbatim reprint** (商业性的原版原式地转载) or distort/alter it, and that **unauthorized reprint of information and services is forbidden**; reprint requires **合法授权** from the MOST portal. Copyright is claimed by MOST. 政府信息公开指南 names `www.most.gov.cn` as a disclosure channel but does not license bulk machine reuse. **Allowed under a cautious reading:** anonymous reading of public 通知公告 for internal Opportunity Intelligence indexing with full attribution (`source_url`, issuing unit, publish date) — **not** commercial republication of original HTML/layout. **Not allowed without authorization:** verbatim commercial republication or redistribution of portal content as a competing feed. H1 must confirm that Producto OI’s intended use is analytical aggregation (not commercial reprint) and accept residual Chinese copyright / 授权 risk; if legal rejects that reading, outcome is **no-go**.
- Anti-bot risk and mitigation (obscura.sh): **Low on the target path; manageable.** Probes via `PlaywrightObscuraRouter` → Obscura (`obscura.sh` over CDP): primary listing `https://service.most.gov.cn/kjjh_tztg/` (including `index_2.html`, `index_41.html`) and detail e.g. `/kjjh_tztg_all/20261112/5935.html` returned HTTP `200` with `blocked_by: none` (no captcha, no WAF challenge). Auth is not required for public notices (login only for application workflows on `service1`/`service2`). Secondary hosts (`data.most.gov.cn`, some `www.most.gov.cn/tztg` URLs, `jhzxgs`) saw `TimeoutError` without a block page — treat as flaky, out of primary scope. Mitigation: (1) scrape only through Obscura; (2) **one-slot Airflow Pool** (`most_source`); (3) polite inter-request delay (≥2 s, matching discovery probe spacing); (4) scope = `kjjh_tztg` listing pages + `kjjh_tztg_all` detail HTML only — do not chase timed-out secondary hosts or authenticated application APIs.
- Personal data (LOPDP): yes. Public 科技计划通知公告 HTML is mostly institutional (title, issuing unit/来源, publish date, guide text). Detail bodies commonly include **联系人** (named contact persons), phone numbers, and occasionally emails for declaration windows — under Ecuador’s LOPDP these identify natural persons acting in an institutional capacity. Mitigation: mark `personal_data: true` in the contract when those fields are retained in bronze; keep raw HTML in Landing for lineage; strip or mask person-level contacts when projecting to Producto OI. If blueprint later proves extractors never capture person fields, H2 can downgrade — assessment stays conservative.
- Duplicates an existing source?: no. Checked `configs/ingestions/` (`caf`, `cyted`, `daad`, `idrc`, `world_bank`) and `configs/contracts/` — no ingestion of `most.gov.cn`, `service.most.gov.cn`, or dataset path `kjjh_tztg` / Chinese MOST funding notices. Do not add a second acquisition path for the same notices (portal `/tztg/` and `fuwu` lists stay out of scope to avoid overlap).
<!-- Personal data and Duplicates: start the answer with `yes` or `no`, then explain.
     Check configs/ingestions/ and configs/contracts/ for duplicates. -->

## Refresh analysis
See `docs/implementation-plan.md` (every run reads the full scope).
- Full scope per run or incremental: **Full scope on every run** — no incremental acquisition mode. Each run walks all static listing pages (`index.html` … `index_41.html`, ~10 rows/page, ~406 notices, newest-first) and fetches in-scope detail HTML under `/kjjh_tztg_all/YYYYMMDD/<id>.html`, then streams normalized records to `RustWorker`. Bronze growth is controlled with `persistence.mode: changes` (keyed on notice id / canonical URL); do not invent watermark or delta crawl modes.
- Proposed schedule and why: **Daily full read (`0 7 * * *`, 07:00 America/Guayaquil)** with one-slot pool `most_source` and ≥2 s delay. Why: discovery shows bursty / near-daily publication in open-call seasons (multiple notices within days of the 2026-11-12 probe) and an archive back to ~2015 (~406 records / 41 pages). At ~450 requests × 2 s ≈ 15–20 minutes per run — acceptable for a daily cadence without hammering the host. Weekly would miss short application windows; more frequent than daily adds little value given static page files.

## Payload triage preview
| Payload | Format | Goes to Tika? |
| :--- | :--- | :--- |
| Listing iframe pages `https://service.most.gov.cn/kjjh_tztg/` (`index.html`, `index_N.html`) | html | no |
| Notice detail pages `/kjjh_tztg_all/YYYYMMDD/<id>.html` | html | no |
| Normalized `funding_opportunities` records emitted by the extractor to `RustWorker` | json | no |

Format is one of json, xml, html, csv, pdf, docx. Only PDF and DOCX go to Apache Tika (answer `yes`);
JSON, XML, HTML and CSV never do (answer `no`). `scrapagents status` checks this.

## Recommendation
- Decision (go / no-go): go
- Reason: Technically viable: public HTML catalogue (no API), Obscura probes clean (`blocked_by: none`), volume small (~406), scrape via Obscura + one-slot pool + polite delay is the right path; `binary_to_tika` stays empty while scope is listing+detail HTML only (PDFs only if H1/H2 later expand scope). **Conditional on H1 accepting the 网站声明 risk** (no commercial verbatim reprint; 授权 language) as compatible with internal Producto OI indexing with attribution — not republication. If legal cannot accept that, flip to no-go.
