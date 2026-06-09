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

### Partial fit / remaining maturity gaps

1. Runtime profile routing is still concentrated in `brain-mirror`.
   - The architecture has specialist profiles, but live Kanban work is not broadly distributed among them.

2. Agent Cards were not previously machine-readable.
   - This session landed `/Users/charles/.hermes/docs/private/agent-cards-v1.json` as the first explicit, Google-style card layer.

3. Agent Card injection into worker prompts is not enabled.
   - The card file is documentation/validation only for now.
   - Runtime prompt injection and specialist routing are higher-blast-radius changes requiring explicit follow-up authorization.

4. Multimodel conductor is still an architecture domain, not the default runtime conductor.
   - Default-on conductor routing needs separate certification, model/profile regression tests, and rollback.

5. ToolSearch/SkillSearch and external skill intake remain governed review/block domains.
   - Safe read-only evaluation exists, but canonical skill writers/installers remain blocked behind review.

## Boundary reached

Safe scope completed:

- SSOT comparison document.
- Machine-readable Agent Cards for runtime profiles and architecture domains.
- Read-only validation script.
- Skill/runbook update.
- Coverage/classification verification.

Boundary requiring explicit next authorization:

- Rewire Kanban dispatch to specialist profiles instead of `brain-mirror` concentration.
- Inject Agent Cards into worker prompts at runtime.
- Make multimodel conductor default-on.
- Enable canonical external skill writers or installers.
- Add external side-effect executors.

## Current verdict

Hermes conforms to the Google agent structure at the control-plane architecture level, and now has explicit Agent Cards that map profiles/domains to Google-style components. It is stronger than a typical simple agent on governance/evidence/lifecycle, but not yet fully mature as a runtime multi-specialist agent system because execution remains concentrated in `brain-mirror` and Agent Cards are not yet active runtime contracts.
