# Manual de Usuario: Plataforma ScrapAgents

> **BIENVENIDO A SCRAPAGENTS:** Sistema determinista de ingesta, normalización y gobernanza de datos no estructurados y estructurados para el producto analítico **Producto OI (Opportunity Intelligence)**.
>
> Este manual consolida paso a paso la operación del sistema, desde la configuración inicial hasta la adición de nuevas fuentes y el monitoreo de DAGs.

---

## Índice

1. [Arquitectura y Concepto General](#1-arquitectura-y-concepto-general)
2. [Requisitos Previos y Configuración](#2-requisitos-previos-y-configuración)
3. [Levantamiento de la Infraestructura Local](#3-levantamiento-de-la-infraestructura-local)
4. [Criterios de Búsqueda y Negocio](#4-criterios-de-búsqueda-y-negocio)
5. [Ciclo de Vida para Añadir una Nueva Fuente](#5-ciclo-de-vida-para-añadir-una-nueva-fuente)
6. [Generación de Artefactos (Bronze, dbt, DAGs)](#6-generación-de-artefactos-bronze-dbt-dags)
7. [Orquestación y Monitoreo en Apache Airflow](#7-orquestación-y-monitoreo-en-apache-airflow)
8. [Transformación Analítica con dbt y Producto OI](#8-transformación-analítica-con-dbt-y-producto-oi)
9. [Solución de Problemas (Troubleshooting)](#9-solución-de-problemas-troubleshooting)

---

## 1. Arquitectura y Concepto General

ScrapAgents se rige por un principio fundamental:
* **La Inteligencia Artificial opera solo en Tiempo de Diseño (Design-Time):** Los agentes autónomos exploran páginas web, identifican estructuras, evalúan riesgos legales y diseñan esquemas.
* **En Tiempo de Ejecución (Run-Time), el sistema es 100% determinista:** No existen llamadas a modelos de lenguaje (LLMs) ni lógicas dinámicas dentro de los extractores de producción, tareas de Airflow o transformaciones SQL.

### Documentación Detallada por Áreas
Para profundizar en cada subsistema, consulta las guías especializadas:
* 🤖 [**Área 1: Agentes y Skills**](file:///Users/edissonmorocho/practicaspp/ScrapAgents/docs/areas/1_agentes_y_skills/README.md)
* 📊 [**Área 2: Datos, Contratos y Modelado**](file:///Users/edissonmorocho/practicaspp/ScrapAgents/docs/areas/2_datos_y_contratos/README.md)
* 🚀 [**Área 3: Extracción, Navegación y Runtime**](file:///Users/edissonmorocho/practicaspp/ScrapAgents/docs/areas/3_extraccion_y_runtime/README.md)
* 🐳 [**Área 4: Orquestación, Contenedores e Infraestructura**](file:///Users/edissonmorocho/practicaspp/ScrapAgents/docs/areas/4_orquestacion_e_infraestructura/README.md)

---

## 2. Requisitos Previos y Configuración

### Requisitos del Sistema
* **Docker y Docker Compose** (mínimo v2.20).
* **Python 3.11 o superior** (se recomienda usar `uv` para gestión rápida de entornos).
* **Rust 1.80 o superior** (con `cargo` para el runtime nativo).

### Instalación del Entorno Virtual
```bash
# Crear el entorno virtual e instalar dependencias del arnés y extractores
uv venv --python 3.13 .venv
source .venv/bin/activate
uv pip install -e ".[dev,extractors,smoke]"
```

### Configuración de Variables de Entorno
Copia el archivo de plantilla a `.env`:
```bash
make infra-env
```
Genera un token seguro para el navegador Obscura y colócalo en `.env` (o en tu shell):
```bash
export OBSCURA_CDP_TOKEN="$(openssl rand -hex 32)"
```

---

## 3. Levantamiento de la Infraestructura Local

El entorno local está unificado bajo un único [`docker-compose.yml`](file:///Users/edissonmorocho/practicaspp/ScrapAgents/docker-compose.yml). Para encender todos los servicios:

```bash
make infra-up
```

### Acceso a las Interfaces de Usuario y Servicios
* **Apache Airflow UI:** [http://localhost:8080](http://localhost:8080) (acceso directo en modo desarrollo).
* **RustFS S3 Console:** [http://localhost:9001](http://localhost:9001) (Usuario: `scrapagents`, Password: `change-me-local-only`).
* **PostgreSQL Warehouse:** `localhost:5433` (Base de datos: `scrapagents`, Usuario: `scrapagents`).
* **Microservicio SourceRuntime (Rust):** `http://localhost:8088`.
* **Obscura Headless Browser (CDP):** `http://localhost:9222`.

Para apagar los servicios:
```bash
make infra-down
```

---

## 4. Criterios de Búsqueda y Negocio

Antes de crear una fuente, consulta el documento obligatorio:
📄 [**Criterios de Búsqueda y Contexto de Negocio (Producto OI)**](file:///Users/edissonmorocho/practicaspp/ScrapAgents/docs/contexto_de_busqueda_y_criterios.md)

### Resumen Rápido: ¿Qué buscar y qué descartar?
* ✅ **EN-SCOPE (Buscar):** Subvenciones I+D+i (Grants), becas de posgrado, premios científicos, llamados a licitación/consultoría multilateral (Banco Mundial, CAF, etc.).
* ❌ **OUT-OF-SCOPE (Ignorar):** Compras rutinarias de papelería/tóner/seguridad física, noticias de prensa institucionales, trámites internos de funcionarios, portales privados con login y agregadores secundarios que solo copian enlaces.

---

## 5. Ciclo de Vida para Añadir una Nueva Fuente

Cada nueva institución transcurre por un dossier formal en `ingestions/<id>/`:

```text
Discovery ──> Assessment ──(H1)──> Blueprint ──(H2)──> Implementación ──> Verificación ──(PR)
```

### Paso 1: Crear el Dossier de la Fuente
```bash
make new-ingestion ID=mi_institucion TEAM=sistemas_internos
```
Esto crea la carpeta `ingestions/mi_institucion/` con los archivos base.

### Paso 2: Fase 1 - Discovery (Sondeo del Portal)
Ejecuta el probeo a través del navegador sigiloso Obscura:
```bash
make probe ID=mi_institucion URL="https://portal.ejemplo.org/convocatorias"
```
El agente `source-scout` completará `discovery.md` con la estructura de páginas, APIs encontradas y `robots.txt`.

Verifica el estado:
```bash
make status ID=mi_institucion
```
Cuando la evidencia esté completa, avanza de fase:
```bash
make advance ID=mi_institucion
```

### Paso 3: Fase 2 - Assessment y Gate H1 (Viabilidad)
El agente `source-assessor` analiza los riesgos legales (ToS), anti-bot y privacidad (LOPDP) en `assessment.md`.

* **Firma de Gate H1:**
  * Si la fuente está en el carril verde autorizado: el auditor automático puede firmar con:
    ```bash
    make sentinel-sign ID=mi_institucion GATE=h1
    ```
  * En casos manuales o amarillos, el humano firma en su terminal:
    ```bash
    make sign ID=mi_institucion GATE=h1 BY="Tu Nombre"
    ```
Avanza a la siguiente fase:
```bash
make advance ID=mi_institucion
```

### Paso 4: Fase 3 - Blueprint y Gate H2 (Contrato de Datos)
El agente `silver-designer` redacta el contrato formal (`contract.yml`) y el plan de adquisición (`blueprint.yml`).
El agente auditor ejecuta la revisión técnica:
```bash
make review ID=mi_institucion
```
Una vez que el veredicto sea aprobatorio, se firma el Gate H2:
```bash
make sign ID=mi_institucion GATE=h2 BY="Tu Nombre"
```
Avanza a implementación:
```bash
make advance ID=mi_institucion
```

### Paso 5: Fase 4 - Implementación del Extractor
1. Mover o confirmar la configuración en `configs/ingestions/mi_institucion.yml` y el contrato en `configs/contracts/mi_institucion/<dataset>.yml`.
2. Crear el paquete extractor en `python/scrapagents/extractors/mi_institucion/extractor.py`.

---

## 6. Generación de Artefactos (Bronze, dbt, DAGs)

Una vez que el contrato y la configuración están en `configs/`, la plataforma genera automáticamente el código determinista:

```bash
# 1. Generar DDL de tablas Bronze en PostgreSQL y registro de RustWorker
make generate-bronze

# 2. Aplicar las tablas en la base de datos PostgreSQL local
make bronze-apply

# 3. Generar modelos de dbt (Sources, Staging, Intermediate y Tests)
make generate-dbt

# 4. Generar los DAGs declarativos YAML para Airflow
make generate-dags

# 5. Importar pools de concurrencia a Airflow
make airflow-pools
```

---

## 7. Orquestación y Monitoreo en Apache Airflow

1. Abre la consola de Airflow en [http://localhost:8080](http://localhost:8080).
2. Verás los DAGs correspondientes a cada fuente bajo el nombre `ingest__<id>`.
3. Cada DAG realiza de forma secuencial:
   * **`runtime_ready`:** Verifica la disponibilidad del motor en Rust.
   * **`land__<dataset>`:** Ejecuta el extractor Python respetando el pool del sitio.
   * **`dbt_build`:** Compila y testea los modelos de staging e intermediate de esa fuente.
4. Puedes activar el DAG para su ejecución según el cron configurado o dispararlo manualmente mediante el botón **Trigger DAG**.

---

## 8. Transformación Analítica con dbt y Producto OI

Para probar las transformaciones de datos directamente desde tu terminal:
```bash
# Ejecutar transformaciones y pruebas de dbt para una fuente específica
dbt build --select tag:source_mi_institucion --project-dir dbt --profiles-dir dbt

# O verificar todos los modelos del catálogo
make dbt-check-catalog
```

En la capa **Producto OI**, las oportunidades de múltiples fuentes se combinan limpiamente:
* Si dos o más instituciones colaboran en una misma convocatoria (ej. CAF y Banco Mundial), el modelo de dbt las unifica bajo un identificador canónico único y preserva a ambas en la columna `collaborating_institutions`.

---

## 9. Solución de Problemas (Troubleshooting)

| Síntoma | Causa Frecuente | Solución Recomendada |
| :--- | :--- | :--- |
| **Error `connection refused` en puerto 8088** | `SourceRuntime` no está levantado. | Ejecuta `make infra-up` y confirma que `scrapagents-source-runtime` esté en estado `Up`. |
| **Timeout de navegación en Obscura (puerto 9222)** | Token de CDP ausente o URL no resuelta. | Verifica que `OBSCURA_CDP_TOKEN` esté definido en `.env` (al menos 32 caracteres) y que el contenedor `scrapagents-obscura` esté activo. |
| **Extractor muy lento al recorrer páginas** | Paginación profunda o pausas excesivas. | Configura `max_listing_pages: 5` en `configs/ingestions/<id>.yml` para ejecuciones diarias y asegura `block_static_resources: true`. |
| **Fallo en `make advance` por gate no firmado** | El archivo `state.yml` no tiene la firma del humano o sentinel. | Revisa con `make status ID=<id>` qué requisito falta antes de intentar avanzar la fase. |
| **Error en Airflow: "Task waiting on missing pool"** | Los pools no se han importado tras crear una nueva fuente. | Ejecuta `make airflow-pools` para sincronizar `dags/_pools.json` con la base de datos de Airflow. |
