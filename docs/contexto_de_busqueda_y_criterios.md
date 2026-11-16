# Criterios de Búsqueda y Contexto de Negocio / Search Criteria and Business Context

[![Language: ES](https://img.shields.io/badge/Language-Espa%C3%B1ol-yellow.svg)](#español)
[![Language: EN](https://img.shields.io/badge/Language-English-blue.svg)](#english)

---

## Español

> **DESTINATARIOS:** Agentes del arnés de diseño (`source-scout`, `source-assessor`, `silver-designer`, `arch-reviewer`, `gate-sentinel`) y revisores humanos.  
> **OBJETIVO:** Definir con precisión qué información constituye una **Oportunidad**, qué debe buscarse en cada portal institucional y qué debe excluirse estrictamente durante las fases de Discovery, Assessment, Blueprint y Contratos.

### 1. Propósito de Negocio: Producto OI (Opportunity Intelligence)

El Producto OI tiene como misión consolidar un catálogo centralizado y analítico de **oportunidades de financiamiento, ciencia, tecnología, innovación (I+D+i) y cooperación técnica** para investigadores, universidades, centros de desarrollo tecnológico y empresas.

Cada fuente que se analice debe evaluarse contra este objetivo central: **¿Contiene oportunidades a las cuales la comunidad académica, científica o empresarial pueda postular o acceder a fondos?**

### 2. Criterios de Inclusión (En-Scope: Lo que SÍ se debe buscar)

Los agentes deben mapear y extraer exclusivamente registros que correspondan a:

1. **Subvenciones y Fondos de I+D+i (Grants):**
   * Fondos concursables para proyectos de investigación, innovación y transferencia tecnológica.
   * Convocatorias multilaterales o bilaterales (ej. DAAD, CYTED, IDRC, Horizonte Europa).
2. **Becas y Movilidad Académica/Científica:**
   * Programas de financiamiento para maestrías, doctorados, estancias de investigación y pasantías postdoctorales.
3. **Licitaciones Internacionales y Consultorías de Alto Valor (Procurement):**
   * Solicitudes de Expresiones de Interés (REOI) e Invitaciones a Licitar (IFB) emitidas por organismos multilaterales (ej. Banco Mundial, CAF, BID, agencias de la ONU).
   * Servicios de consultoría especializada, estudios técnicos y desarrollo de capacidades.
4. **Premios Científicos y Reconocimientos con Dotación Económica.**

#### Atributos Clave Requeridos en el Esquema / Contrato

| Campo Canónico | Tipo | Descripción | Obligatorio |
| :--- | :---: | :--- | :---: |
| `id` / `notice_id` | `string` | Identificador único y estable de la convocatoria en el portal de origen. | **Sí (PK)** |
| `title` | `string` | Título formal y descriptivo de la convocatoria u oportunidad. | **Sí** |
| `issuing_organization` | `string` | Institución que publica o financia los fondos (ej. "Banco Mundial", "DAAD"). | **Sí** |
| `publish_date` | `date` | Fecha en que fue publicada o abierta la convocatoria (formato ISO `YYYY-MM-DD`). | **Sí** |
| `deadline_date` | `date` / `string` | Fecha límite para presentar propuestas o postulación. | Recomendado |
| `description` / `summary` | `string` | Resumen ejecutivo, objetivos o alcance de la convocatoria. | Recomendado |
| `budget` / `amount` | `number` / `string` | Monto financiado o techo presupuestario (si está explícito). | Opcional |
| `currency` | `string` | Código de moneda (ej. "USD", "EUR", "CNY"). | Opcional |
| `eligibility` | `string` | Requisitos de quién puede postular (países admisibles, tipos de institución). | Recomendado |
| `source_url` | `string` | Enlace permanente directo a la oportunidad o formulario oficial. | **Sí** |
| `attachments` | `array` / `string` | Enlaces a bases, pliegos o términos de referencia (PDF/DOCX). | Opcional |

### 3. Criterios de Exclusión (Out-of-Scope: Lo que se DEBE IGNORAR)

Los agentes **deben excluir tajantemente** los siguientes contenidos y no modelarlos en los contratos:

* ❌ **Compras y Gastos Corrientes Operativos:** Adquisición rutinaria de suministros de oficina (papel, tóner), servicios de aseo, seguridad física de edificios, mantenimiento de vehículos o pasajes corporativos.
* ❌ **Noticias y Notas de Prensa Generales:** Artículos informativos, comunicados institucionales o discursos que no contengan una convocatoria formal con requisitos y fechas.
* ❌ **Trámites Burocráticos Internos:** Manuales administrativos o circulares para empleados de la institución.
* ❌ **Portales Transaccionales o Intranets Protegidas:** Formularios de postulación que requieran usuario/clave previos para ver los requisitos. La extracción debe limitarse a la información pública previa a la postulación.
* ❌ **Agregadores Secundarios / Portales de Tráfico:** Sitios web que solo copian o reenvían enlaces hacia los sitios oficiales sin aportar datos propios. Siempre se prioriza la fuente oficial primaria.

### 4. Guía Operativa para los Agentes por Fase

* **Discovery (`source-scout` → `discovery.md`):** Identificar la sección exacta de convocatorias, revisar robots.txt, detectar APIs JSON subyacentes, estimar volumen real de convocatorias (no contar noticias).
* **Assessment (`source-assessor` → `assessment.md`):** Evaluar relevancia para Producto OI, verificar que no se arrastre PII innecesaria, evaluar riesgo ToS/anti-bot.
* **Blueprint y Contrato (`silver-designer` → `blueprint.yml` y `contract.yml`):** Mapear los campos encontrados hacia el esquema canónico de oportunidades con tipos válidos y persistencia `mode: changes`.
* **Cruce de Oportunidades Colaborativas (`dbt`):** Si dos instituciones publican la misma oportunidad (ej. CAF y Banco Mundial), se unifican bajo un hash canónico y se combinan en `collaborating_institutions`.

---

## English

> **TARGET AUDIENCE:** Design-time harness agents (`source-scout`, `source-assessor`, `silver-designer`, `arch-reviewer`, `gate-sentinel`) and human reviewers.  
> **PURPOSE:** Rigorously define what constitutes an **Opportunity**, what must be targeted in each institutional portal, and what must be strictly excluded during Discovery, Assessment, Blueprint, and Contract phases.

### 1. Business Purpose: Producto OI (Opportunity Intelligence)

Producto OI aims to build a centralized, analytical catalogue of **funding, science, technology, innovation (R&D&I), and international cooperation opportunities** for researchers, universities, technology centers, and enterprises.

Every analyzed source must be evaluated against this core question: **Does it provide actionable opportunities through which academic, scientific, or business communities can apply for funding?**

### 2. Inclusion Criteria (En-Scope: What MUST be captured)

Agents must exclusively map and extract records corresponding to:

1. **R&D&I Grants and Research Funds:**
   * Competitive funding for research, technological innovation, and transfer projects.
   * Bilateral or multilateral funding programs (e.g., DAAD, CYTED, IDRC, Horizon Europe).
2. **Scholarships and Academic/Scientific Mobility:**
   * Funding for master's degrees, PhDs, research visits, and postdoctoral fellowships.
3. **International Competitive Procurement and High-Value Consultancies:**
   * Requests for Expressions of Interest (REOI) and Invitations for Bids (IFB) from multilateral organizations (e.g., World Bank, CAF, IDB, UN agencies).
   * Specialized technical consulting, feasibility studies, and institutional capacity building.
4. **Scientific Awards and Endowed Prizes.**

#### Key Schema Attributes for Data Contracts

| Canonical Field | Type | Description | Required |
| :--- | :---: | :--- | :---: |
| `id` / `notice_id` | `string` | Unique, stable notice identifier on the source portal. | **Yes (PK)** |
| `title` | `string` | Formal, descriptive title of the funding opportunity. | **Yes** |
| `issuing_organization` | `string` | Funding or issuing institution (e.g., "World Bank", "DAAD"). | **Yes** |
| `publish_date` | `date` | Date the opportunity was published/opened (ISO `YYYY-MM-DD`). | **Yes** |
| `deadline_date` | `date` / `string` | Submission deadline date. | Recommended |
| `description` / `summary` | `string` | Executive summary, objectives, or scope. | Recommended |
| `budget` / `amount` | `number` / `string` | Total grant budget or funding ceiling (if explicit). | Optional |
| `currency` | `string` | ISO currency code (e.g., "USD", "EUR", "CNY"). | Optional |
| `eligibility` | `string` | Eligibility rules (admissible countries, eligible institutions). | Recommended |
| `source_url` | `string` | Permanent URL to the opportunity notice or official page. | **Yes** |
| `attachments` | `array` / `string` | Links to terms of reference, bidding guidelines (PDF/DOCX). | Optional |

### 3. Exclusion Criteria (Out-of-Scope: What MUST BE IGNORED)

Agents **must strictly avoid** capturing the following content:

* ❌ **Routine Operational Procurement:** Paper, toner, cleaning services, building physical security, vehicle maintenance, or corporate travel.
* ❌ **General News and Press Releases:** Informational news, institutional speeches, or photo-ops lacking formal application deadlines and requirements.
* ❌ **Internal Administrative Procedures:** Bureaucratic notices or internal directives for agency employees.
* ❌ **Gated/Intranet Portals:** Forms requiring prior authentication or user accounts to inspect terms. Extraction is strictly limited to public pre-application details.
* ❌ **Secondary Scraper Aggregators:** Portals that republish or mirror links without authoring data. Primary official sources are always preferred.

### 4. Agent Guidelines by Phase

* **Discovery (`source-scout` → `discovery.md`):** Locate true call sections, inspect robots.txt, record backend JSON APIs, calculate real active notice volume.
* **Assessment (`source-assessor` → `assessment.md`):** Verify value proposition for Producto OI, classify PII (exclude individual contact info), assess ToS/anti-bot risks.
* **Blueprint & Contract (`silver-designer` → `blueprint.yml` and `contract.yml`):** Map fields to standard types with `mode: changes` persistence. Complex binaries go to Tika; structured data goes directly to Bronze.
* **Collaborative Merge (`dbt`):** Cross-portal collaborative opportunities (e.g., joint CAF + World Bank calls) are fingerprinted into a unified canonical record with merged `collaborating_institutions`.
