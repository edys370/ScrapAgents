# Área 4: Orquestación, Contenedores e Infraestructura

> **PRINCIPIO:** Infraestructura local unificada bajo un único archivo `docker-compose.yml`. Orquestación declarativa en Apache Airflow 3.4.0 mediante DAGs nativos en YAML (AIP-85) generados automáticamente.

---

## 1. Topología de Contenedores (`docker-compose.yml`)

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

---

## 2. Orquestación Declarativa en Airflow 3.4.0 (AIP-85)

En esta plataforma, **los DAGs de Airflow nunca se escriben a mano en Python**. 

* Se definen de forma declarativa en `configs/ingestions/<id>.yml`.
* El comando `make generate-dags` compila los archivos YAML resultantes en `dags/ingest__<id>.yml`.
* Airflow 3 carga los DAGs directamente usando el plugin nativo:
  `airflow.sdk.importers.yaml_importer.YamlDagImporter`.

### Ciclo de Tareas Estándar de un DAG de Ingesta
1. **`runtime_ready` (BashOperator):** Verifica que el microservicio `SourceRuntime` esté respondiendo en el puerto 8088.
2. **`land__<dataset>` (BashOperator):** Ejecuta el extractor Python correspondiente bajo su propio pool de concurrencia (`pool: <source>_source`).
3. **`landed` (EmptyOperator):** Barrera de sincronización lógica.
4. **`dbt_build` (BashOperator):** Dispara la compilación y pruebas de dbt para el selector de esa fuente (`dbt build --select tag:source_<id>`).

### Gestión de Pools de Concurrencia
Para evitar saturar los sitios web objetivo:
* Cada fuente declara su propio pool con `pool_slots: 1`.
* Los pools se registran automáticamente en Airflow con:
  ```bash
  make airflow-pools
  ```

---

## 3. Comandos Útiles de Infraestructura

```bash
# Levantar todos los servicios en segundo plano
make infra-up

# Detener todos los servicios
make infra-down

# Importar o actualizar pools de Airflow
make airflow-pools

# Verificar sintaxis y carga de DAGs en Airflow
make airflow-parse
```
