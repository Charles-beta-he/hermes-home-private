# Hermes Agent Architecture vs Google Agent Structure

Date: 2026-06-09
SSOT: /Users/charles/.hermes/docs/private/agent-cards-v1.json

## Evidence basis

Google Cloud describes AI agents as AI systems that achieve goals and perform tasks for users with reasoning, planning, memory, autonomy, learning/adaptation, observation, action, collaboration, and tool use.

Kaggle/Google Agents whitepaper introduction frames an agent as a program that extends beyond a standalone Generative AI model by connecting reasoning/logic with access to external information and tools, enabling self-directed planning and execution.

For Hermes, the structural checklist is:

1. goal
2. role
3. observation
4. memory
5. planning
6. tools
7. actions
8. policy
9. evaluation
10. collaboration
11. escalation

Hermes also adds evidence/proof/lifecycle governance as a first-class requirement.

## Current runtime profiles

Profiles present under `~/.hermes/profiles/`:

- brain-mirror
- dev
- hermes-agent
- hermes-core
- media
- mlops
- personal
- work
- workflow

Kanban-spawnable assignees currently reported by `hermes kanban assignees --json`:

- brain-mirror
- default
- dev
- hermes-agent
- hermes-core
- media
- mlops
- workflow

Current workload concentration:

- `brain-mirror` carries the active Kanban projection lane: 4 blocked, 115 done.
- Other spawnable profiles are available but idle.
- `personal` and `work` exist as profile directories but are not current Kanban assignees.

## Current architecture domains

Active self-architecture task domains:

- control_plane_local_brain: 5
- control_plane_taskpool: 5
- skill_graph_governance: 2
- visual_ingest_runtime: 1
- multimodel_conductor_architecture: 1

The active set is fully classified:

- active brain tasks: 14
- missing canonical classification fields: 0
- iceberg_tier: L for all 14, meaning system/control-plane/runtime depth for Hermes self-architecture tasks.

## Fit against Google's agent structure

### Strong fit

- Goal/role: task objective, mission envelope, profile/domain card.
- Observation: brain notes, Kanban DB, task runs, visual inputs, source reports, model/router evidence.
- Memory/context: local brain markdown, evidence refs, run ledger, task events, skill graph.
- Planning: taskpool lifecycle, dependency order, acceptance criteria, conductor plans.
- Tools/actions: Hermes toolsets, scripts, MCP/tools, Kanban worker actions, validation scripts.
- Collaboration: profiles, taskpool, multimodel fanout, human review gates.
- Evaluation: selfcheck, proof-check, v_state, kanban_coverage_v2, tests.
- Governance: permission_tier, completion_gate, truth_gate, no fake proof, review-required boundaries.

### Current runtime maturity after follow-through

1. Runtime profile routing is default-on.
   - Specialist profile routing now defaults to `apply` and can be rolled back with `HERMES_AGENT_CARD_ROUTING_MODE=shadow|off`.

2. Agent Cards are machine-readable and injected into worker prompts by default.
   - `/Users/charles/.hermes/docs/private/agent-cards-v1.json` is the explicit Google-style card layer.
   - Worker prompt context can be disabled with `HERMES_ENABLE_AGENT_CARD_CONTEXT=off`.

3. Multimodel conductor is default-on for validated worker proofs.
   - Conductor certification defaults to `apply` and can be disabled with `HERMES_MULTIMODEL_CONDUCTOR_MODE=off`.

4. Digest-bound local write-through is enabled for narrow targets.
   - lifecycle: certified `review -> done` only;
   - adapters: `local_file`, `taskpool_note`, `kanban_db` closeout only;
   - skills: create-new-skill only;
   - capabilities: lease validation for dangerous capabilities such as `run_command`.

5. Remaining maturity gaps are now deliberately higher-risk boundaries.
   - broad lifecycle transitions;
   - non-local external sends/deploys;
   - existing-skill edit/delete;
   - memory/cron/provider writes;
   - full Control Tower dashboard/replay integration for every harness event.

## Boundary reached

Safe scope completed and then advanced:

- SSOT comparison document.
- Machine-readable Agent Cards for runtime profiles and architecture domains.
- Read-only validation script.
- Default-on specialist routing and worker Agent Card context.
- Default-on multimodel conductor certification.
- Digest-bound local write-through for narrow lifecycle/adapter/skill/capability surfaces.
- Skill/runbook update.
- Coverage/classification verification.

Still requiring separate target-specific authorization/design:

- Broad lifecycle transitions beyond certified `review -> done`.
- Non-local external sends/deploys.
- Existing-skill edit/delete.
- Memory/cron/provider writes.
- Full Control Tower dashboard/replay integration for every harness event.

## Current verdict

Hermes conforms to the Google agent structure at the control-plane architecture level and now has active Agent Cards that map profiles/domains to Google-style components. It is stronger than a typical simple agent on governance/evidence/lifecycle, with runtime multi-specialist routing and bounded digest/readback write-through. Remaining maturity gaps are deliberately higher-risk external or broad-mutation capabilities rather than missing core agent structure.
