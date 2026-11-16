# ScrapAgents

[![Language: ES](https://img.shields.io/badge/Language-Espa%C3%B1ol-yellow.svg)](#español)
[![Language: EN](https://img.shields.io/badge/Language-English-blue.svg)](#english)

---

## Español

Arnés de diseño y plataforma determinista de ingesta, normalización y gobernanza de datos para el **Producto OI (Opportunity Intelligence)**.

### Enlaces Principales
* 📖 **[Manual de Usuario Completo](docs/MANUAL_DE_USUARIO.md)**: Guía paso a paso para operar, crear fuentes y ejecutar el sistema.
* 🎯 **[Criterios de Búsqueda y Contexto de Negocio](docs/contexto_de_busqueda_y_criterios.md)**: Alcance de lo que los agentes deben buscar y modelar.
* 🏛️ **[Especificación Arquitectónica e Invariantes](AGENTS.md)**: Reglas fundacionales (Zero AI en ejecución, contratos y Obscura).

### Documentación por Áreas
* 🤖 **[Área 1: Agentes y Skills](docs/areas/1_agentes_y_skills/README.md)**: Roles (`source-scout`, `source-assessor`, `silver-designer`, `gate-sentinel`), compuertas H1/H2 y carriles de riesgo.
* 📊 **[Área 2: Datos, Contratos y Modelado](docs/areas/2_datos_y_contratos/README.md)**: Esquemas canónicos, Lakehouse S3 Landing, Postgres Bronze y modelos dbt.
* 🚀 **[Área 3: Extracción, Navegación y Runtime](docs/areas/3_extraccion_y_runtime/README.md)**: Motor en Rust, navegador Obscura CDP, Apache Tika y aceleración de scraping.
* 🐳 **[Área 4: Orquestación, Contenedores e Infraestructura](docs/areas/4_orquestacion_e_infraestructura/README.md)**: Docker Compose unificado y DAGs YAML en Airflow 3.4.0.

### Comandos Rápidos
```bash
uv venv --python 3.13 .venv && uv pip install --python .venv/bin/python -e ".[dev,extractors]"
make validate                                          # linter, pytest, cargo, compuertas, contratos
make new-ingestion ID=world_bank TEAM=iditi            # crear nuevo dossier en ingestions/world_bank/
make infra-up                                          # encender infraestructura Docker unificada
make generate-dags && make airflow-parse               # generar y verificar DAGs declarativos YAML
make smoke-f3                                          # prueba end-to-end completa F3/F4
make status|advance|review|probe ID=<id>               # ciclo de vida de diseño (usado por agentes)
make sign ID=<id> GATE=h1|h2|pr BY="Tu Nombre"         # SOLO HUMANOS: firmar compuerta en terminal
make generate-bronze / check-bronze                    # DDL de tablas Bronze y registro de RustWorker
make bronze-apply                                      # aplicar tablas Bronze en PostgreSQL
make generate-dbt / check-dbt                          # modelos de staging/intermediate dbt
make dbt-check-catalog                                 # construir y probar modelos dbt
make smoke                                             # prueba end-to-end de ingesta F2
```

---

## English

Design-time harness and deterministic run-time data ingestion, normalization, and governance platform for **Producto OI (Opportunity Intelligence)**.

### Key Links
* 📖 **[Complete User Manual](docs/MANUAL_DE_USUARIO.md)**: Step-by-step operational guide for creating sources and running pipelines.
* 🎯 **[Search Criteria and Business Context](docs/contexto_de_busqueda_y_criterios.md)**: Scope defining what agents must search and model.
* 🏛️ **[Architectural Specification & Invariants](AGENTS.md)**: Foundational principles (Zero AI at runtime, contracts, and Obscura).

### Documentation by Areas
* 🤖 **[Area 1: Agents & Skills](docs/areas/1_agentes_y_skills/README.md)**: Agent roles (`source-scout`, `source-assessor`, `silver-designer`, `gate-sentinel`), H1/H2 gates, and risk lanes.
* 📊 **[Area 2: Data, Contracts & Modeling](docs/areas/2_datos_y_contratos/README.md)**: Canonical schemas, Lakehouse S3 Landing, Postgres Bronze, and dbt models.
* 🚀 **[Area 3: Extraction, Navigation & Runtime](docs/areas/3_extraccion_y_runtime/README.md)**: Native Rust worker, Obscura CDP stealth browser, Apache Tika, and scraping speedups.
* 🐳 **[Area 4: Orchestration, Containers & Infrastructure](docs/areas/4_orquestacion_e_infraestructura/README.md)**: Unified Docker Compose and declarative YAML DAGs in Airflow 3.4.0.

### Quick Commands
```bash
uv venv --python 3.13 .venv && uv pip install --python .venv/bin/python -e ".[dev,extractors]"
make validate                                          # lint, pytest, cargo, gates, contracts, compose
make new-ingestion ID=world_bank TEAM=iditi            # design-time dossier in ingestions/world_bank/
make infra-up                                          # start unified Docker infrastructure
make generate-dags && make airflow-parse               # compile and verify declarative YAML DAGs
make smoke-f3                                          # F3/F4 end-to-end validation test
make status|advance|review|probe ID=<id>               # design lifecycle commands (called by agents)
make sign ID=<id> GATE=h1|h2|pr BY="Your Name"         # HUMAN ONLY: sign gate in terminal
make generate-bronze / check-bronze                    # generate typed bronze DDL + registry
make bronze-apply                                      # apply typed bronze tables in PostgreSQL
make generate-dbt / check-dbt                          # generate staging/intermediate dbt models
make dbt-check-catalog                                 # test build dbt models in scratch DB
make smoke                                             # F2 end-to-end ingestion test
```

Rust is required for `make rust-test` (`rustup`, stable).
