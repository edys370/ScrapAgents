# Especificación de Arquitectura y Contexto / Project Context & Architecture Specification (`AGENTS.md`)

[![Language: ES](https://img.shields.io/badge/Language-Espa%C3%B1ol-yellow.svg)](#español)
[![Language: EN](https://img.shields.io/badge/Language-English-blue.svg)](#english)

---

## Español

> **AUDIENCIA OBJETIVO:** Agentes Autónomos de IA (`Claude Code`, `source-scout`, `source-assessor`, `silver-designer`, `arch-reviewer`, `gate-sentinel`).  
> **PRINCIPIO FUNDAMENTAL:** La IA opera estrictamente en **Tiempo de Diseño (Design-Time)** para generar artefactos deterministas. La ejecución en **Tiempo de Ejecución (Run-Time)** es 100% determinista y libre de inferencia de LLMs.

### 1. Invariantes Arquitectónicos Obligatorios
1. **Cero IA en Tiempo de Ejecución:** Nunca incrustar llamadas a LLMs, prompts dinámicos o lógicas no deterministas dentro de extractores de producción, DAGs de Airflow o modelos dbt.
2. **Fuente Única de Verdad para Contratos:** Todos los esquemas, reglas de validación y mapeos canónicos residen en este repositorio (`configs/contracts/`, `configs/ingestions/`) y generan tablas Bronze, dbt y DAGs mediante plantillas YAML y Jinja. Nunca duplicar un contrato en otro lugar.
3. **Acceso al Navegador mediante Obscura (`obscura.sh` + `playwright`):** `obscura.sh` es un navegador headless en Rust diseñado para agentes de IA; es el destino de toda sesión de navegación. Las sondas de descubrimiento (`source-scout`) y los extractores web se conectan a Obscura sobre el protocolo CDP (`connect_over_cdp`, endpoint `OBSCURA_CDP_URL`, token `OBSCURA_CDP_TOKEN`). El uso de Obscura no reemplaza la revisión legal: los Términos de Servicio, `robots.txt` y cualquier bloqueo (WAF, captcha) se registran como hallazgos para el Gate H1.
4. **Integridad de Streaming a Rust y Triaje Binario (`SourceRuntime` / `RustWorker`):** Los extractores en Python transmiten flujos de bytes directamente al worker nativo de Rust. Cada carga útil se escribe primero en **RustFS (S3 Landing)** —documentos estructurados (JSON, XML, HTML, CSV) y binarios complejos (PDF, DOCX). Solo los PDFs/DOCXs pasan por Apache Tika; el texto `.txt` extraído se almacena nuevamente en RustFS junto al archivo original. Las filas tipadas de PostgreSQL `bronze` se cargan leyendo dicho objeto desde RustFS. JSON, XML, HTML y CSV nunca tocan Tika.
5. **Compuertas Estrictas con Humano en el Bucle (HITL):** Los humanos son propietarios de **Macro-H1** (autorización por lotes mediante `make authorize-lane`), la **revisión de valor de Producto OI**, y la aprobación del **PR Merge** (`make sign GATE=pr`). Las compuertas H1/H2 por fuente pueden ser autofirmadas por `gate-sentinel` únicamente cuando la fuente pertenece al carril verde autorizado y cumple el 100% de las reglas deterministas (`make sentinel` / `make sentinel-sign`).

### 2. Matriz de Tecnologías

| Componente | Tecnología | Responsabilidad |
| :--- | :--- | :--- |
| **Arnés de Diseño** | Python (`playwright`, `pytest`) + `obscura.sh` | Sondas efímeras de sondeo sobre CDP, análisis de DOM y detección de bloqueos. |
| **Orquestador** | Apache Airflow `3.4.0` | Carga de DAGs declarativos YAML nativos (AIP-85) sin código Python dinámico. |
| **Worker de Ingesta** | Rust `1.80` (`tokio`, `sha2`) | Hashing SHA-256, persistencia en RustFS S3 y triaje hacia Apache Tika y PostgreSQL Bronze. |
| **Parser Binario** | Apache Tika `4.1.0` | Extracción de texto plano exclusivo para archivos PDF y DOCX. |
| **Lakehouse / Almacén** | RustFS S3 + PostgreSQL `16` | S3 inmutable bajo Hive y tablas tipadas en PostgreSQL Bronze. |
| **Transformación** | dbt Core `1.12.3` | Modelado modular en capas: Staging, Intermediate y Producto OI (Gold). |

### 3. Ciclo de Vida de Diseño (Agentes)
```text
[1. Discovery] ──> [2. Assessment] ──> [3. Blueprint] ──(H2 / Contexto)──> [4. Implement] ──> [5. Verify] ──> [PR Approved]
```
Las validaciones de H1 y H2 están unificadas en una única compuerta situada al finalizar el contexto (en H2, al final de Blueprint). Los agentes avanzan de Discovery a Blueprint sin interrupciones ni confirmaciones intermedias; se solicita una única confirmación al terminar el contexto.
Los agentes deben consultar obligatoriamente **`Contex.md`** en la raíz del repositorio (y `docs/contexto_de_busqueda_y_criterios.md` como referencia) como guía canónica de búsqueda, atributos requeridos y exclusiones.

---

## English

> **TARGET AUDIENCE:** Autonomous AI Agents (`Claude Code`, `source-scout`, `source-assessor`, `silver-designer`, `arch-reviewer`, `gate-sentinel`).  
> **CORE PRINCIPLE:** AI operates strictly at **Design-Time** to generate deterministic artifacts. **Run-Time** execution is 100% deterministic and free of LLM inference.

### 1. Mandatory Architectural Invariants
1. **Zero AI at Run-Time:** Never embed LLM calls, dynamic prompts, or non-deterministic agent logic inside production extractors, Airflow DAGs, or dbt models.
2. **Single Source of Truth for Contracts:** All schemas, validation rules, and canonical mappings live in this repository (`configs/contracts/`, `configs/ingestions/`) and generate bronze, dbt, and DAGs via YAML & Jinja templates. Never duplicate a contract elsewhere.
3. **Browser access through Obscura (`obscura.sh` + `playwright`):** `obscura.sh` is a headless browser written in Rust built for AI agents; it is the destination of every browser session. All probes (`source-scout`) and web extractors connect to Obscura over CDP (`connect_over_cdp`, endpoint `OBSCURA_CDP_URL`, token `OBSCURA_CDP_TOKEN`). Obscura does not replace legal review: Terms of Service, `robots.txt`, and blocks (WAF, captcha) are recorded as findings for Gate H1.
4. **Stream-to-Rust Integrity & Binary Triage (`SourceRuntime` / `RustWorker`):** Python extractors stream raw byte payloads to `RustWorker`. Every payload is written to **RustFS (S3 Landing)** first — structured documents (JSON, XML, HTML, CSV) and complex binaries (PDF, DOCX). Only PDF/DOCX then pass through Apache Tika; the extracted `.txt` is written back to RustFS beside the raw object. Typed PostgreSQL `bronze` rows are loaded by reading that object back from RustFS. JSON, XML, HTML, and CSV never touch Tika.
5. **Strict Human-in-the-Loop (HITL) Gates:** Humans own **Macro-H1** (batch risk-lane authorization via `make authorize-lane`), **Producto OI value review**, and **PR Merge** (`make sign GATE=pr`). Per-source **H1/H2** may be auto-signed by `gate-sentinel` only when the source is in the authorized green lane and deterministic rules pass 100% (`make sentinel` / `make sentinel-sign`).

### 2. Technology & Tooling Matrix

| Component | Technology | Responsibility |
| :--- | :--- | :--- |
| **Design Harness** | Python (`playwright`, `pytest`) + `obscura.sh` | Ephemeral discovery probe scripts over CDP, DOM mapping, and block detection. |
| **Orchestrator** | Apache Airflow `3.4.0` | Native YAML declarative DAG importer (AIP-85) without dynamic runtime Python. |
| **Ingestion Worker** | Rust `1.80` (`tokio`, `sha2`) | SHA-256 hashing, RustFS S3 Landing storage, and triage to Apache Tika and PostgreSQL Bronze. |
| **Binary Parser** | Apache Tika `4.1.0` | Plain-text extraction strictly for PDF and DOCX files. |
| **Lakehouse / Warehouse**| RustFS S3 + PostgreSQL `16` | Immutable S3 under Hive partitioning and typed Bronze PostgreSQL tables. |
| **Transformation** | dbt Core `1.12.3` | Modular transformations across Staging, Intermediate, and Producto OI (Gold). |

### 3. Design-Time Workflow (Agentic SDLC)
```text
[1. Discovery] ──> [2. Assessment] ──> [3. Blueprint] ──(H2 / Context)──> [4. Implement] ──> [5. Verify] ──> [PR Approved]
```
Validations for H1 and H2 are unified into a single gate evaluated when context definition completes (at H2, end of Blueprint). No intermediate confirmations are prompted during Discovery or Assessment; only one confirmation is requested once the full context is established at H2.
Agents must strictly consult **`Contex.md`** at the repository root (and `docs/contexto_de_busqueda_y_criterios.md` as reference) as the single canonical guide for search intent, required attributes, and exclusions.
