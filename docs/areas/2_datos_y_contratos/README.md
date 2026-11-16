# Área 2: Datos, Contratos y Modelado / Area 2: Data, Contracts and Modeling

[![Language: ES](https://img.shields.io/badge/Language-Espa%C3%B1ol-yellow.svg)](#español)
[![Language: EN](https://img.shields.io/badge/Language-English-blue.svg)](#english)

---

## Español

> **PRINCIPIO:** Fuente única de verdad (**Single Source of Truth**). Todos los esquemas, reglas de validación y transformaciones se originan en `configs/contracts/` y `configs/ingestions/`. El código DDL, los modelos dbt y los DAGs se generan a partir de estas especificaciones.

### 1. Estructura de Contratos de Datos (`configs/contracts/<source>/<dataset>.yml`)

Cada conjunto de datos tiene un contrato formal obligatorio.

#### Tipos de Datos Permitidos
`string`, `integer`, `number`, `boolean`, `object`, `array`, `json`, `date`, `timestamp`.

#### Estructura Mínima Requerida
```yaml
source_system: world_bank
dataset: opportunities
description: Avisos de adquisiciones y licitaciones públicas del Banco Mundial.
owner: data_team_sistemas_internos
grain: un registro por aviso de adquisición
primary_key:
  - id
columns:
  - name: id
    type: string
    required: true
    description: Identificador único del aviso.
  - name: title
    type: string
    required: true
    description: Título de la oportunidad.
  - name: publish_date
    type: date
    required: true
    description: Fecha de publicación en formato YYYY-MM-DD.
```

### 2. Arquitectura de Datos en Capas (Lakehouse & Warehouse)

```text
[Extractor] ──> [RustFS Landing S3] ──> [Postgres Bronze] ──> [Staging (dbt)] ──> [Intermediate (dbt)] ──> [Producto OI (Gold)]
```

1. **Landing (RustFS S3):** Almacena los bytes originales crudos recibidos (JSON, XML, HTML, CSV, PDF, DOCX) bajo particiones Hive inmutables (`batch_id` es el SHA-256).
2. **Bronze (PostgreSQL Warehouse):** Tablas tipadas generadas automáticamente (`bronze.<source_system>__<dataset>`) con clave primaria, columna `payload` (JSONB) y metadatos de linaje.
3. **Staging (`dbt/models/staging/`):** Desempaqueta el JSONB a columnas SQL tipadas y normaliza formatos.
4. **Intermediate (`dbt/models/intermediate/`):** Aplica deduplicación lógica y filtros de vigencia.
5. **Producto OI (Gold / Capa Analítica):** Modela oportunidades unificadas. Si dos instituciones colaboran en una misma convocatoria (ej. CAF + Banco Mundial), se unifican mediante un hash canónico y se registran en `collaborating_institutions`.

### 3. Generación y Validación de Código
* **Validar contratos:** `make check-contracts`
* **Generar tablas Bronze DDL:** `make generate-bronze`
* **Generar modelos dbt:** `make generate-dbt`
* **Compilar y probar modelos dbt:** `make dbt-check-catalog`

---

## English

> **PRINCIPLE:** Single Source of Truth. All schemas, validation rules, and analytical mappings originate strictly in `configs/contracts/` and `configs/ingestions/`. DDL, dbt models, and Airflow DAGs are compiled from these specifications.

### 1. Data Contract Structure (`configs/contracts/<source>/<dataset>.yml`)

Every ingested dataset requires a formal declarative contract.

#### Allowed Column Types
`string`, `integer`, `number`, `boolean`, `object`, `array`, `json`, `date`, `timestamp`.

#### Minimum Contract Structure
```yaml
source_system: world_bank
dataset: opportunities
description: World Bank procurement and consultancy notices.
owner: data_team_sistemas_internos
grain: one record per procurement notice
primary_key:
  - id
columns:
  - name: id
    type: string
    required: true
    description: Unique notice identifier.
  - name: title
    type: string
    required: true
    description: Opportunity title.
  - name: publish_date
    type: date
    required: true
    description: Publication date in YYYY-MM-DD format.
```

### 2. Layered Data Architecture (Lakehouse & Warehouse)

```text
[Extractor] ──> [RustFS Landing S3] ──> [Postgres Bronze] ──> [Staging (dbt)] ──> [Intermediate (dbt)] ──> [Producto OI (Gold)]
```

1. **Landing (RustFS S3):** Stores immutable raw bytes (JSON, XML, HTML, CSV, PDF, DOCX) under Hive-style partitions. The batch ID is the SHA-256 hash.
2. **Bronze (PostgreSQL Warehouse):** Typed tables (`bronze.<source_system>__<dataset>`) holding primary keys, full JSONB payload, and lineage columns (`_ingested_at`, `_batch_id`, `_landing_uri`, `_record_hash`).
3. **Staging (`dbt/models/staging/`):** Unpacks JSONB into typed relational SQL columns and cleans strings.
4. **Intermediate (`dbt/models/intermediate/`):** Enforces grain deduplication and active status filtering.
5. **Producto OI (Gold Layer):** Canonical analytical models. Collaborative opportunities across multiple portals (e.g., CAF and World Bank co-funding) are unified via canonical fingerprinting into a single opportunity with merged `collaborating_institutions`.

### 3. Code Generation and Verification
* **Validate contracts:** `make check-contracts`
* **Generate Bronze DDL:** `make generate-bronze`
* **Generate dbt models:** `make generate-dbt`
* **Build & test dbt catalog:** `make dbt-check-catalog`
