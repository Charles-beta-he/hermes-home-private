---
type: backlog
layer: L3
status: active
created: 2026-05-06T18:29:31+08:00
project: cybernetic-multimodel-intervention
---

# P9 - Implementation Backlog

## P0 — 本轮完成

### P0.1 Artifact landing

Create P10/P9/project/playbook/review/task/evolution/atoms and link theory notes。

Acceptance checks:

- `python3 ~/.hermes/scripts/cybernetic_multimodel_selfcheck.py --json`
- required artifacts exist。

### P0.2 Deterministic gate

Run local proof commands。This includes brainctl sync / reindex / search as the deterministic audit path。

Acceptance checks:

- `python3 ~/.hermes/scripts/brainctl.py --json sync`
- `python3 ~/.hermes/scripts/brainctl.py --json reindex`
- `python3 ~/.hermes/scripts/brainctl.py --json search "cybernetic multi-model intervention first-order second-order observer" --limit 8`
- structural audit: empty_dirs=[], top_level_no_index=[], parent_no_direct_md_top=[], broken_wikilinks_count=0, secret_pattern_hits=0。

### P0.3 Multi-model caveat ledger

Record planner status and timeout/dissent as provenance。

Acceptance checks:

- review contains `not_certified`。
- review contains `issue_ledger`。
- review contains `timeout` and `dissent`。

## P1 — 协议工程化

### P1.1 consult_models state template

Create reusable state template for cybernetic multi-model intervention：

- object_task
- first_order_claims
- evidence_requests
- second_order_self_audit
- issue_ledger
- deterministic_stop_gates

Acceptance checks:

- template can generate a state JSON without external API。
- self-audit fields are required, not optional。

### P1.2 local-brain promotion rule

Create rule: review hypotheses can only promote to atom/project after evidence pointer exists。

Acceptance checks:

- `10-atoms/model-agreement-is-not-evidence.md` linked。
- new review note records promotion status。

## P2 — 自动化与治理

### P2.1 Second-order periodic audit

Add optional scheduled local report that checks whether multi-model reviews are being falsely promoted。

Acceptance checks:

- local-first script only。
- no automatic external model calls。
- alert only on concrete violations。

### P2.2 Skill integration

Patch relevant skills if future runs reveal missing steps。

Acceptance checks:

- skill patch records pitfall and verification commands。

## Execution order

P0.1 → P0.2 → P0.3 → P10 verification → P1 template if requested。
