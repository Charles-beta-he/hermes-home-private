# Module Pool and Synthesis Ratchet

Scope: workflow creation/governance systems where conversation seeds should become reusable workflow assets only when justified, and where workflows should be assembled from capability modules rather than hand-written as monoliths.

Anti-conditions:
- Do not create a module only because the user mentioned a scenario or used workflow vocabulary.
- Do not promote a high-frequency combination directly to canonical.
- Do not treat model consensus as evidence.
- Do not turn external side effects, taskpool/cron/AgentOS mutation, publish/deploy, destructive actions, credentials, or production writes into autonomous behavior without exact authority, rollback, and readback.

## Core model

A conversation produces a `WorkflowSeed`, not a permanent workflow. If the seed passes the assetization gate, compile it into capability needs, retrieve matching modules from the module pool, detect gaps, and assemble a workflow graph.

```text
conversation seed
-> assetization decision
-> capability need inference
-> module retrieval
-> gap detection
-> candidate module generation
-> workflow graph assembly
-> route/evidence dry-run
-> usage ledger
-> synthesis ratchet
-> promotion/demotion/cleanup
```

## CapabilityModule contract

```yaml
capability_module:
  id: string
  kind: atomic_module|composite_module|gate|adapter|presentation|verifier
  responsibility: string
  consumes: []
  produces: []
  applies_when: []
  does_not_apply_when: []
  positive_examples: []
  negative_examples: []
  neighbor_modules: []
  forbidden_triggers: []
  side_effects: none|local_write|external_write|lifecycle|publish|destructive
  required_authority: []
  maturity: seed|draft|candidate|validated|common|canonical|deprecated|archived|revoked
  metrics:
    usage_count: 0
    success_count: 0
    evidence_pass_rate: 0.0
    false_trigger_count: 0
    human_intervention_rate: 0.0
```

## Workflow graph compiler

The compiler should produce an intermediate representation before any durable write:

```yaml
intent_ir:
  seed: string
  inferred_goal: string
  ambiguity_level: low|medium|high
  reuse_signal: low|medium|high
  risk_surface: none|local|external|lifecycle|destructive
  evidence_need: low|medium|high
  capability_needs: []
  forbidden_actions: []
```

Then assemble a graph with nodes, edges, gates, output/presentation contracts, evidence requirements, and lifecycle policy.

## Frequency is a candidate signal, not proof

New modules should be synthesized only when frequency combines with quality signals:

```yaml
module_synthesis_gate:
  create_candidate_when:
    - same_module_combo_seen >= 3
    - same_output_contract_seen >= 2
    - human_intervention_reduced == true
    - no_external_side_effect_without_gate == true
  promote_to_validated_when:
    - successful_runs >= 2
    - evidence_pass_rate >= 0.8
    - negative_cases_pass == true
  promote_to_common_when:
    - reuse_count >= 5
    - false_trigger_count == 0
    - neighbor_collision_count == 0
  promote_to_canonical_when:
    - cross_project_reuse == true
    - regression_suite_exists == true
    - cleanup_policy_exists == true
    - rollback_or_supersession_path_exists == true
    - advisory_review_passed == true
```

## Auto-advance vs human gate

Auto-advance safe local/reversible/evidence-producing work:
- read existing context;
- create local candidate assets/modules;
- generate eval cases;
- run validators/dry-runs;
- write local evidence receipts;
- demote or quarantine weak candidates locally.

Ask the user only for real boundaries:
- exact authority for external/lifecycle/destructive/publish/production/credential/payment actions;
- durable preference conflict;
- global canonical behavior change;
- missing evidence after attempted retrieval.

## Local helper CLI

Path: `~/.hermes/scripts/workflow_module_pool.py`

Commands:

```bash
# Generate a module JSON draft.
python3 ~/.hermes/scripts/workflow_module_pool.py default-module \
  --id evidence_collector \
  --responsibility 'Collect objective evidence for workflow claims'

# Validate a module file.
python3 ~/.hermes/scripts/workflow_module_pool.py validate --module /path/to/module.json

# Register a validated module in the local registry.
python3 ~/.hermes/scripts/workflow_module_pool.py register \
  --module /path/to/module.json \
  --registry ~/.hermes/workflows/module-pool/module_registry.json

# Compile a seed into a local module graph plan.
python3 ~/.hermes/scripts/workflow_module_pool.py plan \
  --seed '以后给我外链就自动做事实、商业、风险分析，并保留证据和美化输出'

# Record usage evidence; this is local JSONL only and enables no side effects.
python3 ~/.hermes/scripts/workflow_module_pool.py record \
  --workflow-id wf-demo \
  --modules evidence_collector,business_analysis,presentation_builder \
  --evidence-passed

# Mine the usage ledger for candidate composite modules.
python3 ~/.hermes/scripts/workflow_module_pool.py synthesize
```

Fail-closed contract:
- registry and ledger writes are local files only;
- synthesis creates candidate JSON only;
- no external dispatch, taskpool lifecycle write, cron enablement, AgentOS mutation, memory write, publish/deploy/push, destructive action, payment, or credential entry.

## Engineering anchors

Use these as rationale when explaining or auditing the design:
- Control theory / cybernetics: closed-loop observe-orient-act-feedback systems.
- Deming PDCA/PDSA: plan-do-check-act lifecycle, not one-shot workflow docs.
- BPM / Workflow Patterns / Process Mining: workflows are state/control/resource/evidence systems.
- Compiler IR: natural-language seeds compile into IR before graph/backend generation.
- DevOps/DORA and SRE: small batches, fast feedback, reliability gates, rollback, fail-closed automation.
- Evolutionary Architecture: fitness functions govern promotion and prevent drift.
- DDD: module pools need bounded contexts and negative routing space.
- Enterprise Integration Patterns: routing, filtering, transformation, idempotency, message history.
- Knowledge management / double-loop learning: successful/failed experience modifies modules, gates, and assumptions.
- ReAct/Reflexion/SkillOpt-style agent learning: rollout -> reflection -> skill/module update -> eval gate.
