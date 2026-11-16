# Área 3: Extracción, Navegación y Runtime

> **PRINCIPIO:** La capa de extracción ejecuta código Python y Rust determinista. Utiliza navegación sigilosa a través del navegador Obscura sobre CDP y transmite flujos de bytes directamente al motor nativo en Rust (`SourceRuntime`) para garantizar integridad y alto rendimiento.

---

## 1. Componentes del Subsistema de Extracción

```text
[Portal Externo / API]
         │
         ▼ (HTTP / CDP)
[Playwright + Obscura.sh]  <── Bloqueo automático de imágenes, CSS, fuentes y multimedia
         │
         ▼ (Stream bytes)
[SourceRuntime (RustWorker)]
         ├──> Escribe objeto inmutable en S3 (RustFS Landing)
         ├──> ¿Es PDF / DOCX? ──> [Apache Tika] ──> Extrae .txt hacia Landing
         └──> Carga registros validados en PostgreSQL Bronze
```

### 1. Obscura (`obscura.sh` en Rust)
* Navegador headless escrito en Rust diseñado para sortear barreras anti-bot (Cloudflare, Akamai, WAFs).
* Escucha en el puerto `9222` vía Chrome DevTools Protocol (CDP).
* Protegido mediante token de autenticación (`OBSCURA_CDP_TOKEN`).

### 2. Enrutador Sigiloso (`PlaywrightObscuraRouter`)
* Módulo Python en `python/scrapagents/stealth/playwright_obscura.py`.
* Conecta Playwright al navegador Obscura (`connect_over_cdp`) en lugar de levantar Chromium localmente.
* **Aceleración activa:** Bloquea por defecto recursos estáticos innecesarios (imágenes `.png/.jpg`, hojas de estilo `.css`, fuentes `.woff/.ttf` y archivos multimedia).

### 3. SourceRuntime (`RustWorker`)
* Microservicio en Rust (`rust/source_runtime/`) ejecutándose en el puerto `8088`.
* Recibe el payload en bruto, calcula su hash SHA-256 y lo deposita primero en RustFS (S3 Landing).
* **Triaje de contenido (Invariante 4):**
  * `json`, `html`, `xml`, `csv`: **Nunca** pasan por Tika; se envían directamente a PostgreSQL Bronze.
  * `pdf`, `docx`: Se despachan a Apache Tika (puerto `9998`) para extraer texto plano, el cual se guarda junto al binario en Landing.

---

## 2. Técnicas de Optimización y Rendimiento de Scraping

Para evitar ejecuciones lentas en portales institucionales grandes, se implementan las siguientes mejores prácticas:

1. **Priorizar APIs sobre el DOM:**
   Si durante Discovery se detecta una API REST/JSON interna (como en el Banco Mundial), el extractor debe consumir directamente el JSON en lugar de renderizar páginas completas.
2. **Ventana Caliente vs Carga Histórica (`max_listing_pages`):**
   * En ejecuciones programadas diarias, limitar la paginación a las primeras 3 a 5 páginas recientes.
   * Convocatorias antiguas que ya están en Bronze no deben descargarse nuevamente.
   * El flag `--full-history` permite realizar cargas completas cuando sea requerido.
3. **Pausas y Reintentos Adaptativos:**
   * Pausas aleatorias cortas (`pause_seconds_min: 1.0`, `pause_seconds_max: 2.5`).
   * Timeouts de navegación ajustados (45 segundos en lugar de 90 segundos) para detectar caídas de red rápidamente.
4. **Respeto de Concurrencia:**
   * Cada portal cuenta con su propio Pool de Airflow (`pool_slots: 1`) para evitar sobrecargar servidores gubernamentales o disparar bloqueos por IP.
