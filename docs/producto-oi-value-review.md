# Revisión de Valor de Producto OI / Producto OI Value Review

[![Language: ES](https://img.shields.io/badge/Language-Espa%C3%B1ol-yellow.svg)](#español)
[![Language: EN](https://img.shields.io/badge/Language-English-blue.svg)](#english)

---

## Español

> **Punto Estratégico 2:** Punto de control humano después de que los extractores y modelos dbt existen, **antes** de considerar la fuente lista para el negocio. No es una revisión de código o sintaxis YAML, sino una auditoría de valor del dato para el producto.

### Lista de Verificación
1. **Utilidad de la Oportunidad:** ¿Las oportunidades capturadas aportan valor real a los investigadores y empresas del público objetivo de Producto OI?
2. **Calidad de Cruce y Deduplicación:** ¿El cruce de colaboradores e instituciones (ej. CAF + Banco Mundial + DAAD) es coherente y no genera duplicados basura?
3. **Legibilidad:** ¿Los montos, fechas de cierre, requisitos y elegibilidad son claros en la capa analítica de Producto OI?
4. **Protección de Datos Personales (LOPDP):** Si el contrato tiene `personal_data: true`, ¿los datos de contacto individual están debidamente enmascarados o excluidos de las vistas finales?
5. **Atribución Institucional:** ¿Cada oportunidad preserva su `source_url` y atribución institucional clara?

### Relación con otras Compuertas (Gates)

| Punto de Control | Responsable | Comando / Artefacto |
| :--- | :--- | :--- |
| **1. Macro-H1 (Carriles de Riesgo)** | Humano | `make risk-matrix`, `make authorize-lane` |
| **H1 / H2 Técnicos** | `gate-sentinel` (verde) o Humano | `make sentinel-sign` / `make sign` |
| **2. Valor Producto OI** | Humano | Esta lista de verificación |
| **3. PR Merge** | Humano | `make sign GATE=pr` |

---

## English

> **Strategic Point 2:** Human checkpoint after extractors and dbt models exist, **before** treating the source as business-ready. This is not a code review of selectors or YAML length; it is a business product audit.

### Checklist
1. **Opportunity Usefulness:** Do captured opportunities matter for researchers and enterprises in the intended Producto OI audience?
2. **Cross-Source Quality:** Are deduplication and collaborator/institution joins across sources (e.g. CAF + World Bank + DAAD) coherent?
3. **Legibility:** Are amounts, closing dates, eligibility, and requirements readable in the Producto OI layer (not only raw bronze JSON)?
4. **Personal Data:** If the contract has `personal_data: true`, are personal contacts masked or excluded from Producto OI surfaces?
5. **Attribution:** Does every opportunity retain `source_url` and clear institutional attribution?

### Relation to Other Gates

| Control Point | Owner | Command / Artifact |
| :--- | :--- | :--- |
| **1. Macro-H1 Risk Lane** | Human | `make risk-matrix`, `make authorize-lane` |
| **H1 / H2 Technical Gates** | `gate-sentinel` (green) or Human | `make sentinel-sign` / `make sign` |
| **2. Producto OI Value** | Human | This checklist |
| **3. PR Merge** | Human | `make sign GATE=pr` |
