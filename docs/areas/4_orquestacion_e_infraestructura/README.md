# Área 4: Orquestación, Contenedores e Infraestructura / Area 4: Orchestration, Containers and Infrastructure

[![Language: ES](https://img.shields.io/badge/Language-Espa%C3%B1ol-yellow.svg)](#español)
[![Language: EN](https://img.shields.io/badge/Language-English-blue.svg)](#english)

---

## Español

> **PRINCIPIO:** Infraestructura local unificada bajo un único archivo `docker-compose.yml`. Orquestación declarativa en Apache Airflow 3.4.0 mediante DAGs nativos en YAML (AIP-85) generados automáticamente.

### 1. Topología de Contenedores (`docker-compose.yml`)

Todos los servicios locales se ejecutan en la red compartida `scrapagents_net` con nombres de contenedor explícitos y fijos:

| Servicio | Contenedor | Puerto Host | Puerto Interno | Función |
| :--- | :--- | :---: | :---: | :--- |
| **`postgres`** | `scrapagents-postgres` | `5433` | `5432` | Data Warehouse (tablas Bronze y schemas dbt). |
| **`rustfs`** | `scrapagents-rustfs` | `9000` (API), `9001` (UI) | `9000`, `9001` | Lakehouse S3 inmutable para Landing. |
| **`tika`** | `scrapagents-tika` | `9998` | `9998` | Servidor Apache Tika para extracción de PDFs/DOCXs. |
| **`source-runtime`** | `scrapagents-source-runtime` | `8088` | `8088` | Worker de Rust para ingesta, hashing y triage. |
| **`obscura`** | `scrapagents-obscura` | `9222` | `9222` | Navegador headless stealth en Rust (CDP). |
| **`airflow-db`** | `scrapagents-airflow-db` | - | `5432` | Metadatos internos de Apache Airflow. |
| **`airflow-api-server`** | `scrapagents-airflow-api-server` | `8080` | `8080` | Airflow 3 UI y servidor de APIs. |
| **`airflow-scheduler`** | `scrapagents-airflow-scheduler` | - | - | Planificador y ejecutor de tareas. |
| **`airflow-dag-processor`**| `scrapagents-airflow-dag-processor`| - | - | Procesador declarativo de DAGs en YAML. |

### 2. Orquestación Declarativa en Airflow 3.4.0 (AIP-85)

En esta plataforma, **los DAGs de Airflow nunca se escriben a mano en Python**. 

* Se definen de forma declarativa en `configs/ingestions/<id>.yml`.
* El comando `make generate-dags` compila los archivos YAML resultantes en `dags/ingest__<id>.yml`.
* Airflow 3 carga los DAGs directamente usando el plugin nativo:
  `airflow.sdk.importers.yaml_importer.YamlDagImporter`.

#### Tareas Estándar de un DAG de Ingesta
1. **`runtime_ready` (BashOperator):** Verifica que el microservicio `SourceRuntime` esté respondiendo en el puerto 8088.
2. **`land__<dataset>` (BashOperator):** Ejecuta el extractor Python correspondiente bajo su propio pool de concurrencia (`pool: <source>_source`).
3. **`landed` (EmptyOperator):** Barrera de sincronización lógica.
4. **`dbt_build` (BashOperator):** Dispara la compilación y pruebas de dbt para el selector de esa fuente (`dbt build --select tag:source_<id>`).

### 3. Comandos de Operación
```bash
make infra-up       # Levantar todos los servicios en segundo plano
make infra-down     # Detener todos los servicios
make airflow-pools  # Importar o actualizar pools de Airflow
make airflow-parse  # Verificar sintaxis y carga de DAGs en Airflow
```

---

## English

> **PRINCIPLE:** Unified local infrastructure managed under a single root `docker-compose.yml`. Declarative orchestration in Apache Airflow 3.4.0 via native YAML DAGs (AIP-85) generated automatically.

### 1. Container Topology (`docker-compose.yml`)

All local services communicate on the pre-declared bridge network `scrapagents_net` with deterministic container names:

| Service | Container Name | Host Port | Internal Port | Function |
| :--- | :--- | :---: | :---: | :--- |
| **`postgres`** | `scrapagents-postgres` | `5433` | `5432` | Data Warehouse (Bronze tables & dbt schemas). |
| **`rustfs`** | `scrapagents-rustfs` | `9000` (API), `9001` (UI) | `9000`, `9001` | Immutable S3 Lakehouse Landing. |
| **`tika`** | `scrapagents-tika` | `9998` | `9998` | Apache Tika server for PDF/DOCX text extraction. |
| **`source-runtime`** | `scrapagents-source-runtime` | `8088` | `8088` | Native Rust worker for streaming, hashing and triage. |
| **`obscura`** | `scrapagents-obscura` | `9222` | `9222` | Headless stealth browser in Rust (CDP). |
| **`airflow-db`** | `scrapagents-airflow-db` | - | `5432` | Internal Apache Airflow PostgreSQL metadata DB. |
| **`airflow-api-server`** | `scrapagents-airflow-api-server` | `8080` | `8080` | Airflow 3 Web UI and execution API server. |
| **`airflow-scheduler`** | `scrapagents-airflow-scheduler` | - | - | Task scheduler and LocalExecutor runner. |
| **`airflow-dag-processor`**| `scrapagents-airflow-dag-processor`| - | - | Declarative YAML DAG processor (AIP-85). |

### 2. Declarative Orchestration in Airflow 3.4.0 (AIP-85)

Airflow DAGs are **never hand-coded in Python**:
* Sources declare schedules, pools, and datasets in `configs/ingestions/<id>.yml`.
* `make generate-dags` compiles clean declarative YAML DAGs into `dags/ingest__<id>.yml`.
* Loaded natively via `airflow.sdk.importers.yaml_importer.YamlDagImporter`.

#### Standard DAG Task Sequence
1. **`runtime_ready` (BashOperator):** Asserts `SourceRuntime` responds on port 8088.
2. **`land__<dataset>` (BashOperator):** Runs extractor under dedicated concurrency pool (`pool_slots: 1`).
3. **`landed` (EmptyOperator):** Synchronization checkpoint.
4. **`dbt_build` (BashOperator):** Triggers dbt staging/intermediate builds and tests (`dbt build --select tag:source_<id>`).

### 3. Operational Commands
```bash
make infra-up       # Start all infrastructure containers in the background
make infra-down     # Stop and tear down all containers
make airflow-pools  # Import or refresh Airflow concurrency pools
make airflow-parse  # Parse and validate DAG syntax inside Airflow
```
