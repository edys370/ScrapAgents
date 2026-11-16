# Gate Sentinel: daad

- Phase: done
- Lane: green
- eligible_for_auto_sign: true

## Rules

| Gate | Rule | Lane | Detail |
| :--- | :--- | :--- | :--- |
| h1 | legal_tos | green | open license / permissive robots or low legal risk stated |
| h1 | anti_bot | green | probes present with blocked_by none/error only |
| h1 | privacy_lopdp | green | assessment reports no personal data |
| h2 | pool_slots | green | airflow.pool_slots is 1 |
| h2 | persistence_mode | green | all datasets use persistence.mode: changes |
| h2 | stealth | green | web source with stealth: true |
| h2 | arch_review | green | review current with Verdict: approve |

## Blockers
- none
