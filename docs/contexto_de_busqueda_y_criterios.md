# Criterios de Búsqueda y Contexto de Negocio (Producto OI)

> **DESTINATARIOS:** Agentes del arnés de diseño (`source-scout`, `source-assessor`, `silver-designer`, `arch-reviewer`, `gate-sentinel`) y revisores humanos.  
> **OBJETIVO:** Definir con precisión qué información constituye una **Oportunidad**, qué debe buscarse en cada portal institucional y qué debe excluirse estrictamente durante las fases de Discovery, Assessment, Blueprint y Contratos.

---

## 1. Propósito de Negocio: Producto OI (Opportunity Intelligence)

El Producto OI tiene como misión consolidar un catálogo centralizado y analítico de **oportunidades de financiamiento, ciencia, tecnología, innovación (I+D+i) y cooperación técnica** para investigadores, universidades, centros de desarrollo tecnológico y empresas.

Cada fuente que se analice debe evaluarse contra este objetivo central: **¿Contiene oportunidades a las cuales la comunidad académica, científica o empresarial pueda postular o acceder a fondos?**

---

## 2. Criterios de Inclusión (En-Scope: Lo que SÍ se debe buscar)

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

### Atributos Clave Requeridos en el Esquema / Contrato
Al diseñar el contrato (`contract.yml`), el agente debe procurar capturar prioritariamente estos campos:

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

---

## 3. Criterios de Exclusión (Out-of-Scope: Lo que se DEBE IGNORAR)

Los agentes **deben excluir tajantemente** los siguientes contenidos y no modelarlos en los contratos:

* ❌ **Compras y Gastos Corrientes Operativos:** Adquisición rutinaria de suministros de oficina (papel, tóner), servicios de aseo, seguridad física de edificios, mantenimiento de vehículos o pasajes corporativos.
* ❌ **Noticias y Notas de Prensa Generales:** Artículos informativos, comunicados institucionales o discursos que no contengan una convocatoria formal con requisitos y fechas.
* ❌ **Trámites Burocráticos Internos:** Manuales administrativos o circulares para empleados de la institución.
* ❌ **Portales Transaccionales o Intranets Protegidas:** Formularios de postulación que requieran usuario/clave previos para ver los requisitos. La extracción debe limitarse a la información pública previa a la postulación.
* ❌ **Agregadores Secundarios / Portales de Tráfico:** Sitios web que solo copian o reenvían enlaces hacia los sitios oficiales sin aportar datos propios. Siempre se prioriza la fuente oficial primaria.

---

## 4. Guía Operativa para los Agentes por Fase

### Fase 1: Discovery (`source-scout` → `discovery.md`)
* **Localizar la sección correcta:** Asegurarse de navegar al apartado de *Convocatorias*, *Llamados a propuestas*, *Grants*, *Procurement* o *Funding programmes*.
* **Detectar APIs subyacentes:** Monitorear el tráfico de red de Obscura. Si el portal (ej. React, Angular, Vue) consume un endpoint JSON/REST oculto, documentar la API para evitar parsear el DOM.
* **Calcular volumen real:** Medir el total de oportunidades vigentes e históricas (no sumar noticias generales).

### Fase 2: Assessment (`source-assessor` → `assessment.md`)
* **Validación de valor:** Si la página no contiene oportunidades que aporten a Producto OI, recomendar `Decision: no-go`.
* **Privacidad (LOPDP):** Identificar si las oportunidades contienen correos o nombres de funcionarios de contacto. Si los contienen, clasificarlos como `personal` en el contrato y planificar su enmascaramiento antes de Producto OI.
* **Viabilidad Técnica y Legal:** Evaluar `robots.txt`, licencias de uso y protecciones anti-bot.

### Fase 3: Blueprint y Contrato (`silver-designer` → `blueprint.yml` y `contract.yml`)
* Mapear los campos encontrados hacia el esquema canónico de oportunidades.
* Configurar persistencia `mode: changes` keyed en el identificador único.
* Asegurar que solo documentos complejos (`pdf`, `docx`) vayan a Apache Tika; payloads estructurados (`json`, `html`, `xml`) van directo a RustFS y Bronze.

### Transformación y Producto OI (`dbt`)
* **Resolución de Entidades y Cruce de Colaboradores:**
  Cuando dos o más fuentes publiquen la misma oportunidad (ej. convocatoria conjunta CAF + Banco Mundial), la capa analítica de dbt debe generar un fingerprint canónico unificado y registrar a ambas instituciones en la lista de colaboradores (`collaborating_institutions`).
