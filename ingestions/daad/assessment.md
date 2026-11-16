# Assessment: daad

Phase 2. Written by `source-assessor`. Closed by **Gate H1** (human sign-off in `state.yml`).
Every `- Label:` line must be answered; `make status ID=daad` lists what is missing.

## Viability
- Legal / ToS risk: **Low.** Evidence (`discovery.md`, read 2026-11-12): `https://www.daad.de/robots.txt` explicitly permits crawling `/en/information-services-for-higher-education-institutions/*`, `/en/the-daad/what-we-do/*`, and `/de/infos-services-fuer-hochschulen/*`, subject to `Crawl-delay: 2` and a disallow list of internal/search/PDF paths (`/*?barrierUrl=`, `/en/suche.html`, `/de/suche.html`, `/ausland/*.pdf$`, `/deutschland/*.pdf$`, `/laenderinformationen/*.pdf$`). The Imprint (`https://www.daad.de/en/imprint/`) reserves copyright over texts and images to Deutscher Akademischer Austauschdienst e.V. (DAAD) and contains no prohibition against automated non-commercial indexing of public funding programme metadata. Every record will retain full attribution (`DAAD`, canonical `source_url`, and Imperia `publish_date`).
- Anti-bot risk and mitigation (obscura.sh): **Low, verified directly through Obscura over CDP.** All 8 probed URLs on `www.daad.de` returned HTTP `200 OK` with `blocked_by: none` via `scrapagents.stealth.PlaywrightObscuraRouter` connected to `obscura.sh`. No WAF challenge or CAPTCHA was encountered, and the SSR Nuxt 3 HTML includes complete `<main>` markup and `<script id="__NUXT_DATA__">` JSON hydration state in the initial document load. Mitigation: (1) route all navigation through `PlaywrightObscuraRouter` (`OBSCURA_CDP_URL`); (2) enforce a **one-slot Airflow Pool** (`daad_source`) and a 3-second delay between requests (exceeding `Crawl-delay: 2`); (3) strictly avoid all paths disallowed in `robots.txt` (including search endpoints and disallowed PDF paths).
- Personal data (LOPDP): no. The target HEI funding programme overview and catalogue pages publish only institutional programme titles, thematic areas, eligibility summaries, and functional institutional links (`webmaster@daad.de`, DAAD Bonn headquarters). Notice: individual contact cards on specific project subpages or the Imprint executive committee names are excluded from extraction; the contract extracts only institutional programme metadata (`personal_data: false`).
- Duplicates an existing source?: no. Checked `configs/ingestions/` (`caf`, `cyted`, `idrc`, `world_bank`) and `configs/contracts/`: no existing source ingests `daad.de` or the German Academic Exchange Service (DAAD).
<!-- Personal data and Duplicates: start the answer with `yes` or `no`, then explain.
     Check configs/ingestions/ and configs/contracts/ for duplicates. -->

## Refresh analysis
See `docs/implementation-plan.md` (every run reads the full scope).
- Full scope per run or incremental: **Full scope on every run**, with table growth governed in bronze by `persistence.mode: changes`. The scope consists of 4 unpaginated SSR pages (~4 requests per run, ~12 seconds total at 3 s spacing): the English HEI overview (`/en/information-services-for-higher-education-institutions/`), the English Campus Initiative page, the English Sustainable Development HEI cooperation page (`/en/the-daad/what-we-do/sustainable-development/`), and the complete A–Z HEI funding programmes catalogue (`/de/infos-services-fuer-hochschulen/weiterfuehrende-infos-zu-daad-foerderprogrammen/`). Every run parses all programmes from these pages and streams the normalized JSON batch to `RustWorker`.
- Proposed schedule and why: **Weekly full read (`0 6 * * 2`, Tuesday 06:00 America/Guayaquil)** with a one-slot Airflow Pool (`daad_source`). Why: DAAD institutional cooperation programmes and thematic initiatives update on a monthly/quarterly cycle, and a weekly 4-request run takes ~12 seconds while keeping `bronze.daad__funding_programmes` current without unnecessary traffic.

## Payload triage preview
| Payload | Format | Goes to Tika? |
| :--- | :--- | :--- |
| Nuxt 3 SSR pages (`/en/information-services-for-higher-education-institutions/`, `/en/the-daad/what-we-do/sustainable-development/`, `/de/infos-services-fuer-hochschulen/weiterfuehrende-infos-zu-daad-foerderprogrammen/`) | html | no |
| Normalized `funding_programmes` dataset records emitted by the Python extractor to `RustWorker` | json | no |

Format is one of json, xml, html, csv, pdf, docx. Only PDF and DOCX go to Apache Tika (answer `yes`);
JSON, XML, HTML and CSV never do (answer `no`). `scrapagents status` checks this.

## Recommendation
- Decision (go / no-go): go
- Reason: High technical viability verified through Obscura (`200 OK`, no WAF/captcha, SSR HTML + Nuxt JSON state), clear `robots.txt` rules (`Crawl-delay: 2` respected with 3 s spacing and zero disallowed PDFs in scope), no personal data required, and no overlap with existing sources.
