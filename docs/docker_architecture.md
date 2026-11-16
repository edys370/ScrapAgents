# Arquitectura Docker y Contenedores / Docker Container Architecture

[![Language: ES](https://img.shields.io/badge/Language-Espa%C3%B1ol-yellow.svg)](#español)
[![Language: EN](https://img.shields.io/badge/Language-English-blue.svg)](#english)

---

## Español

> **PRINCIPIO:** Todos los servicios centrales de infraestructura (Warehouse, Almacenamiento de Objetos, Runtime de Ingesta, Navegador y Orquestación) se ejecutan bajo un **único archivo `docker-compose.yml`** en la raíz del repositorio, con nombres de contenedor explícitos y deterministas (`container_name`).

### 1. Resumen y Arquitectura Unificada
Todos los servicios se encuentran consolidados en:
* **Archivo Compose Principal:** [`docker-compose.yml`](file:///Users/edissonmorocho/practicaspp/ScrapAgents/docker-compose.yml)
* **Variables de Entorno:** [`.env`](file:///Users/edissonmorocho/practicaspp/ScrapAgents/.env) (copiado desde [`.env.example`](file:///Users/edissonmorocho/practicaspp/ScrapAgents/.env.example))
* **Red Compartida:** Red bridge `scrapagents_net`.

### 2. Inventario de Contenedores

| Servicio | Nombre Contenedor (`container_name`) | Imagen / Build | Puerto Host | Rol y Responsabilidad |
| :--- | :--- | :--- | :---: | :--- |
| **`postgres`** | `scrapagents-postgres` | `postgres:16` | `5433` | Data Warehouse: aloja tablas `bronze`, esquema de cuarentena y modelos dbt. |
| **`rustfs`** | `scrapagents-rustfs` | `rustfs/rustfs:1.0.4` | `9000`, `9001` | Data Lake S3 Landing inmutable con particionamiento Hive. |
| **`tika`** | `scrapagents-tika` | `apache/tika:4.1.0` | `9998` | Parser binario: extrae texto de PDFs y DOCXs ya almacenados en RustFS. |
| **`source-runtime`** | `scrapagents-source-runtime` | Build: `rust/source_runtime` | `8088` | RustWorker: calcula SHA-256, escribe a RustFS y carga filas a Bronze. |
| **`obscura`** | `scrapagents-obscura` | `h4ckf0r0day/obscura:0.2.6` | `9222` | Navegador headless en Rust sobre CDP para scraping sigiloso. |
| **`airflow-db`** | `scrapagents-airflow-db` | `postgres:16` | Interno | Base de datos de metadatos de Apache Airflow. |
| **`airflow-init`** | `scrapagents-airflow-init` | Build: `infra/orchestration/Dockerfile` | Efímero | Migraciones de base de datos e importación de pools (`_pools.json`). |
| **`airflow-api-server`**| `scrapagents-airflow-api-server` | Build: `infra/orchestration/Dockerfile` | `8080` | Servidor API y Web UI de Airflow 3.4.0. |
| **`airflow-scheduler`** | `scrapagents-airflow-scheduler` | Build: `infra/orchestration/Dockerfile` | Interno | Planificador y ejecutor LocalExecutor de Airflow. |
| **`airflow-dag-processor`**| `scrapagents-airflow-dag-processor`| Build: `infra/orchestration/Dockerfile` | Interno | Procesador declarativo de DAGs YAML (AIP-85). |

### 3. Volúmenes y Red
* **Red:** `scrapagents_net`
* **Volúmenes persistentes:** `postgres_data`, `rustfs_data`, `airflow_db`, `airflow_logs`.

### 4. Comandos de Operación
```bash
make infra-up      # Levantar toda la infraestructura
make infra-down    # Detener y desmontar contenedores
```

---

## English

> **PRINCIPLE:** All core infrastructure services (Warehouse, Object Storage, Ingestion Runtime, Browser, and Orchestration) run under a **single unified `docker-compose.yml`** at the repository root, with explicit, deterministic container names (`container_name`).

### 1. Overview & Architectural Shift
All services are consolidated into:
* **Root Compose File:** [`docker-compose.yml`](file:///Users/edissonmorocho/practicaspp/ScrapAgents/docker-compose.yml)
* **Environment Configuration:** [`.env`](file:///Users/edissonmorocho/practicaspp/ScrapAgents/.env) (copied from [`.env.example`](file:///Users/edissonmorocho/practicaspp/ScrapAgents/.env.example))
* **Network:** Unified bridge network `scrapagents_net`.

### 2. Container Inventory & Naming Convention

| Service | Container Name (`container_name`) | Base Image / Build Context | Exposed Host Port | Role & Responsibility |
| :--- | :--- | :--- | :---: | :--- |
| **`postgres`** | `scrapagents-postgres` | `postgres:16` | `5433` | Data Warehouse: hosts typed `bronze` tables, quarantine schema, and analytical dbt targets. |
| **`rustfs`** | `scrapagents-rustfs` | `rustfs/rustfs:1.0.4` | `9000` (S3), `9001` (UI) | Immutable S3 Landing Data Lake with Hive-style partitioning. |
| **`tika`** | `scrapagents-tika` | `apache/tika:4.1.0` | `9998` | Binary parser: extracts plain text from a PDF/DOCX already in RustFS. |
| **`source-runtime`** | `scrapagents-source-runtime` | Build: `rust/source_runtime` | `8088` | RustWorker: computes SHA-256, writes payloads to RustFS, loads typed `bronze`. |
| **`obscura`** | `scrapagents-obscura` | `h4ckf0r0day/obscura:0.2.6` | `9222` | Stealth headless browser in Rust exposing CDP over WebSocket. |
| **`airflow-db`** | `scrapagents-airflow-db` | `postgres:16` | Internal only | Metadata database for Apache Airflow. |
| **`airflow-init`** | `scrapagents-airflow-init` | Build: `infra/orchestration/Dockerfile` | Ephemeral | Database migration runner and declarative pool importer. |
| **`airflow-api-server`**| `scrapagents-airflow-api-server` | Build: `infra/orchestration/Dockerfile` | `8080` | Airflow 3.4.0 API server and Web UI. |
| **`airflow-scheduler`** | `scrapagents-airflow-scheduler` | Build: `infra/orchestration/Dockerfile` | Internal only | Airflow LocalExecutor scheduler and task runner. |
| **`airflow-dag-processor`**| `scrapagents-airflow-dag-processor`| Build: `infra/orchestration/Dockerfile` | Internal only | Declarative YAML DAG processor (AIP-85). |

### 3. Storage Volumes & Network
* **Network:** `scrapagents_net`
* **Persistent Volumes:** `postgres_data`, `rustfs_data`, `airflow_db`, `airflow_logs`.

### 4. Operational Commands (Lifecycle)
```bash
make infra-up      # Start all local infrastructure
make infra-down    # Stop and tear down all services
```
