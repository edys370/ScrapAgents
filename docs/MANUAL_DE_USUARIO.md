# Manual de Usuario / User Manual: ScrapAgents

[![Language: ES](https://img.shields.io/badge/Language-Espa%C3%B1ol-yellow.svg)](#español)
[![Language: EN](https://img.shields.io/badge/Language-English-blue.svg)](#english)

---

## Español

> **BIENVENIDO A SCRAPAGENTS:** Sistema determinista de ingesta, normalización y gobernanza de datos para el producto analítico **Producto OI (Opportunity Intelligence)**.

### Índice (Español)
1. [Arquitectura y Concepto General](#1-arquitectura-y-concepto-general-es)
2. [Requisitos Previos y Configuración](#2-requisitos-previos-y-configuración-es)
3. [Levantamiento de la Infraestructura Local](#3-levantamiento-de-la-infraestructura-local-es)
4. [Criterios de Búsqueda y Negocio](#4-criterios-de-búsqueda-y-negocio-es)
5. [Ciclo de Vida para Añadir una Nueva Fuente](#5-ciclo-de-vida-para-añadir-una-nueva-fuente-es)
6. [Generación de Artefactos (Bronze, dbt, DAGs)](#6-generación-de-artefactos-bronze-dbt-dags-es)
7. [Orquestación y Monitoreo en Apache Airflow](#7-orquestación-y-monitoreo-en-apache-airflow-es)
8. [Transformación Analítica con dbt y Producto OI](#8-transformación-analítica-con-dbt-y-producto-oi-es)
9. [Solución de Problemas (Troubleshooting)](#9-solución-de-problemas-troubleshooting-es)

---

### 1. Arquitectura y Concepto General (ES)
ScrapAgents opera bajo dos principios:
* **IA en Tiempo de Diseño (Design-Time):** Los agentes autónomos exploran páginas web, diseñan contratos y generan código determinista.
* **Cero IA en Tiempo de Ejecución (Run-Time):** No existen llamadas a LLMs ni lógicas dinámicas dentro de extractores de producción, tareas de Airflow o transformaciones SQL.

#### Documentación por Áreas
* 🤖 [**Área 1: Agentes y Skills**](docs/areas/1_agentes_y_skills/README.md)
* 📊 [**Área 2: Datos, Contratos y Modelado**](docs/areas/2_datos_y_contratos/README.md)
* 🚀 [**Área 3: Extracción, Navegación y Runtime**](docs/areas/3_extraccion_y_runtime/README.md)
* 🐳 [**Área 4: Orquestación, Contenedores e Infraestructura**](docs/areas/4_orquestacion_e_infraestructura/README.md)

### 2. Requisitos Previos y Configuración (ES)
* **Docker y Docker Compose** (v2.20+).
* **Python 3.11+** (recomendado `uv`).
* **Rust 1.80+** (para compilación del motor nativo `source_runtime`).

```bash
uv venv --python 3.13 .venv
source .venv/bin/activate
uv pip install -e ".[dev,extractors,smoke]"
make infra-env
export OBSCURA_CDP_TOKEN="$(openssl rand -hex 32)"
```

### 3. Levantamiento de la Infraestructura Local (ES)
```bash
make infra-up
```
* **Airflow UI:** [http://localhost:8080](http://localhost:8080)
* **RustFS S3 Console:** [http://localhost:9001](http://localhost:9001) (`scrapagents` / `change-me-local-only`)
* **PostgreSQL Warehouse:** `localhost:5433` (`scrapagents` / `change-me-local-only`)
* **SourceRuntime (Rust):** `http://localhost:8088`
* **Obscura CDP Browser:** `http://localhost:9222`

Para apagar los servicios: `make infra-down`.

### 4. Criterios de Búsqueda y Negocio (ES)
Consulta [**Criterios de Búsqueda y Contexto de Negocio**](docs/contexto_de_busqueda_y_criterios.md):
* ✅ **Buscar:** Subvenciones I+D+i, becas de posgrado, premios científicos, licitaciones internacionales y fondos concursables.
* ❌ **Ignorar:** Compras de oficina (papel, tóner), noticias de prensa, trámites internos y portales con login.

### 5. Ciclo de Vida para Añadir una Nueva Fuente (ES)
```text
Discovery ──> Assessment ──(H1)──> Blueprint ──(H2)──> Implementación ──> Verificación ──(PR)
```
1. **Crear Dossier:** `make new-ingestion ID=mi_fuente TEAM=sistemas_internos`
2. **Discovery:** `make probe ID=mi_fuente URL="https://portal.ejemplo.org/convocatorias"` y luego `make advance ID=mi_fuente`.
3. **Assessment & H1:** `make sign ID=mi_fuente GATE=h1 BY="Tu Nombre"` (o `make sentinel-sign` para fuentes verdes).
4. **Blueprint & H2:** `make review ID=mi_fuente` y luego `make sign ID=mi_fuente GATE=h2 BY="Tu Nombre"`.
5. **Implementación:** Redactar extractor en `python/scrapagents/extractors/mi_fuente/extractor.py`.

### 6. Generación de Artefactos (Bronze, dbt, DAGs) (ES)
```bash
make generate-bronze && make bronze-apply
make generate-dbt
make generate-dags && make airflow-pools
```

### 7. Orquestación y Monitoreo en Apache Airflow (ES)
Abre [http://localhost:8080](http://localhost:8080) y activa el DAG `ingest__<id>`.

### 8. Transformación Analítica con dbt y Producto OI (ES)
```bash
dbt build --select tag:source_mi_fuente --project-dir dbt --profiles-dir dbt
```

### 9. Solución de Problemas (Troubleshooting) (ES)
* **Connection refused 8088:** Corre `make infra-up` y confirma que `scrapagents-source-runtime` esté levantado.
* **Timeout en 9222:** Verifica `OBSCURA_CDP_TOKEN` en `.env` (al menos 32 caracteres) y contenedor activo.
* **Extractor lento:** Usa `max_listing_pages: 5` para ejecuciones diarias y confirma `block_static_resources: true`.
* **Airflow missing pool:** Corre `make airflow-pools`.

---

## English

> **WELCOME TO SCRAPAGENTS:** Deterministic data ingestion, normalization, and governance platform for **Producto OI (Opportunity Intelligence)**.

### Table of Contents (English)
1. [General Architecture & Concept](#1-general-architecture--concept-en)
2. [Prerequisites & Environment Setup](#2-prerequisites--environment-setup-en)
3. [Starting Local Infrastructure](#3-starting-local-infrastructure-en)
4. [Search Intent & Business Criteria](#4-search-intent--business-criteria-en)
5. [Step-by-Step Source Lifecycle](#5-step-by-step-source-lifecycle-en)
6. [Code Generation (Bronze, dbt, DAGs)](#6-code-generation-bronze-dbt-dags-en)
7. [Airflow Orchestration & Monitoring](#7-airflow-orchestration--monitoring-en)
8. [Analytical Transformation & Producto OI](#8-analytical-transformation--producto-oi-en)
9. [Troubleshooting](#9-troubleshooting-en)

---

### 1. General Architecture & Concept (EN)
ScrapAgents adheres strictly to two architectural pillars:
* **AI at Design-Time:** Autonomous agents discover portals, draft data contracts, and generate deterministic code.
* **Zero AI at Run-Time:** Extractors, DAGs, and SQL models run 100% deterministically with no LLM inference.

#### Area Documentation
* 🤖 [**Area 1: Agents & Skills**](docs/areas/1_agentes_y_skills/README.md)
* 📊 [**Area 2: Data, Contracts & Modeling**](docs/areas/2_datos_y_contratos/README.md)
* 🚀 [**Area 3: Extraction, Navigation & Runtime**](docs/areas/3_extraccion_y_runtime/README.md)
* 🐳 [**Area 4: Orchestration, Containers & Infrastructure**](docs/areas/4_orquestacion_e_infraestructura/README.md)

### 2. Prerequisites & Environment Setup (EN)
* **Docker & Docker Compose** (v2.20+).
* **Python 3.11+** (recommended `uv`).
* **Rust 1.80+** (for building `source_runtime`).

```bash
uv venv --python 3.13 .venv
source .venv/bin/activate
uv pip install -e ".[dev,extractors,smoke]"
make infra-env
export OBSCURA_CDP_TOKEN="$(openssl rand -hex 32)"
```

### 3. Starting Local Infrastructure (EN)
```bash
make infra-up
```
* **Airflow Web UI:** [http://localhost:8080](http://localhost:8080)
* **RustFS S3 Console:** [http://localhost:9001](http://localhost:9001) (`scrapagents` / `change-me-local-only`)
* **PostgreSQL Warehouse:** `localhost:5433` (`scrapagents` / `change-me-local-only`)
* **SourceRuntime (Rust):** `http://localhost:8088`
* **Obscura CDP Browser:** `http://localhost:9222`

To shut down services: `make infra-down`.

### 4. Search Intent & Business Criteria (EN)
Read [**Search Criteria and Business Context**](docs/contexto_de_busqueda_y_criterios.md):
* ✅ **In-Scope:** R&D&I grants, academic scholarships, scientific awards, international procurement tenders.
* ❌ **Out-of-Scope:** Office supplies (paper, toner), press releases, internal bureaucracy, login-gated portals.

### 5. Step-by-Step Source Lifecycle (EN)
```text
Discovery ──> Assessment ──(H1)──> Blueprint ──(H2)──> Implementation ──> Verification ──(PR)
```
1. **Scaffold Dossier:** `make new-ingestion ID=my_source TEAM=sistemas_internos`
2. **Discovery:** `make probe ID=my_source URL="https://portal.example.org/tenders"` then `make advance ID=my_source`.
3. **Assessment & H1:** `make sign ID=my_source GATE=h1 BY="Your Name"` (or `make sentinel-sign` for green sources).
4. **Blueprint & H2:** `make review ID=my_source` then `make sign ID=my_source GATE=h2 BY="Your Name"`.
5. **Implementation:** Code extractor in `python/scrapagents/extractors/my_source/extractor.py`.

### 6. Code Generation (Bronze, dbt, DAGs) (EN)
```bash
make generate-bronze && make bronze-apply
make generate-dbt
make generate-dags && make airflow-pools
```

### 7. Airflow Orchestration & Monitoring (EN)
Navigate to [http://localhost:8080](http://localhost:8080) and toggle on `ingest__<id>`.

### 8. Analytical Transformation & Producto OI (EN)
```bash
dbt build --select tag:source_my_source --project-dir dbt --profiles-dir dbt
```

### 9. Troubleshooting (EN)
* **Connection refused 8088:** Run `make infra-up` and verify `scrapagents-source-runtime` is running.
* **Timeout on 9222:** Ensure `OBSCURA_CDP_TOKEN` is set in `.env` (32+ chars) and `scrapagents-obscura` is healthy.
* **Slow Scraping:** Set `max_listing_pages: 5` in config for daily runs and keep `block_static_resources: true`.
* **Airflow missing pool:** Run `make airflow-pools`.
