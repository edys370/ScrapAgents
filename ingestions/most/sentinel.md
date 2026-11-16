# Gate Sentinel: most

- Phase: done
- Lane: yellow
- eligible_for_auto_sign: false

## Rules

| Gate | Rule | Lane | Detail |
| :--- | :--- | :--- | :--- |
| h1 | legal_tos | yellow | no clear open license and no hard ban; human Macro-H1 / manual H1 required |
| h1 | anti_bot | green | probes present with blocked_by none/error only |
| h1 | privacy_lopdp | green | personal_data true with not_extracted and/or masking policy |
| h2 | pool_slots | green | airflow.pool_slots is 1 |
| h2 | persistence_mode | green | all datasets use persistence.mode: changes |
| h2 | stealth | green | web source with stealth: true |
| h2 | arch_review | green | review current with Verdict: approve |

## Blockers
- none
