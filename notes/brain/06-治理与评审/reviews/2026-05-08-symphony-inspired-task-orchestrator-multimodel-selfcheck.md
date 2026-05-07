---
type: review
layer: L6
status: active
created: 2026-05-08T00:06:02+08:00
concepts: [multi-model-selfcheck, symphony-inspired, evidence-boundary]
---

# 2026-05-08 Symphony-inspired Task Orchestrator Multi-model Selfcheck

## Scope

Question: OpenAI Symphony 对本地大脑待完成任务规划是否有帮助，以及如何以长期可维护方式落地。

## Model Provenance

A four-model `consult_models.py run --tier T3 --quorum 4 --discussion` attempt was executed before landing.

- Fan-out: 4/4 planners produced seed plans: Claude Opus, gpt-5.5, DeepSeek, MiMo.
- Discussion/ratification: timed out / no certified `discussion_result.json` available at that time.
- Merged status: `truth_not_certified` because evidence bundle grounding did not link claims into truth gate, even though local tools had read source files.
- Therefore: seed plans are provenance and challenge material, not full certification.

## Agreement Summary

| Point | Status | Landing Response |
|---|---|---|
| Do not adopt Symphony runtime wholesale | agreed | Reject Linear/Codex/Elixir runtime adoption |
| Markdown remains canonical | agreed | Explicit invariant in P10 and atom |
| Claim/retry/reconciliation are useful | agreed | Landed in playbook/templates |
| Need deterministic evidence | agreed | Added self-check script and brainctl verification loop |
| Need safety caveat for hooks | agreed | Hooks inert unless allowlisted |

## Issue Ledger

| ID | Severity | Issue | Resolution |
|---|---:|---|---|
| I-001 | 5 | Second source of truth if Linear/Symphony becomes canonical | Resolved: external queues are derived; Markdown canonical |
| I-002 | 4 | Multi-model fanout is not ratification | Resolved: this review marks prior fanout as provenance-only |
| I-003 | 5 | Arbitrary hooks can damage vault | Resolved: workflow hooks are descriptive/inert unless allowlisted |
| I-004 | 3 | Dashboard could drift and be treated as truth | Resolved: dashboard declares derived/not source of truth |
| I-005 | 3 | Chinese/English search can miss artifacts | Resolved: bilingual aliases and representative search required |

## Current Selfcheck Status

Final loop status: `certified_with_runtime_adapter_caveat` for P0 landing.

Deterministic gates:

- [x] `python3 ~/.hermes/scripts/symphony_task_orchestrator_selfcheck.py --json` -> PASS, 12 required files, `failures=[]`, `warnings=[]`.
- [x] `python3 ~/.hermes/scripts/brainctl.py --json sync` -> exit 0.
- [x] `python3 ~/.hermes/scripts/brainctl.py --json reindex` -> `indexed_blocks=2087`.
- [x] `brainctl search "Symphony-inspired 本地任务编排"` -> found playbook/project/review entries.
- [x] `brainctl search "claim_expires_at risk register"` -> found P10 risk register and lease fields.
- [x] `python3 ~/.hermes/scripts/local_brain_exhaustive_audit.py --sample-limit 5` -> `stop_gate_pass=true`, empty dirs=0, broken wikilinks=0, secret pattern hits=0.
- [x] post-landing multi-model selfcheck after artifacts exist.

## Post-landing Multi-model Certification

Primary grounded run:

- State: `/tmp/symphony-task-orchestrator-grounded-state.json`.
- Tick: `/Users/charles/.hermes/tick-20260507-162228/`.
- Truth gate: `grounded`, `can_certify_truth=true`, `verified_claim_count=5/5`, `evidence_coverage=1.0`.
- Issue ledger: `[]`.
- Agreement matrix: framing=0.95, approach=0.95, implementation_order=0.95.

Ratification votes:

| Model | Vote | best_within_constraints | Notes |
|---|---|---:|---|
| Claude Code Opus | approve | true | Direct Claude Code CLI ratification, no unresolved severity>=3 blocker |
| gpt-5.5 | approve | true | No unresolved round-delta issues; truth gate grounded |
| DeepSeek v4 Pro | approve | true | 5/5 claims verified; no novel severity>=3 blocker |
| MiMo v2.5 Pro | approve | true | 100% evidence coverage; no amendments needed |

Adapter caveat:

- `consult_models.py` Hermes Anthropic adapter produced `session_id` / API-routing failures for `claude-opus-4-7`, so its native manifest remains `not_certified` for adapter reasons.
- The Claude signature was fulfilled through Claude Code CLI direct ratification against the same grounded state, with `Read`-only access to `/tmp`.
- Therefore the loop gate is treated as passed for the P0 landing package, while the Hermes Anthropic adapter issue remains a separate infrastructure caveat, not a blocker to the local-brain plan.

## Evidence Boundary

This review certifies only the local P0 landing package. It does not certify OpenAI Symphony itself, does not import Symphony runtime, does not make Linear canonical, and does not authorize arbitrary workflow hooks. P1/P2/P3 implementation remains future backlog and must pass separate claim/mutator/runner gates before write-capable automation.
