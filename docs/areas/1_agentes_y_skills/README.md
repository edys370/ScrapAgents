# Área 1: Agentes y Skills / Area 1: Agents and Skills

[![Language: ES](https://img.shields.io/badge/Language-Espa%C3%B1ol-yellow.svg)](#español)
[![Language: EN](https://img.shields.io/badge/Language-English-blue.svg)](#english)

---

## Español

> **PRINCIPIO:** La Inteligencia Artificial opera **exclusivamente en Tiempo de Diseño (Design-Time)** para analizar sitios web, diseñar contratos y generar código determinista. En Tiempo de Ejecución (Run-Time) el código es 100% determinista sin llamadas a LLMs.

### 1. Inventario de Agentes

| Agente | Fase | Herramienta Clave | Responsabilidad Principal |
| :--- | :---: | :---: | :--- |
| **`source-scout`** | 1. Discovery | `make probe ID=<id> URL="<urls>"` | Inspecciona la fuente vía Obscura CDP, analiza `robots.txt`, detecta WAF/CAPTCHAs, localiza APIs ocultas y genera `discovery.md`. |
| **`source-assessor`** | 2. Assessment | `make status ID=<id>` | Evalúa la viabilidad legal (ToS), riesgo anti-bot, datos personales (LOPDP) y relevancia para Producto OI en `assessment.md`. Prepara el **Gate H1**. |
| **`silver-designer`** | 3. Blueprint | `make check-contracts` | Tras la aprobación de H1, diseña el contrato formal (`contract.yml`) y el plan de adquisición (`blueprint.yml`) con tipos estrictos y persistencia. |
| **`arch-reviewer`** | 3. Blueprint (Auditoría) | `make review ID=<id>` | Segunda mirada técnica independiente: verifica invariantes arquitectónicos, políticas de nombres y linajes antes del **Gate H2**. |
| **`gate-sentinel`** | Supervisión Automática | `make sentinel ID=<id>` | Agente auditor que valida reglas deterministas de compliance. Puede auto-firmar H1/H2 únicamente en fuentes del carril verde autorizado. |

### 2. Ciclo de Vida y Flujo de Trabajo (State Machine)

Toda nueva ingesta transcurre a través de una máquina de estados estricta:

```text
[1. Discovery] ──> [2. Assessment] ──(H1)──> [3. Blueprint] ──(H2)──> [4. Implement] ──> [5. Verify] ──> [PR Approved]
```

#### Comandos del Arnés de Diseño
* **Iniciar nuevo dossier:** `make new-ingestion ID=<id> TEAM=sistemas_internos`
* **Ver estado actual:** `make status ID=<id>`
* **Avanzar de fase:** `make advance ID=<id>` (solo avanza si la evidencia requerida está completa y el gate firmado).
* **Auditar blueprint:** `make review ID=<id>`
* **Firmar compuerta humana:** `make sign ID=<id> GATE=h1|h2|pr BY="Nombre"`

### 3. Gobernanza y Carriles de Riesgo (Risk Lanes)

Para evitar el "cuello de botella de fatiga" al procesar decenas de fuentes, la plataforma implementa carriles de riesgo:

* 🟢 **Carril Verde (`green.yml`):**
  * Fuentes públicas, datos abiertos, sin WAF bloqueante y sin PII sensible.
  * El humano autoriza el lote a nivel macro (`make authorize-lane LANE=green`).
  * `gate-sentinel` puede auto-aprobar técnicamente H1 y H2 (`make sentinel-sign`).
* 🟡 **Carril Amarillo:** Fuentes con términos ambiguos o requerimiento de crawling profundo. Requieren firma humana individual en H1.
* 🔴 **Carril Rojo:** Sitios que prohíben explícitamente scraping o tienen Cloudflare/CAPTCHA estricto. Se marcan como `no-go`.

---

## English

> **PRINCIPLE:** Artificial Intelligence operates **strictly at Design-Time** to analyze websites, design contracts, and generate deterministic code. At Run-Time, execution is 100% deterministic with zero LLM inference.

### 1. Agent Inventory

| Agent | Phase | Key Tool / Command | Primary Responsibility |
| :--- | :---: | :---: | :--- |
| **`source-scout`** | 1. Discovery | `make probe ID=<id> URL="<urls>"` | Inspects target portal via Obscura CDP, analyzes `robots.txt`, detects WAF/CAPTCHAs, uncovers hidden APIs, and writes `discovery.md`. |
| **`source-assessor`** | 2. Assessment | `make status ID=<id>` | Evaluates legal viability (ToS), anti-bot risks, privacy/PII (LOPDP), and Producto OI business relevance in `assessment.md`. Prepares **Gate H1**. |
| **`silver-designer`** | 3. Blueprint | `make check-contracts` | Following H1 sign-off, drafts the data contract (`contract.yml`) and acquisition plan (`blueprint.yml`) with strict types and persistence rules. |
| **`arch-reviewer`** | 3. Blueprint (Audit) | `make review ID=<id>` | Independent technical second pair of eyes: enforces architecture invariants, naming conventions, and lineage before **Gate H2**. |
| **`gate-sentinel`** | Automated Audit | `make sentinel ID=<id>` | Deterministic compliance auditor that verifies rules and may auto-sign H1/H2 for pre-authorized green-lane sources. |

### 2. Design-Time State Machine

Every new institutional ingestion pipeline is built through a strict 5-phase state machine:

```text
[1. Discovery] ──> [2. Assessment] ──(H1)──> [3. Blueprint] ──(H2)──> [4. Implement] ──> [5. Verify] ──> [PR Approved]
```

#### Design Harness Commands
* **Initialize new dossier:** `make new-ingestion ID=<id> TEAM=sistemas_internos`
* **Check dossier status:** `make status ID=<id>`
* **Advance phase:** `make advance ID=<id>` (only proceeds when required evidence is complete and gates are signed).
* **Run technical review:** `make review ID=<id>`
* **Human gate sign-off:** `make sign ID=<id> GATE=h1|h2|pr BY="Your Name"`

### 3. Governance and Risk Lanes

To prevent human rubber-stamping and review fatigue across large catalogues:

* 🟢 **Green Lane (`green.yml`):**
  * Public sources, open data licenses, no blocking WAF, and no sensitive personal data.
  * Human grants macro batch authorization (`make authorize-lane LANE=green`).
  * `gate-sentinel` automatically evaluates and auto-signs H1 and H2 (`make sentinel-sign`).
* 🟡 **Yellow Lane:** Ambiguous Terms of Service or deep DOM crawling required. Requires explicit individual human sign-off at H1.
* 🔴 **Red Lane:** Sites with explicit scraping bans or active, hard CAPTCHA barriers. Marked as `no-go`.
