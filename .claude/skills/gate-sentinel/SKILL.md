---
name: gate-sentinel
description: Run Gate Sentinel compliance rules, produce the risk matrix, and auto-sign H1/H2 for Macro-H1 authorized green-lane sources. Use when auditing assessment/blueprint gates, batch-approving sources, or advancing past H1/H2 without per-file human micro-signing.
disable-model-invocation: false
---

# Gate Sentinel (`gate-sentinel`)

> Humans decide **Macro-H1** (green batch), **Producto OI value**, and **PR merge**.
> `gate-sentinel` audits H1/H2 policy and may auto-sign only for authorized greens.

## Commands

```bash
make risk-matrix
make authorize-lane LANE=green IDS="src_a src_b" BY="<Human>"   # human TTY only
make sentinel ID=<id>
make sentinel-sign ID=<id> GATE=h1|h2                             # agents OK when eligible
make sign ID=<id> GATE=pr BY="<Human>"                            # human only; never sentinel
```

## Per-source flow

1. After `source-assessor` finishes → `make sentinel ID=<id>`.
2. If lane is green, eligible, and Macro-H1 authorized → `make sentinel-sign ... GATE=h1` → `make advance`.
3. After `arch-reviewer` approve → `make sentinel ID=<id>` again → `make sentinel-sign ... GATE=h2` → `make advance`.
4. Yellow/red → present to human; do not auto-sign.
5. After implement/verify → human PR: `make sign GATE=pr`.

## Batch flow (Strategic Point 1)

1. `make risk-matrix` → `build/risk_matrix.md`.
2. Human authorizes greens once via `make authorize-lane`.
3. For each authorized green dossier in the right phase, run sentinel-sign + advance.

## Never

- Auto-sign PR.
- Edit `state.yml` by hand.
- Treat yellow/red as green.
- Sign an id not listed in `ingestions/_lanes/green.yml`.
