# Producto OI value review (Strategic Point 2)

Human checkpoint after extractors and dbt models exist, **before** treating the source as
business-ready. This is not a code review of selectors or YAML length; it is a product audit.

## Checklist

1. **Opportunity usefulness** — Do captured opportunities matter for researchers / enterprises
   in the intended Producto OI audience?
2. **Cross-source quality** — Are deduplication and collaborator/institution joins across sources
   (e.g. CAF + World Bank + DAAD) coherent?
3. **Legibility** — Are amounts, closing dates, eligibility, and requirements readable in the
   Producto OI layer (not only raw bronze JSON)?
4. **Personal data** — If the contract has `personal_data: true`, are contacts masked or excluded
   from Producto OI surfaces?
5. **Attribution** — Does every opportunity retain `source_url` / institutional attribution?

## Evidence

Prefer a Data Quality dashboard or dbt tests over reading intermediate Markdown. Record decisions
in the PR description or a short note under `ingestions/<id>/` when rejecting or delaying a source.

## Relation to other gates

| Point | Owner | Command / artifact |
| :--- | :--- | :--- |
| 1 Macro-H1 risk lane | Human | `make risk-matrix`, `make authorize-lane` |
| H1/H2 technical | `gate-sentinel` (green) or human | `make sentinel-sign` / `make sign` |
| 2 Producto OI value | Human | this checklist |
| 3 PR merge | Human | `make sign GATE=pr` |
