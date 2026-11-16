# Área 3: Extracción, Navegación y Runtime / Area 3: Extraction, Navigation and Runtime

[![Language: ES](https://img.shields.io/badge/Language-Espa%C3%B1ol-yellow.svg)](#español)
[![Language: EN](https://img.shields.io/badge/Language-English-blue.svg)](#english)

---

## Español

> **PRINCIPIO:** La capa de extracción ejecuta código Python y Rust determinista. Utiliza navegación sigilosa a través del navegador Obscura sobre CDP y transmite flujos de bytes directamente al motor nativo en Rust (`SourceRuntime`) para garantizar integridad y alto rendimiento.

### 1. Componentes del Subsistema de Extracción

```text
[Portal Externo / API]
         │
         ▼ (HTTP / CDP)
[Playwright + Obscura.sh]  <── Bloqueo automático de imágenes, CSS, fuentes y multimedia
         │
         ▼ (Stream bytes)
[SourceRuntime (RustWorker)]
         ├──> Escribe objeto inmutable en S3 (RustFS Landing)
         ├──> ¿Es PDF / DOCX? ──> [Apache Tika] ──> Extrae .txt hacia Landing
         └──> Carga registros validados en PostgreSQL Bronze
```

1. **Obscura (`obscura.sh` en Rust):** Navegador headless escrito en Rust especializado para evitar bloqueos por WAF y Cloudflare, escuchando en el puerto `9222` sobre CDP.
2. **Enrutador Sigiloso (`PlaywrightObscuraRouter`):** Módulo Python que conecta Playwright a Obscura sobre CDP. Bloquea por defecto recursos estáticos innecesarios (imágenes, CSS, fuentes, multimedia) para acelerar drásticamente la carga de páginas.
3. **SourceRuntime (`RustWorker`):** Microservicio nativo en Rust (puerto `8088`). Recibe streams de bytes, calcula el SHA-256 y despacha primero a Landing (S3).
   * **Invariante 4:** JSON, XML, HTML y CSV van directo a Bronze sin pasar por Apache Tika. Solo PDF y DOCX se envían a Apache Tika (puerto `9998`).

### 2. Técnicas de Optimización y Rendimiento
* **Consumo de APIs Directas:** Si el portal cuenta con APIs REST/JSON (ej. Banco Mundial), se consumen directamente evitando renderizar el DOM.
* **Ventana Caliente Periódica (`max_listing_pages`):** En ejecuciones diarias se escanean únicamente las páginas recientes (ej. las primeras 5 páginas), reduciendo ejecuciones de horas a minutos.
* **Pausas Cortas y Timeouts Asertivos:** Pausas de 1.0 a 2.5s y timeouts de 45s para no bloquearse en páginas colgadas.
* **Pools de Concurrencia:** Un pool exclusivo de 1 slot por sitio en Airflow para respetar a los servidores de origen.

---

## English

> **PRINCIPLE:** The extraction layer executes deterministic Python and Rust code. It drives stealth browser sessions through Obscura over CDP and streams byte payloads directly to the native Rust engine (`SourceRuntime`) for integrity and high performance.

### 1. Extraction Pipeline Architecture

```text
[External Portal / API]
         │
         ▼ (HTTP / CDP)
[Playwright + Obscura.sh]  <── Automated blocking of images, CSS, fonts, and media
         │
         ▼ (Stream bytes)
[SourceRuntime (RustWorker)]
         ├──> Writes immutable object to S3 (RustFS Landing)
         ├──> Is PDF / DOCX? ──> [Apache Tika] ──> Extracts .txt to Landing
         └──> Loads validated records into PostgreSQL Bronze
```

1. **Obscura (`obscura.sh` in Rust):** Headless browser written in Rust specifically built for AI agents to evade WAFs and Cloudflare challenges, listening on port `9222` via CDP.
2. **Stealth Router (`PlaywrightObscuraRouter`):** Connects Playwright over CDP to Obscura. Automatically aborts images, CSS, fonts, and video/audio by default to maximize scraping throughput.
3. **SourceRuntime (`RustWorker`):** Native Rust microservice on port `8088`. Calculates SHA-256 digests and persists payloads to S3 Landing first.
   * **Invariant 4:** JSON, XML, HTML, and CSV never touch Tika; only complex binaries (PDF, DOCX) pass through Apache Tika (port `9998`).

### 2. Scraping Speed and Performance Best Practices
* **API-First Discovery:** When SPA portals use underlying JSON APIs (e.g., World Bank), the extractor queries endpoints directly without loading the browser DOM.
* **Recent Window Scans (`max_listing_pages`):** Daily runs scan the top 3-5 listing pages (~50 notices), trimming crawl times from hours down to 1-2 minutes. Full backfills run via `--full-history`.
* **Polite Pacing & Short Timeouts:** Polite randomized pauses (1.0 to 2.5s) and 45s deadlines to fail fast when external servers lag.
* **Single-Slot Airflow Pools:** Dedicated pool of 1 slot per source domain to respect institutional rate limits.
