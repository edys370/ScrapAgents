# Risk lanes (Macro-H1)

Strategic Point 1 of the HITL model:

1. Run `make risk-matrix` to classify dossiers (green / yellow / red).
2. A **human** authorizes the green batch:

   ```bash
   make authorize-lane LANE=green IDS="src_a src_b" BY="Your Name"
   ```

3. `gate-sentinel` may then auto-sign H1/H2 for authorized green sources that pass
   100% of deterministic rules (`make sentinel` / `make sentinel-sign`).

Yellow and red never auto-sign. PR merge is always human (`make sign GATE=pr`).

Files here: `green.yml` (authorization), optional notes. Generated reports live in
`build/risk_matrix.md`.
