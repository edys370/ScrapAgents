# Área 1: Agentes y Skills (Diseño Autónomo de Fuentes)

> **PRINCIPIO:** La Inteligencia Artificial opera **exclusivamente en Tiempo de Diseño (Design-Time)** para analizar sitios web, diseñar contratos y generar código determinista. En Tiempo de Ejecución (Run-Time) el código es 100% determinista sin llamadas a LLMs.

---

## 1. Inventario de Agentes

| Agente | Fase | Herramienta Clave | Responsabilidad Principal |
| :--- | :---: | :---: | :--- |
| **`source-scout`** | 1. Discovery | `make probe ID=<id> URL="<urls>"` | Inspecciona la fuente vía Obscura CDP, analiza `robots.txt`, detecta WAF/CAPTCHAs, localiza APIs ocultas y genera `discovery.md`. |
| **`source-assessor`** | 2. Assessment | `make status ID=<id>` | Evalúa la viabilidad legal (ToS), riesgo anti-bot, datos personales (LOPDP) y relevancia para Producto OI en `assessment.md`. Prepara el **Gate H1**. |
| **`silver-designer`** | 3. Blueprint | `make check-contracts` | Tras la aprobación de H1, diseña el contrato formal (`contract.yml`) y el plan de adquisición (`blueprint.yml`) con tipos estrictos y persistencia. |
| **`arch-reviewer`** | 3. Blueprint (Auditoría) | `make review ID=<id>` | Segunda mirada técnica independiente: verifica invariantes arquitectónicos, políticas de nombres y linajes antes del **Gate H2**. |
| **`gate-sentinel`** | Supervisión Automática | `make sentinel ID=<id>` | Agente auditor que valida reglas deterministas de compliance. Puede auto-firmar H1/H2 únicamente en fuentes del carril verde autorizado. |

---

## 2. Ciclo de Vida y Flujo de Trabajo (State Machine)

Toda nueva ingesta transcurre a través de una máquina de estados estricta:

```text
[1. Discovery] ──> [2. Assessment] ──(H1)──> [3. Blueprint] ──(H2)──> [4. Implement] ──> [5. Verify] ──> [PR Approved]
```

### Comandos del Arnés de Diseño
* **Iniciar nuevo dossier:** `make new-ingestion ID=<id> TEAM=sistemas_internos`
* **Ver estado actual:** `make status ID=<id>`
* **Avanzar de fase:** `make advance ID=<id>` (solo avanza si la evidencia requerida está completa y el gate firmado).
* **Auditar blueprint:** `make review ID=<id>`
* **Firmar compuerta humana:** `make sign ID=<id> GATE=h1|h2|pr BY="Nombre"`

---

## 3. Gobernanza y Carriles de Riesgo (Risk Lanes)

Para evitar el "cuello de botella de fatiga" al procesar decenas de fuentes, la plataforma implementa carriles de riesgo:

* 🟢 **Carril Verde (`green.yml`):**
  * Fuentes públicas, datos abiertos, sin WAF bloqueante y sin PII sensible.
  * El humano autoriza el lote a nivel macro (`make authorize-lane LANE=green`).
  * `gate-sentinel` puede auto-aprobar técnicamente H1 y H2 (`make sentinel-sign`).
* 🟡 **Carril Amarillo:** Fuentes con términos ambiguos o requerimiento de crawling profundo. Requieren firma humana individual en H1.
* 🔴 **Carril Rojo:** Sitios que prohíben explícitamente scraping o tienen Cloudflare/CAPTCHA estricto. Se marcan como `no-go`.
