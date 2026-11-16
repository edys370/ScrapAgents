# PROJECT CONTEXT & ARCHITECTURE SPECIFICATION (`AGENTS.md`)

> **TARGET AUDIENCE:** Autonomous AI Agents (`Claude Code`, `source-scout`, `source-assessor`, `silver-designer`, `arch-reviewer`, `gate-sentinel`).
> **CORE PRINCIPLE:** AI operates strictly at **Design-Time** to generate deterministic artifacts. **Run-Time** execution is 100% deterministic and free of LLM inference.

---

## 1. SYSTEM OVERVIEW & ARCHITECTURAL INVARIANTS

This platform ingests, normalizes, and governs unstructured and structured data from external institutions into a unified analytical product (**Producto OI - Opportunity Intelligence**). 

### Mandatory Architectural Invariants
1. **Zero AI at Run-Time:** Never embed LLM calls, dynamic prompts, or non-deterministic agent logic inside production extractors, Airflow DAGs, or dbt models.
2. **Single Source of Truth for Contracts:** All schemas, validation rules, and canonical mappings live in this repository (`configs/contracts/`, `configs/ingestions/`) and generate bronze, dbt and DAGs via YAML & Jinja templates. Never duplicate a contract elsewhere. CEDIA is a reference only, not a dependency.
3. **Browser access through Obscura (`obscura.sh` + `playwright`):** `obscura.sh` is a headless browser written in Rust and built for AI agents; it is the *destination* of every browser session. All browser-based discovery probes (`source-scout`) and production web extractors requiring DOM navigation use `playwright`, but instead of opening a local Chromium on the extractor host, Playwright connects to Obscura over the Chrome DevTools Protocol (`connect_over_cdp`, endpoint `OBSCURA_CDP_URL`, bearer token `OBSCURA_CDP_TOKEN`). Using Obscura does not replace the legal review: a site's Terms of Service, `robots.txt` and any block (WAF, captcha) are recorded as findings for Gate H1.
4. **Stream-to-Rust Integrity & Binary Triage (`SourceRuntime` / `RustWorker`):** Python extractors stream raw byte payloads to `RustWorker` / `SourceRuntime`. Every payload is written to **RustFS (S3 `Landing`)** first — structured documents (JSON, XML, HTML, CSV) and complex binaries (PDF, DOCX). Only PDF/DOCX then pass through Apache Tika; the extracted `.txt` is written back to RustFS beside the raw object. Typed PostgreSQL `bronze` rows are loaded by **reading that object back from RustFS**. JSON, XML, HTML and CSV never touch Tika.
5. **Strict Human-in-the-Loop (HITL) Gates:** Humans own **Macro-H1** (batch risk-lane authorization via `make authorize-lane`), **Producto OI value review**, and **PR Merge** (`make sign GATE=pr`). Per-source **H1/H2** may be auto-signed by `gate-sentinel` only when the source is in the authorized green lane and deterministic rules pass 100% (`make sentinel` / `make sentinel-sign`). Yellow/red and exceptions stay human. Agents never sign PR and never edit `state.yml` by hand.

---

## 2. TECHNOLOGY STACK & TOOLING MATRIX

### 2.1 Design-Time (Agentic Harness)
| Component | Technology / Version | Agentic Role & Responsibility |
| :--- | :--- | :--- |
| **Core Orchestrator** | Claude Code | Primary repository orchestrator, scaffolding executor (`make new-ingestion`), and multi-agent coordinator. |
| **Discovery Probes & Browser** | Python (`playwright`, `pytest`) + `obscura.sh` (headless browser in Rust, reached over CDP) | Used by `source-scout` to run ephemeral probe scripts that connect to Obscura, map DOM/API structures, and detect and report WAF, Captcha and ToS blocks. |
| **Contract Engine** | YAML & Jinja2 | Read from `configs/` of this repository to compile data dictionaries, quality rules, and DAG/dbt generation templates. |

### 2.2 Run-Time (Deterministic Infrastructure)
| Component | Technology / Version | Operational Responsibility |
| :--- | :--- | :--- |
| **Workflow Orchestrator** | Apache Airflow `3.4.0` | Latest stable release (with native YAML DAG importer / AIP-85 support). Parses declarative `.yml` configurations generated at design-time to instantiate and schedule deterministic DAGs. |
| **Extractor & Browser Layer** | Python + `playwright` + `obscura.sh` | Executes production extraction from institutional web portals/APIs: Playwright drives the Obscura browser over CDP (`OBSCURA_CDP_URL`) and streams raw bytes directly to the Rust worker. |
| **SourceRuntime (`RustWorker`)** | Rust `1.80` (`tokio`, `sha2`) | Writes every payload to RustFS first, then loads typed PostgreSQL `bronze` from that object. Only PDF/DOCX are sent to Apache Tika; the plain text is stored back in RustFS. |
| **Binary Parser** | Apache Tika Server `4.1.0` | Invoked by `RustWorker` only after the raw PDF/DOCX is already in RustFS. The extracted `.txt` is written to Landing next to the binary. |

### 2.3 Data Warehouse, Lakehouse & Governance
| Component | Technology / Version | Storage / Modeling Responsibility |
| :--- | :--- | :--- |
| **Object Storage (Landing)** | RustFS S3 | Immutable Data Lake storing raw payloads and binaries under Hive-style partitioning. |
| **Data Warehouse** | PostgreSQL `16` | Hosts typed `bronze` tables (one per dataset, `JSONB` payload + lineage columns, plus a quarantine table) and analytical schemas managed by dbt. |
| **Transformation Engine** | dbt Core `1.12.3` (`dbt-postgres 1.10.1`) | Manages SQL transformations across `Staging`, `Intermediate`, and `Producto OI` layers. |
| **Data Catalog & Lineage** | OpenMetadata `1.4.2` | Automatically ingests Airflow execution logs and dbt `manifest.json` artifacts to map 5-layer end-to-end lineage. |

---

## 3. DESIGN-TIME WORKFLOW (AGENTIC SDLC)

Every new institutional ingestion pipeline is built autonomously through a 5-phase state machine with strategic human checkpoints (Macro-H1, Producto OI value, PR) and optional sentinel auto-sign for green H1/H2:

```text
[1. Discovery] ──> [2. Assessment] ──(H1)──> [3. Blueprint] ──(H2)──> [4. Implement] ──> [5. Verify] ──> [PR Approved]
```

[4. Implement] and [5. Verify] run in this repository (`configs/`, `python/scrapagents/extractors/<id>/`, see section 5);
[1. Discovery] to [3. Blueprint] produce their evidence in `ingestions/<id>/` of this repository.

### Gates (operational rules)
| Gate | Between | Evidence required | Who signs |
| :--- | :--- | :--- | :--- |
| **H1** | Assessment -> Blueprint | `ingestions/<id>/assessment.md` (legal/ToS, anti-bot, volume, refresh analysis) | Human owner |
| **H2** | Blueprint -> Implement | `ingestions/<id>/blueprint.yml` + draft contract (schema, quality rules, `configs/ingestions/<id>.yml` draft) | Human owner + arch-reviewer |
| **PR** | Verify -> merge | `make validate` green (lint, tests, gates, contracts, generated files current), reviewer approval | Human reviewer |

Agents and their commands: `source-scout` (`make probe`), `source-assessor`, `silver-designer`, `arch-reviewer` (`make review`), `gate-sentinel` (`make sentinel` / `make sentinel-sign`), coordinated by the `new-source` skill; `make status` shows where a source stands and `make advance` moves its phase. Humans run `make authorize-lane` (Macro-H1) and `make sign` (PR / yellow path); see `docs/implementation-plan.md` F5 and `docs/producto-oi-value-review.md`.

State lives in `ingestions/<id>/state.yml` (`phase`, `h1`, `h2`, `pr`). An agent MUST NOT move
`phase` past a gate whose `status` is not `approved` and whose `approved_by` is empty.

---

## 4. REPOSITORY LAYOUT (this repo: design-time harness)

```text
AGENTS.md / Contex.md   architecture context (this file is canonical for agents)
docs/                   implementation plan, reference notes on CEDIA
configs/contracts/      `<source>/<dataset>.yml`: the single source of contracts
configs/ingestions/     `<id>.yml`: one declaration per source (datasets, acquisition, schedule, pool)
python/scrapagents/     contract loader/validator, stealth interface, runtime client, scaffolding helpers
dags/                   declarative Airflow YAML DAGs generated by `make generate-dags` (never hand-edited); one DAG per source
bronze/                 typed bronze DDL and RustWorker registry generated by `make generate-bronze` (never hand-edited)
dbt/                    dbt project: generated sources/staging/intermediate; hand-designed `producto_oi` (needs H1 and H2)
ingestions/_template/   design-time dossier template (discovery, assessment, blueprint, state)
scripts/                new_ingestion.py (dossier scaffold)
rust/source_runtime/    native SourceRuntime / RustWorker (hashing, triage, sinks)
infra/<stack>/          one docker compose project per domain (warehouse, ingestion; later orchestration, transformation, governance) on the shared network `scrapagents_net`
.cursor/rules/          invariants and gates as always-applied rules
```

## 5. CONTRACTS AND CEDIA (reference only)

This project is independent of CEDIA: it runs entirely on this machine (RustFS for Landing, PostgreSQL
for bronze, local Airflow) and does not link, vendor or deploy to CEDIA's repository
(`sicedia/cedia-data-platform_prod`). Its conventions were used as a guide.

* Contracts live in `configs/contracts/<source_system>/<dataset>.yml`; a source is declared once in
  `configs/ingestions/<id>.yml`. Allowed contract types: `string, integer, number, boolean, object,
  array, json, date, timestamp`; owner must be `data_team_<team>`. Rules: `scrapagents.contracts`.
* Implementation (phase 4) happens here: `configs/`, an extractor package
  `python/scrapagents/extractors/<id>/`, then `make generate-bronze generate-dbt generate-dags`.
* Optional reading, outside this repository: `../cedia-data-platform_prod-main/docs/ai/` and
  `docs/architecture/`. Differences are tracked in `docs/cedia-alignment.md`; do not "fix" either side silently.

## 6. IMPLEMENTATION PHASES
F1 Foundations (done) -> F2 Runtime core (done) -> F3 Airflow orchestration (done) -> F4 dbt / Producto OI (done) -> F5 Design-time agents (done) -> F6 Governance.
Details and exit criteria: `docs/implementation-plan.md`.
