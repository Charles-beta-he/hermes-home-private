# Freeze Mobile Offline Avatar + Travel SSOT — quota observability brief

Generated: 2026-06-25T23:28:15+08:00
Task: 2026-06-25-为-2026-06-21-freeze-mobile-offline-avatar--travel-ssot-细化-quota-observability-收敛
Parent: 2026-06-21-freeze-mobile-offline-avatar--travel-ssot
Parent artifact: /Users/charles/.hermes/tick-20260624-152533-311040-p65260-fe9d0e26-a5e34c19/discussion_result.json
Quota advisory artifact: /Users/charles/.hermes/tick-20260624-202621-613510-p26601-4aeab818-ec2c5702/discussion_result.json

## File access boundary used

Allowed reads:
- Child task note under `/Users/charles/Documents/brain/05-实践与项目/tasks/`
- Parent certification artifact and quota advisory artifact under `/Users/charles/.hermes/tick-*`
- MOAT project profile/progress ledger under `/Users/charles/.hermes/project-profiles/` and `/Users/charles/.hermes/workflows/product/mobile-offline-avatar-travel/`

Allowed writes:
- This evidence artifact.
- The child task note proof log/status only.
- The MOAT progress ledger summary only.

Forbidden:
- provider auth material, local env files, SSH material, and private auth paths.
- Runtime deploy/push/device/cloud side effects.

## Source evidence summary

Quota advisory round:
- status: `certified`
- fanout: `fanout_quorum_met`, success_count=`2`
- truth gate: `grounded`, evidence_coverage=`1.0`
- unresolved issues: `[]`
- quota_confidence: `{'estimated_count': 0, 'exact_count': 0, 'exhausted_count': 0, 'has_low_confidence_quota': True, 'low_confidence_models': ['claude-opus-4-8', 'gpt-5.5'], 'schema_version': 1, 'unknown_count': 0, 'unobservable_count': 2}`

## Quota state table

| Model key | Source | Observability | Status | Confidence | Stale after seconds | Unknown handling evidence |
|---|---|---|---|---:|---:|---|
| claude-code::claude-opus-4-8 | response_headers | unobservable | unobservable | 0.2 | 300 | remaining/reset unavailable (`remaining_requests=None`, `reset_at=None`) |
| openai-codex::gpt-5.5 | response_headers | unobservable | unobservable | 0.2 | 300 | remaining/reset unavailable (`remaining_requests=None`, `reset_at=None`) |

## Narrowed semantics

1. Source of quota state:
   - File-backed discussion artifact: `/Users/charles/.hermes/tick-20260624-202621-613510-p26601-4aeab818-ec2c5702/discussion_result.json`.
   - The values are captured in `final_design.quota_confidence` and `final_design.quota_snapshot`.

2. Confidence:
   - `has_low_confidence_quota=true`.
   - `exact_count=0`, `estimated_count=0`, `unknown_count=0`, `unobservable_count=2`.
   - Both consulted providers are low-confidence because subscription-cap remaining/reset values are not observable from response headers.

3. Staleness:
   - Each snapshot carries `stale_after_seconds=300`.
   - After that window, any scheduler/ratification logic must treat the snapshot as stale advisory context, not authoritative live quota.

4. Unknown/unobservable handling:
   - `unobservable` is not the same as `exhausted`; `exhausted_count=0`.
   - It is also not enough to authorize broad fallback changes by itself.
   - Correct fail-closed behavior: continue parent ratification only if required claims and evidence are grounded without depending on exact quota; if exact quota is required, request fresh quota evidence or route through a lower-blast-radius path.

5. File-backed evidence locations:
   - Quota advisory artifact: `/Users/charles/.hermes/tick-20260624-202621-613510-p26601-4aeab818-ec2c5702/discussion_result.json`.
   - Parent certification artifact: `/Users/charles/.hermes/tick-20260624-152533-311040-p65260-fe9d0e26-a5e34c19/discussion_result.json`.
   - This narrowed brief: `/Users/charles/.hermes/workflows/product/mobile-offline-avatar-travel/evidence/non-convergence-narrowing/freeze-ssot-quota-observability-20260625.md`.

## Minimum next action for parent

Parent can consume this artifact to close the quota-observability axis: quota state is known to be low-confidence/unobservable but non-blocking for no-action certification because the parent truth gate is grounded without exact quota. Future runtime policy changes should not be derived from this artifact alone; they require fresh quota probes or provider-specific observable limits.

## Rollback / degradation boundary

Documentation/evidence only. Rollback: delete this artifact and revert child task proof-log/ledger additions. No runtime, source code, deployment, private auth material, or external state changed.
