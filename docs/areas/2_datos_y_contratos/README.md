# Área 2: Datos, Contratos y Modelado (Producto OI)

> **PRINCIPIO:** Fuente única de verdad (**Single Source of Truth**). Todos los esquemas, reglas de validación y transformaciones se originan en `configs/contracts/` y `configs/ingestions/`. El código DDL, los modelos dbt y los DAGs se generan a partir de estas especificaciones.

---

## 1. Estructura de Contratos de Datos (`configs/contracts/<source>/<dataset>.yml`)

Cada conjunto de datos tiene un contrato formal obligatorio.

### Tipos de Datos Permitidos
`string`, `integer`, `number`, `boolean`, `object`, `array`, `json`, `date`, `timestamp`.

### Estructura Mínima Requerida
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

---

## 2. Arquitectura de Datos en Capas (Lakehouse & Warehouse)

```text
[Extractor] ──> [RustFS Landing S3] ──> [Postgres Bronze] ──> [Staging (dbt)] ──> [Intermediate (dbt)] ──> [Producto OI (Gold)]
```

### 1. Landing (RustFS S3)
* Almacena los bytes originales crudos recibidos (JSON, XML, HTML, CSV, PDF, DOCX) bajo particiones Hive inmutables:
  `s3://landing/<source_system>/<dataset>/year=YYYY/month=MM/day=DD/<batch_id>.<ext>`
* El identificador del lote (`batch_id`) es el hash **SHA-256** del payload.

### 2. Bronze (PostgreSQL Warehouse)
* Tablas tipadas generadas automáticamente (`make generate-bronze`): `bronze.<source_system>__<dataset>`.
* Estructura estándar:
  * Columnas de clave primaria (extraídas directamente del payload).
  * `payload`: Documento completo en formato `JSONB`.
  * Metadatos de linaje: `_ingested_at`, `_batch_id`, `_landing_uri`, `_record_hash`.
* Modo de persistencia recomendado: `mode: changes` (solo inserta registros nuevos o modificados).

### 3. Staging (`dbt/models/staging/`)
* Modelos generados automáticamente (`make generate-dbt`).
* Desempaquetan el JSONB a columnas SQL tipadas, limpian espacios en blanco y normalizan formatos.

### 4. Intermediate (`dbt/models/intermediate/`)
* Aplican deduplicación lógica por clave de negocio y filtran registros activos/vigentes.

### 5. Producto OI (Gold / Capa Analítica)
* Modelos canónicos consolidados para los usuarios finales.
* **Resolución de Entidades y Cruce de Colaboradores:**
  * Si dos o más instituciones publican la misma oportunidad (ej. convocatoria conjunta CAF y Banco Mundial), se unifican mediante un hash de identidad de negocio:
    $$\text{hash}(\text{título normalizado}, \text{fecha de cierre}, \text{alcance})$$
  * Los colaboradores se colapsan en una sola lista unificada (`collaborating_institutions: ["CAF", "World Bank"]`).

---

## 3. Generación y Validación de Código

* **Validar contratos:** `make check-contracts`
* **Generar tablas Bronze DDL:** `make generate-bronze`
* **Generar modelos dbt:** `make generate-dbt`
* **Compilar y probar modelos dbt:** `make dbt-check-catalog`
