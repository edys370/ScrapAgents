# Manual de Usuario / User Manual: ScrapAgents

[![Language: ES](https://img.shields.io/badge/Language-Espa%C3%B1ol-yellow.svg)](#español)
[![Language: EN](https://img.shields.io/badge/Language-English-blue.svg)](#english)

---

## Español

> **BIENVENIDO A SCRAPAGENTS:** Plataforma de diseño asistido por agentes y ejecución determinista para la ingesta, normalización y gobernanza de datos desde la web hacia un almacén analítico estructurado.

### Índice (Español)
1. [Arquitectura y Concepto General](#1-arquitectura-y-concepto-general-es)
2. [Requisitos Previos y Configuración del Entorno](#2-requisitos-previos-y-configuración-del-entorno-es)
3. [Levantamiento de la Infraestructura Local](#3-levantamiento-de-la-infraestructura-local-es)
4. [Plantar los Cimientos: Configuración de Contexto de Scraping (`Contex.md`)](#4-plantar-los-cimientos-configuración-de-contexto-de-scraping-contexmd-es)
5. [Flujo Completo: De un Link al DAG en Airflow (Paso a Paso)](#5-flujo-completo-de-un-link-al-dag-en-airflow-paso-a-paso-es)
6. [Generación de Artefactos (Bronze, dbt, DAGs)](#6-generación-de-artefactos-bronze-dbt-dags-es)
7. [Orquestación y Monitoreo en Apache Airflow](#7-orquestación-y-monitoreo-en-apache-airflow-es)
8. [Transformación Analítica con dbt](#8-transformación-analítica-con-dbt-es)
9. [Aislamiento y Git: Por qué los DAGs y Contextos están Ignorados](#9-aislamiento-y-git-por-qué-los-dags-y-contextos-están-ignorados-es)
10. [Solución de Problemas (Troubleshooting)](#10-solución-de-problemas-troubleshooting-es)

---

### 1. Arquitectura y Concepto General (ES)
ScrapAgents opera bajo dos principios fundamentales:
* **IA en Tiempo de Diseño (Design-Time):** Los agentes autónomos exploran páginas web, inspeccionan estructuras DOM/APIs, diseñan esquemas de contratos y generan código de extracción determinista.
* **Cero IA en Tiempo de Ejecución (Run-Time):** La ejecución diaria es 100% determinista, de alto rendimiento y libre de costos o alucinaciones de LLMs.

#### Documentación Detallada por Áreas
* 🤖 [**Área 1: Agentes y Skills**](areas/1_agentes_y_skills/README.md)
* 📊 [**Área 2: Datos, Contratos y Modelado**](areas/2_datos_y_contratos/README.md)
* 🚀 [**Área 3: Extracción, Navegación y Runtime**](areas/3_extraccion_y_runtime/README.md)
* 🐳 [**Área 4: Orquestación, Contenedores e Infraestructura**](areas/4_orquestacion_e_infraestructura/README.md)

---

### 2. Requisitos Previos y Configuración del Entorno (ES)
* **Docker y Docker Compose** (v2.20+).
* **Python 3.11+** (recomendado `uv`).
* **Rust 1.80+** (para compilación del motor nativo `source_runtime`).

```bash
# 1. Crear y activar entorno virtual
uv venv --python 3.13 .venv
source .venv/bin/activate

# 2. Instalar dependencias
uv pip install -e ".[dev,extractors,smoke]"

# 3. Configurar variables de entorno locales
make infra-env
export OBSCURA_CDP_TOKEN="$(openssl rand -hex 32)"
```

---

### 3. Levantamiento de la Infraestructura Local (ES)
Para iniciar todos los servicios del proyecto:
```bash
make infra-up
```

* **Airflow Web UI:** [http://localhost:8080](http://localhost:8080) (Airflow 3.4.0)
* **RustFS S3 Console:** [http://localhost:9001](http://localhost:9001) (`scrapagents` / `change-me-local-only`)
* **PostgreSQL Warehouse:** `localhost:5433` (`scrapagents` / `change-me-local-only`)
* **SourceRuntime (Rust):** `http://localhost:8088` (Worker de ingesta y triaje binario)
* **Obscura CDP Stealth Browser:** `http://localhost:9222` (Navegador anti-bloqueo para agentes)

Para detener la infraestructura: `make infra-down`.

---

### 4. Plantar los Cimientos: Configuración de Contexto de Scraping (`Contex.md`) (ES)

Al clonar este repositorio, el archivo **`Contex.md`** en la raíz está listo para que definas tu propio contexto de scraping. Este archivo es la **fuente canónica** que le indica a los agentes de IA exactamente qué deben buscar al recibir un enlace web.

Para plantar los cimientos de tu proyecto, ajusta `Contex.md` con estos tres parámetros esenciales:

1. **Propósito de Negocio (Business Purpose):**
   * Define en 1 o 2 párrafos qué necesidad resuelves. Por ejemplo:
     * *"Catálogo de becas y subvenciones científicas internacionales."*
     * *"Monitoreo de licitaciones públicas de software y tecnología."*
     * *"Comparador de precios de insumos agrícolas o productos de comercio electrónico."*
2. **Criterios de Inclusión (En-Scope: Lo que SÍ se debe buscar):**
   * Especifica qué entidades buscar y qué atributos son requeridos en el contrato:
     * `id`: Identificador único y estable del registro en el portal.
     * `title`: Título formal de la oportunidad o elemento.
     * `publish_date`: Fecha de publicación en formato ISO `YYYY-MM-DD`.
     * `source_url`: Enlace permanente oficial.
     * `description` / `amount` / `deadline_date`: Campos descriptivos y complementarios.
3. **Criterios de Exclusión (Out-of-Scope: Lo que se DEBE IGNORAR):**
   * Define las reglas negativas para evitar que los agentes extraigan ruido:
     * Compras rutinarias de insumos de oficina (tóner, papel).
     * Artículos informativos, discursos o noticias de prensa sin convocatoria formal.
     * Portales transaccionales protegidos por contraseña o login previo.
     * Agregadores secundarios que sólo reenvían a enlaces de terceros.

> [!TIP]
> Consulta también [**`docs/contexto_de_busqueda_y_criterios.md`**](contexto_de_busqueda_y_criterios.md) como una guía de referencia detallada y ejemplo ampliado de criterios de búsqueda.

---

### 5. Flujo Completo: De un Link al DAG en Airflow (Paso a Paso) (ES)

Una vez plantados los cimientos en `Contex.md`, solo necesitas **proporcionar un enlace (URL)** y seguir el ciclo de vida. Las validaciones de H1 y H2 están unificadas en una única compuerta (H2) que se valida **una sola vez al terminar todo el contexto**, sin interrupciones intermedias:

```text
[1. Scaffolding] ──> [2. Discovery (Link)] ──> [3. Assessment] ──> [4. Blueprint (H2 / Contexto)] ──> [5. Extractor] ──> [6. Generate DAG] ──> [7. Airflow Run]
```

#### Paso 1: Crear el Dossier de la Fuente
Inicializa la estructura de trabajo para el nuevo portal:
```bash
make new-ingestion ID=mi_portal TEAM=sistemas_internos TYPE=web
```
*Esto crea la carpeta `ingestions/mi_portal/` con plantillas de `discovery.md`, `assessment.md`, `blueprint.yml` y `state.yml`.*

#### Paso 2: Pasar el Link y Explorar con Obscura (Discovery)
Pasa la URL del portal que deseas scrapear. El arnés se conectará a través de Obscura (navegador headless en Rust sobre CDP) para inspeccionar la estructura web y eludir bloqueos WAF/antibot:
```bash
make probe ID=mi_portal URL="https://portal.ejemplo.org/convocatorias"
```
Revisa las evidencias registradas en `ingestions/mi_portal/discovery.md` y avanza directamente:
```bash
make advance ID=mi_portal
```

#### Paso 3: Evaluación de Riesgo (Assessment)
Se analizan los Términos de Servicio (ToS), robots.txt, frecuencia de actualización y volumen en `ingestions/mi_portal/assessment.md`. No hay confirmación intermedia; avanzas directamente al Blueprint:
```bash
make advance ID=mi_portal
```

#### Paso 4: Contrato de Datos y Única Confirmación de Contexto (Blueprint & Gate H2)
Al terminar el contexto en Blueprint, se mapean los campos hacia el esquema canónico definido en tus cimientos (`Contex.md`):
* Ejecuta la revisión técnica y mecánica:
  ```bash
  make review ID=mi_portal
  ```
* **Única confirmación de contexto (Gate H2):** Aquí es donde se valida y confirma todo el contexto de una sola vez:
  * Si la fuente es de bajo riesgo (carril verde):
    ```bash
    make sentinel-sign ID=mi_portal
    ```
  * O firma manualmente en tu terminal:
    ```bash
    make sign ID=mi_portal BY="Tu Nombre"
    ```
  * Avanza a la implementación:
    ```bash
    make advance ID=mi_portal
    ```

#### Paso 5: Implementación Determinista del Extractor
Crea o valida el extractor en Python sin IA en runtime:
`python/scrapagents/extractors/mi_portal/extractor.py`
El extractor transmite los flujos de bytes directamente al motor de Rust (`SourceRuntime`), persistiendo en RustFS S3 y cargando a PostgreSQL Bronze.

Copia las configuraciones aprobadas:
* Configuración de la fuente: `configs/ingestions/mi_portal.yml`
* Contrato de datos: `configs/contracts/mi_portal/records.yml`

#### Paso 6: Generación Automática del DAG y Almacén
Genera automáticamente el DAG declarativo de Airflow y las tablas de base de datos con un único comando:
```bash
# 1. Generar DAGs declarativos YAML y pools de concurrencia
make generate-dags
make airflow-pools

# 2. Generar y aplicar esquemas Bronze en PostgreSQL
make generate-bronze && make bronze-apply

# 3. Generar modelos y tests en dbt
make generate-dbt
```

#### Paso 7: Ejecución y Monitoreo en Airflow
Abre la interfaz de Airflow en [http://localhost:8080](http://localhost:8080):
1. Verás aparecer el DAG generado: `ingest__mi_portal`.
2. Activa el interruptor (**Unpause**).
3. Haz clic en **Trigger DAG** para ejecutarlo inmediatamente.
4. Monitorea las tareas:
   * `runtime_ready`: Verifica que el worker de Rust esté listo.
   * `land__records`: Ejecuta el extractor web y guarda en S3 Landing.
   * `landed`: Barrera de sincronización.
   * `dbt_run__records`: Modela los datos en PostgreSQL.

---

### 6. Generación de Artefactos (Bronze, dbt, DAGs) (ES)
Los comandos generadores leen tus contratos y crean código 100% determinista:
* `make generate-dags`: Crea los archivos YAML en `dags/`.
* `make airflow-pools`: Carga los límites de concurrencia para evitar saturar los sitios web.
* `make generate-bronze && make bronze-apply`: Define y aplica las tablas SQL tipadas en PostgreSQL.
* `make generate-dbt`: Genera los modelos dbt de Staging e Intermediate.

---

### 7. Orquestación y Monitoreo en Apache Airflow (ES)
Airflow lee directamente los archivos YAML declarativos generados en `dags/` (siguiendo AIP-85). No hay código dinámico de Python en Airflow, garantizando estabilidad total y cero memory leaks.

---

### 8. Transformación Analítica con dbt (ES)
Para probar y ejecutar las transformaciones analíticas:
```bash
dbt build --select tag:source_mi_portal --project-dir dbt --profiles-dir dbt
```

---

### 9. Aislamiento y Git: Por qué los DAGs y Contextos están Ignorados (ES)
En este repositorio, el archivo `.gitignore` está configurado intencionalmente para ignorar:
* `dags/*`: Los DAGs generados en Airflow y `_pools.json`.
* `ingestions/*`: Los dossiers de investigación y análisis local generados por los agentes.
* `.cache/`, `probes/.cache/`: Capturas y páginas intermedias descargadas durante el sondeo.
* `logs/`, `airflow_logs/`, `data/`: Datos y registros de ejecución local.

**¿Por qué?**
Para que cualquier desarrollador o empresa que clone el repositorio pueda:
1. Plantar sus propios cimientos en `Contex.md` sin conflictos.
2. Generar sus propios DAGs de Airflow según sus necesidades locales.
3. Subir sus cambios a GitHub manteniendo el repositorio central limpio y desacoplado de artefactos generados.

---

### 10. Solución de Problemas (Troubleshooting) (ES)
* **Connection refused en el puerto 8088:** Corre `make infra-up` y confirma que el contenedor `scrapagents-source-runtime` esté en estado `healthy`.
* **Timeout o error en Obscura (puerto 9222):** Verifica que `OBSCURA_CDP_TOKEN` esté configurado en tu terminal y en `.env` (al menos 32 caracteres hexadecimales).
* **DAG no aparece en Airflow:** Ejecuta `make generate-dags && make airflow-pools` y refresca el navegador en `http://localhost:8080`.
* **Tasks en Airflow quedan en estado `up_for_reschedule`:** Corre `make airflow-pools` para importar las cuotas de concurrencia requeridas por cada fuente.

---

## English

> **WELCOME TO SCRAPAGENTS:** Agent-assisted design-time harness and deterministic run-time data ingestion, normalization, and governance platform from the web to an analytical warehouse.

### Table of Contents (English)
1. [General Architecture & Concept](#1-general-architecture--concept-en)
2. [Prerequisites & Environment Setup](#2-prerequisites--environment-setup-en)
3. [Starting Local Infrastructure](#3-starting-local-infrastructure-en)
4. [Laying the Foundations: Scraping Context Setup (`Contex.md`)](#4-laying-the-foundations-scraping-context-setup-contexmd-en)
5. [Step-by-Step Flow: From a Link to an Airflow DAG](#5-step-by-step-flow-from-a-link-to-an-airflow-dag-en)
6. [Code Generation (Bronze, dbt, DAGs)](#6-code-generation-bronze-dbt-dags-en)
7. [Airflow Orchestration & Monitoring](#7-airflow-orchestration--monitoring-en)
8. [Analytical Transformation with dbt](#8-analytical-transformation-with-dbt-en)
9. [Git Isolation: Why Generated DAGs and Contexts are Ignored](#9-git-isolation-why-generated-dags-and-contexts-are-ignored-en)
10. [Troubleshooting](#10-troubleshooting-en)

---

### 1. General Architecture & Concept (EN)
ScrapAgents adheres strictly to two foundational pillars:
* **AI at Design-Time:** Autonomous agents discover portals, inspect DOM/API structures, draft schemas and contracts, and generate deterministic extractor code.
* **Zero AI at Run-Time:** Daily scheduled pipelines run 100% deterministically with high performance and zero LLM inference costs or hallucinations.

#### Detailed Area Documentation
* 🤖 [**Area 1: Agents & Skills**](areas/1_agentes_y_skills/README.md)
* 📊 [**Area 2: Data, Contracts & Modeling**](areas/2_datos_y_contratos/README.md)
* 🚀 [**Area 3: Extraction, Navigation & Runtime**](areas/3_extraccion_y_runtime/README.md)
* 🐳 [**Area 4: Orchestration, Containers & Infrastructure**](areas/4_orquestacion_e_infraestructura/README.md)

---

### 2. Prerequisites & Environment Setup (EN)
* **Docker & Docker Compose** (v2.20+).
* **Python 3.11+** (recommended `uv`).
* **Rust 1.80+** (for compiling native `source_runtime`).

```bash
# 1. Create and activate virtual environment
uv venv --python 3.13 .venv
source .venv/bin/activate

# 2. Install dependencies
uv pip install -e ".[dev,extractors,smoke]"

# 3. Configure local environment variables
make infra-env
export OBSCURA_CDP_TOKEN="$(openssl rand -hex 32)"
```

---

### 3. Starting Local Infrastructure (EN)
To start all services:
```bash
make infra-up
```

* **Airflow Web UI:** [http://localhost:8080](http://localhost:8080) (Airflow 3.4.0)
* **RustFS S3 Console:** [http://localhost:9001](http://localhost:9001) (`scrapagents` / `change-me-local-only`)
* **PostgreSQL Warehouse:** `localhost:5433` (`scrapagents` / `change-me-local-only`)
* **SourceRuntime (Rust):** `http://localhost:8088` (Ingestion worker & binary triage)
* **Obscura CDP Browser:** `http://localhost:9222` (Stealth headless browser for agents)

To shut down services: `make infra-down`.

---

### 4. Laying the Foundations: Scraping Context Setup (`Contex.md`) (EN)

When cloning this repository, the **`Contex.md`** file at the root is clean and ready for you to define your custom scraping context. This file is the **canonical source** that tells design agents what to target whenever you provide a URL.

Configure `Contex.md` with these three foundational parameters:

1. **Business Purpose:**
   * Describe in 1-2 paragraphs what data you are aggregating (e.g. public tenders, university scholarships, job listings, real estate, ecommerce products).
2. **Inclusion Criteria (En-Scope: What MUST be captured):**
   * Specific entities to extract and required canonical attributes in the contract:
     * `id`: Stable, unique identifier of the notice.
     * `title`: Formal title of the opportunity/record.
     * `publish_date`: ISO format date (`YYYY-MM-DD`).
     * `source_url`: Permanent source link.
     * `description` / `amount` / `deadline_date`: Key metadata.
3. **Exclusion Criteria (Out-of-Scope: What MUST be ignored):**
   * Negative filtering rules to prevent noisy data:
     * Routine office procurement (paper, ink cartridges).
     * General press releases and news without formal applications.
     * Behind-login portals or private intranets.
     * Secondary aggregator sites that merely redirect to third-party links.

> [!TIP]
> See also [**`docs/contexto_de_busqueda_y_criterios.md`**](contexto_de_busqueda_y_criterios.md) for an extended reference and business guide example.

---

### 5. Step-by-Step Flow: From a Link to an Airflow DAG (EN)

Once your foundations are laid in `Contex.md`, simply **pass a link (URL)** and follow the guided lifecycle. H1 and H2 validations are unified into a single gate (H2) evaluated **only once when the full context definition is completed**, with no intermediate prompts:

```text
[1. Scaffolding] ──> [2. Discovery (Link)] ──> [3. Assessment] ──> [4. Blueprint (H2 / Context)] ──> [5. Extractor] ──> [6. Generate DAG] ──> [7. Airflow Run]
```

#### Step 1: Scaffold Source Dossier
Initialize the workspace for the new target site:
```bash
make new-ingestion ID=my_source TEAM=sistemas_internos TYPE=web
```

#### Step 2: Pass the Link & Probe with Obscura (Discovery)
Pass the target URL. The design harness connects to Obscura (Rust headless browser over CDP) to probe the DOM and intercept background JSON APIs:
```bash
make probe ID=my_source URL="https://portal.example.org/opportunities"
```
Inspect findings in `ingestions/my_source/discovery.md` and advance directly:
```bash
make advance ID=my_source
```

#### Step 3: Risk Assessment
Review robots.txt, ToS, and volume estimates in `ingestions/my_source/assessment.md`. There is no intermediate confirmation gate; advance directly to Blueprint:
```bash
make advance ID=my_source
```

#### Step 4: Data Contract Design & Single Context Confirmation (Blueprint & Gate H2)
Upon concluding the context in Blueprint, target fields are mapped into the canonical schema defined in your foundations (`Contex.md`):
* Run mechanical review:
  ```bash
  make review ID=my_source
  ```
* **Single context confirmation (Gate H2):** This is where the complete context is verified in one go:
  * For low-risk / green sources:
    ```bash
    make sentinel-sign ID=my_source
    ```
  * Or sign manually as a human owner:
    ```bash
    make sign ID=my_source BY="Your Name"
    ```
  * Advance to implementation:
    ```bash
    make advance ID=my_source
    ```
  ```
* Sign Gate H2:
  ```bash
  make sign ID=my_source GATE=h2 BY="Your Name"
  make advance ID=my_source
  ```

#### Step 5: Deterministic Extractor Implementation
Implement or verify the Python extractor with zero run-time AI:
`python/scrapagents/extractors/my_source/extractor.py`
The extractor streams byte payloads directly to Rust (`SourceRuntime`), landing raw files in RustFS S3 and loading PostgreSQL Bronze.

Ensure your configs are placed in:
* Source config: `configs/ingestions/my_source.yml`
* Contract schema: `configs/contracts/my_source/records.yml`

#### Step 6: Automated Artifact Generation
Compile the Airflow YAML DAG and database structures:
```bash
# 1. Compile declarative Airflow YAML DAGs and pools
make generate-dags
make airflow-pools

# 2. Generate and apply Bronze PostgreSQL tables
make generate-bronze && make bronze-apply

# 3. Generate dbt staging models
make generate-dbt
```

#### Step 7: Orchestration & Execution in Airflow
Open [http://localhost:8080](http://localhost:8080):
1. Locate your generated DAG: `ingest__my_source`.
2. Toggle the **Unpause** switch.
3. Click **Trigger DAG** to run it immediately.
4. Watch the pipeline stream data to S3 and PostgreSQL Bronze!

---

### 6. Code Generation (Bronze, dbt, DAGs) (EN)
* `make generate-dags`: Compiles Airflow declarative YAML DAGs into `dags/`.
* `make airflow-pools`: Syncs source rate-limiting pools into Airflow.
* `make generate-bronze && make bronze-apply`: Creates PostgreSQL Bronze DDL and applies it.
* `make generate-dbt`: Generates staging and intermediate dbt models.

---

### 7. Airflow Orchestration & Monitoring (EN)
Airflow 3.4.0 parses declarative YAML files directly without running dynamic Python code, guaranteeing complete determinism and zero run-time overhead.

---

### 8. Analytical Transformation with dbt (EN)
Test and execute analytical models:
```bash
dbt build --select tag:source_my_source --project-dir dbt --profiles-dir dbt
```

---

### 9. Git Isolation: Why Generated DAGs and Contexts are Ignored (EN)
In `.gitignore`, the repository intentionally excludes:
* `dags/*`: Locally generated Airflow DAG YAML files and `_pools.json`.
* `ingestions/*`: Local discovery dossiers and agent research files.
* `.cache/`, `probes/.cache/`: Intermediary HTML/API response caches.
* `logs/`, `airflow_logs/`, `data/`: Local execution logs and databases.

**Why?**
This ensures that anyone cloning the repository can:
1. Define their custom scraping context in `Contex.md` without merge conflicts.
2. Generate and run their own Airflow DAGs locally tailored to their needs.
3. Push changes cleanly back to GitHub without polluting the central repository with ephemeral artifacts.

---

### 10. Troubleshooting (EN)
* **Port 8088 connection refused:** Run `make infra-up` and verify `scrapagents-source-runtime` is running and healthy.
* **Obscura port 9222 error:** Check that `OBSCURA_CDP_TOKEN` is set in your environment and `.env` (32+ hexadecimal characters).
* **DAG not showing in Airflow:** Run `make generate-dags && make airflow-pools` and refresh the Airflow UI at `http://localhost:8080`.
* **Airflow tasks stay `up_for_reschedule`:** Execute `make airflow-pools` to register concurrency pools.
