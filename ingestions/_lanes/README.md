# Carriles de Riesgo / Risk Lanes (Macro-H1)

[![Language: ES](https://img.shields.io/badge/Language-Espa%C3%B1ol-yellow.svg)](#español)
[![Language: EN](https://img.shields.io/badge/Language-English-blue.svg)](#english)

---

## Español

> **Punto Estratégico 1 del modelo HITL:**
> Autorización macro por lotes para evitar la fatiga en la firma individual de fuentes estándar.

### Flujo de Trabajo
1. Ejecuta `make risk-matrix` para clasificar los dossiers (verde / amarillo / rojo).
2. Un **humano** autoriza el lote del carril verde:
   ```bash
   make authorize-lane LANE=green IDS="src_a src_b" BY="Tu Nombre"
   ```
3. `gate-sentinel` puede entonces auto-aprobar H1 y H2 para fuentes autorizadas que cumplan el 100% de las reglas deterministas (`make sentinel` / `make sentinel-sign`).

Las fuentes amarillas y rojas nunca se auto-firman. La mezcla de PR (`make sign GATE=pr`) siempre es realizada por un humano.

---

## English

> **Strategic Point 1 of the HITL model:**
> Batch macro-authorization to prevent individual sign-off fatigue across standardized sources.

### Operational Workflow
1. Run `make risk-matrix` to classify dossiers (green / yellow / red).
2. A **human** authorizes the green batch:
   ```bash
   make authorize-lane LANE=green IDS="src_a src_b" BY="Your Name"
   ```
3. `gate-sentinel` may then auto-sign H1 and H2 for authorized green sources that pass 100% of deterministic checks (`make sentinel` / `make sentinel-sign`).

Yellow and red sources never auto-sign. Final PR merge (`make sign GATE=pr`) is strictly human-owned.
