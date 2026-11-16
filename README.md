# ScrapAgents

Arnés de diseño y plataforma determinista de ingesta, normalización y gobernanza de datos para el **Producto OI (Opportunity Intelligence)**.

* 📖 **[Manual de Usuario Completo](docs/MANUAL_DE_USUARIO.md)**: Guía paso a paso para operar, crear fuentes y ejecutar el sistema.
* 🎯 **[Criterios de Búsqueda y Contexto de Negocio](docs/contexto_de_busqueda_y_criterios.md)**: Alcance de lo que los agentes deben buscar y modelar.
* 🏛️ **[Especificación Arquitectónica e Invariantes](AGENTS.md)**: Reglas fundacionales (Zero AI en ejecución, contratos y Obscura).

---

### Documentación por Áreas
* 🤖 **[Área 1: Agentes y Skills](docs/areas/1_agentes_y_skills/README.md)**: Roles (`source-scout`, `source-assessor`, `silver-designer`, `gate-sentinel`), compuertas H1/H2 y carriles de riesgo.
* 📊 **[Área 2: Datos, Contratos y Modelado](docs/areas/2_datos_y_contratos/README.md)**: Esquemas canónicos, Lakehouse S3 Landing, Postgres Bronze y modelos dbt.
* 🚀 **[Área 3: Extracción, Navegación y Runtime](docs/areas/3_extraccion_y_runtime/README.md)**: Motor en Rust, navegador Obscura CDP, Apache Tika y aceleración de scraping.
* 🐳 **[Área 4: Orquestación, Contenedores e Infraestructura](docs/areas/4_orquestacion_e_infraestructura/README.md)**: Docker Compose unificado y DAGs YAML en Airflow 3.4.0.

---

### Comandos Rápidos
uv venv --python 3.13 .venv && uv pip install --python .venv/bin/python -e ".[dev,extractors]"
make validate                                          # lint, pytest, cargo, gates, contracts, compose
make new-ingestion ID=world_bank TEAM=iditi            # design-time dossier in ingestions/world_bank/
make infra-up                                          # warehouse (PostgreSQL) + ingestion (RustFS, Tika, RustWorker); needs Docker
make generate-dags && make airflow-parse                     # declarative YAML DAGs -> loaded by Airflow 3.4.0
make smoke-f3                                          # F3/F4 end-to-end: Airflow -> RustWorker -> dbt (all stacks up)
make status|advance|review|probe ID=<id>               # F5 design-time workflow of a source (agents call these)
make sign ID=<id> GATE=h1|h2|pr BY="Your Name"         # HUMAN ONLY: sign a gate in your own terminal
make generate-bronze / check-bronze                      # typed bronze DDL + runtime registry from contracts
make bronze-apply                                      # create the typed bronze tables in the running warehouse
make generate-dbt / check-dbt                          # dbt sources/models from contracts / drift check
make dbt-check-catalog                                 # build models of every contract in configs/ in a scratch DB
make smoke                                             # F2 end-to-end (needs `.[smoke]`: pip install -e ".[dev,smoke]")
```

Rust is required for `make rust-test` (`rustup`, stable).
