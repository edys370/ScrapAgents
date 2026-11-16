# Contexto del Proyecto y Especificación de Arquitectura / Project Context & Architecture Specification (`Contex.md`)

[![Language: ES](https://img.shields.io/badge/Language-Espa%C3%B1ol-yellow.svg)](#español)
[![Language: EN](https://img.shields.io/badge/Language-English-blue.svg)](#english)

---

## Español

> **AUDIENCIA OBJETIVO:** Agentes Autónomos de IA (`Claude Code`, `source-scout`, `source-assessor`, `silver-designer`, `arch-reviewer`).  
> **PRINCIPIO FUNDAMENTAL:** La IA opera estrictamente en **Tiempo de Diseño (Design-Time)** para generar artefactos deterministas. La ejecución en **Tiempo de Ejecución (Run-Time)** es 100% determinista y libre de inferencia de LLMs.

### 1. Invariantes Arquitectónicos
1. **Cero IA en Tiempo de Ejecución:** Sin llamadas a LLMs dentro de extractores, DAGs o modelos SQL.
2. **Fuente Única de Verdad para Contratos:** Todos los esquemas y reglas residen en `configs/contracts/` y `configs/ingestions/`.
3. **Navegador Obscura sobre CDP:** Todo acceso web automatizado se realiza a través de Obscura (`obscura.sh`) conectado por CDP (`OBSCURA_CDP_URL`).
4. **Integridad de Streaming a Rust:** Extracción transmitida en bruto a `SourceRuntime` (RustWorker); almacenamiento inmutable en RustFS S3 Landing y triaje hacia Tika (solo PDFs/DOCXs) y Bronze en PostgreSQL.
5. **Compuertas Humanas (HITL):** Macro-H1, Producto OI y PR Merge bajo estricto control humano.

---

## English

> **TARGET AUDIENCE:** Autonomous AI Agents (`Claude Code`, `source-scout`, `source-assessor`, `silver-designer`, `arch-reviewer`).  
> **CORE PRINCIPLE:** AI operates strictly at **Design-Time** to generate deterministic artifacts. **Run-Time** execution is 100% deterministic and free of LLM inference.

### 1. Architectural Invariants
1. **Zero AI at Run-Time:** No LLM SDK imports or agent prompts in production extractors, DAGs, or dbt models.
2. **Single Source of Truth for Contracts:** All contracts and declarations live in `configs/contracts/` and `configs/ingestions/`.
3. **Browser Access via Obscura:** Playwright connects over CDP to Obscura (`obscura.sh` in Rust).
4. **Stream-to-Rust Integrity:** Payloads stream directly to `SourceRuntime` (RustWorker); raw Landing in RustFS S3 and binary triage to Tika (PDF/DOCX only) and PostgreSQL Bronze.
5. **Human Gates (HITL):** Macro-H1, Producto OI, and PR Merge remain strictly human-governed.
