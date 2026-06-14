# Modular Agent Builder Workflow Kernel

Use this reference when designing or extending a self-advancing business Agent / personal-assistant builder where workflows are described in natural language, compiled into taskpool-executable DAGs, routed across models, and delivered as enterprise-grade Agent Packs.

## Core thesis

The stable unit is not a prompt or a standalone agent. The stable unit is a governed workflow kernel:

```text
Intent → WorkflowSpec → ExecutionDAG → RunLockfile → Taskpool → ModuleRuntime → ModelRouter → Evidence → Acceptance → ReleaseArtifact
```

Principle: let intelligence happen inside modules and routing; let stability happen in the control plane, versioning, evidence, and acceptance gates.

## Canonical components

- **Module Registry**: versioned capability modules with typed inputs/outputs, side-effect class, permissions, model profile, evidence requirements, compatibility notes, and lifecycle state.
- **Workflow Compiler**: converts natural-language workflow edits into semantic diffs, static checks, dry-runs, risk classification, and a new WorkflowSpec version.
- **Taskpool Runtime**: owns lifecycle state, dependency order, claim/lease, retries, blockers, human gates, and evidence attachment. Workers/modules do not mark `done` directly.
- **Model Router**: chooses model/provider by module, task type, abstraction layer, risk, data sensitivity, context length, tool/structured-output needs, latency/cost budget, tenant policy, provider health, and eval score.
- **Acceptance Compiler**: derives run-specific acceptance criteria from project context, abstraction layer, workflow goal, module contract, risk, and historical failure modes; freezes them before execution.
- **Evidence Ledger**: binds each acceptance criterion to proof artifacts: tests, diffs, screenshots, API readbacks, logs, UAT records, or customer approvals.
- **Policy/Human Gate**: controls permissions, external side effects, destructive actions, secrets, production writes, business commitments, and value judgments.
- **Projection UI**: dashboard/control tower is projection and operator cockpit only; it is never a fact source.

## Module contract shape

Every hot-pluggable module should declare at minimum:

```yaml
module_id: resume_parser
version: 1.3.0
capability: parse_resume
abstraction_layer: implementation
input_schema: [resume_file, jd_criteria]
output_schema: [candidate_profile_json, evidence_quotes]
side_effects: local-read   # pure | local-read | local-write | external-read | external-write | destructive
permissions_required: [read_file]
model_profile:
  preferred: [best.resume_parse.structured]
  fallback: [local_parser, cheap_extraction_model]
evidence_required: [original_resume_ref, quote_match]
risk_level: medium
human_gate: [low_confidence, sensitive_inference]
compatibility:
  input: backward-compatible
  output: backward-compatible
  state: migratable
```

Natural language can appear in summaries, but module status, outputs, and evidence refs must be machine-readable.

## Run lockfile invariant

Each workflow run must freeze the effective execution envelope:

```yaml
run_id: wf_run_123
workflow_spec_version: 1.4.0
modules:
  planner: planner@2.1.0
  verifier: verifier@1.8.4
model_routing_policy: routing@5
acceptance_policy: acceptance@9
project_profile: customer_profile@2.0.0
context_digest: sha256:...
started_at: ...
```

This gives reproducibility, replay, audit, rollback, and root-cause analysis. Enterprise production runs default to pinned semantics; dynamic routing is allowed only at declared safe boundaries.

## Hot-plug lifecycle

Hot-plugging is controlled cutover, not arbitrary runtime replacement:

```text
registered → validated → shadow → canary → active → deprecated → retired
```

On module/model update:

```text
update → compatibility report → impact graph → affected workflow list → shadow/eval replay → policy decision → new runs use new version → eligible active runs upgrade at safe boundary → incompatible/high-risk runs remain pinned
```

## Route modes

- `pinned_run`: run starts with fixed module/model/acceptance set; safest for enterprise production, UAT, external side effects.
- `module_dynamic`: re-resolve at step/module boundaries; useful for long-running self-advancement.
- `turn_dynamic`: re-resolve each LLM turn; only for low-risk chat/read-only work.
- `shadow_only`: evaluate new module/model alongside production without affecting result.

## Acceptance by abstraction layer

- **Strategy**: goal clarity, constraints, viable paths, risk/rollback, evidence plan.
- **Architecture**: invariants, state-source ownership, module boundaries, compatibility, failure modes.
- **Implementation**: tests, typecheck/lint, scoped diff, API/schema contracts.
- **Runtime**: real execution, logs, readback, recoverability, rollback proof.
- **Enterprise delivery**: UAT, audit chain, permission matrix, SLO/SLA, security, cost, release/rollback package.

Acceptance can be context-sensitive, but must be frozen before execution. Never let the agent/module change `done` criteria after seeing its own output.

## Enterprise delivery path

Package mature workflows as Agent Packs:

```text
Agent Pack Studio → Delivery Cockpit → Pack/Module Registry → Evaluation & Certification Center → Runtime Control Plane → Observability & Audit → Enterprise Admin
```

Each Pack should include manifest, workflow spec, tool permissions, model policy, UAT/golden cases, evidence schema, docs, deployment/runbook, rollback path, and version lock.

## Pitfalls

- Updating a module and instantly mutating all running workflows without compatibility and impact analysis.
- Treating a natural-language workflow edit as production logic instead of compiling to a versioned spec.
- Letting modules carry persistent state or canonical lifecycle authority.
- Dynamic model routing without route trace, eval score, fallback chain, privacy/cost filters, and rollback alias.
- Runtime acceptance criteria drift: executing first, then redefining what counts as success.
- Dashboard/control UI becoming a second fact source.
- Packaging enterprise delivery around “an agent builder” instead of evidence-backed Agent Packs with UAT, audit, rollback, and version locks.
