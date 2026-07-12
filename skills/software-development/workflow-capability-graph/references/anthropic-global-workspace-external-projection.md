# Anthropic Global Workspace → external WorkspaceProjection pattern

Applicability:
- Use when absorbing interpretability / hidden-state / global-workspace research into agent workflow, taskpool, evidence-gate, or completion-claim design.
- Use for closed/API models only as an **external projection pattern**: explicit workspace state, evidence DAG, reflection readback, authority gates, and completion packets.

Anti-conditions:
- Do not claim hidden-state or real J-space access for closed/API models.
- Do not equate J-space with chain-of-thought.
- Do not treat model judgment, reflection text, or model consensus as objective evidence for completion-critical claims.
- Do not open taskpool lifecycle writes, external dispatch, publish/deploy, credential/payment entry, destructive operations, or broad fan-out from this pattern alone.

## Source facts to preserve

Primary source: Anthropic Research / Transformer Circuits, 2026, `Verbalizable Representations Form a Global Workspace in Language Models`.

Key facts:
- The paper introduces the Jacobian lens / J-lens, an interpretability method for finding internal activations positioned to influence what a model could verbalize later.
- The resulting J-space is a small set of token-linked, verbalizable internal representations. A token lighting up means the concept is salient/available, not necessarily that the model will output that token.
- Anthropic frames this as a functional/access-consciousness analogy, not a claim of phenomenal consciousness.
- Claimed workspace properties: verbal report, directed modulation, internal reasoning, flexible generalization/broadcast, and selectivity.
- Safety examples include silent detection of bugs, prompt-injection-like content, staged/evaluation contexts, and strategic concepts. Treat these as source claims requiring primary-source grounding.
- The companion repository is useful as reference implementation context, but should not be assumed production-maintained without a fresh repo/readme check.

## Engineering translation

For Hermes-style systems, translate hidden workspace ideas into explicit external artifacts:

```text
source facts / task goal
→ WorkspaceProjection
→ EvidenceDAG
→ ReflectionReadback
→ AuthorityGate
→ CompletionClaimPacket
→ SSOT/taskpool/readback evidence
```

Minimum packet fields:
- `source_boundary`: source refs, `hidden_state_access=false`, `model_judgment_is_objective_evidence=false`.
- `workspace_projection`: goal, non-goals, constraints, authority boundary, workspace state, missing evidence, next action contract.
- `evidence_dag`: claims, evidence, support links, evidence authority, verification status.
- `reflection_readback`: concise readback from external state only.
- `completion_claim_packet`: claim, scope, evidence refs, missing evidence, negative evidence, excluded claims, status.

## Gate checklist

Before allowing a completion claim:
- Completion-critical claims have objective or user-authorized verified evidence.
- Model-only evidence remains advisory.
- Negative evidence records what did **not** happen: no hidden-state access, no external dispatch, no lifecycle write, no secret/payment/destructive action unless explicitly authorized and read back.
- Excluded claims list what the packet does not prove.
- Dashboard/control-room summaries distinguish current-task effects from historical aggregate flags.

## Exact target / payload / rollback / readback gate

Before opening any write-through or high-risk boundary from this pattern, require a four-field packet:

| Field | Required meaning |
|---|---|
| `exact_target` | One concrete workspace/task/file/channel/repo/resource id. Broad classes like “deploy” or “send” are not targets. |
| `payload` | The minimal event/message/ref/content to write or send, plus an idempotency key when external. |
| `rollback` | The exact undo/restore/disable/correction path; for credentials/payments this is a human cancel/stop gate only. |
| `readback` | The command/file/API/platform receipt proving target, effect, and negative side effects. |

Current safe defaults:
- Taskpool bridge: one workspace id + one task id + deterministic `command:` evidence; read back task file, event ledger, closure packet, and `brain_task_orchestrator.py selfcheck --json`.
- Destructive smoke: generated disposable canary only; read back absence, restore from `.bak`, and hash equality; never touch production/user resources.
- Dashboard: use `dashboard-data --workspace-id <id>` and bind claims to `current_workspace_effects` instead of aggregate history.

Keep these closed until exact packets exist:
- external dispatch: platform + target + payload + receipt/readback + recall/correction path;
- publish/deploy/push: repo/remote/env/branch + artifact/ref + rollback command + remote/deploy readback;
- credential/payment: human gate only; the agent never types secrets/cards/OTP/API keys;
- broad fan-out: finite channel set + payload + per-channel rollback/readback;
- worker/runtime router: worker id/command/workspace/budget + kill/disable/readback path.

## Taskpool bridge pitfall

A read-only dashboard or workspace summary may aggregate historical workspaces. If it reports flags such as prior runtime mutation or taskpool write-through, do not treat those as new authorization or evidence for the current task. Record the current workspace id, current event refs, and negative evidence separately.

When building dashboard/control-room projections, expose both aggregate effects and current-workspace effects. The completion claim should bind to `current_workspace_effects` or equivalent, not to aggregate history. Add a regression test where a historical workspace has taskpool write-through but the selected current workspace does not, and require the selected current workspace to report no current write-through.

## Reusable validator pattern

A small deterministic validator is useful for this class of work. It should fail closed when:
- `hidden_state_access` is true for an external projection.
- model judgment is marked as objective evidence.
- dangerous authority is listed as allowed.
- a verified local completion claim has missing evidence.
- completion evidence refs do not exist in the evidence DAG.

Keep the validator local/read-only unless a later exact authority grant opens a bounded write path.
