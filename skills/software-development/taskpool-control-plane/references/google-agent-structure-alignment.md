# Google Agent Structure Alignment for Hermes

Use this reference when a user asks whether Hermes's current agents/profile/domain layout matches Google-style AI agent architecture.

## Authoritative Google-style structure to compare against

Google Cloud's public AI agent explanation and the Google/Kaggle Agents whitepaper frame an agent as more than a standalone LLM. The recurring structural elements are:

- **Model / reasoner**: performs reasoning, planning, decision making, and response generation.
- **Tools / actions**: external APIs, databases, search, file systems, execution tools, senders, or other systems the model can use to observe or act.
- **Orchestration / cognitive loop**: observe → reason/plan → act → evaluate/iterate.
- **Memory / context**: task state, retrieved knowledge, user/task history, and environment context.
- **Role / instruction / policy**: the agent's role, communication style, available tools, action scope, and constraints.
- **Multi-agent collaboration**: agents can cooperate, coordinate, and split complex workflows.
- **Governance / safety**: permission boundaries, auditing, escalation, human review, and safe failure modes.

Do not treat a plain chatbot or single prompt as a complete agent unless it has at least tool/action access and a goal-directed orchestration loop.

## Hermes mapping

Hermes should be explained in two layers:

1. **Execution profile layer**
   - Examples: `brain-mirror`, `dev`, `hermes-agent`, `hermes-core`, `media`, `mlops`, `workflow`, `default`.
   - These are spawnable worker/profile seats. They may have distinct config, skills, model routing, and tool context.
   - A profile being on disk does not mean it is actively carrying work. Always check `hermes kanban assignees --json` for live use.

2. **Architecture/domain layer**
   - Examples observed in Hermes self-architecture work:
     - `control_plane_local_brain`: memory/context/retrieval/evidence/source-of-truth.
     - `control_plane_taskpool`: orchestration, lifecycle, dispatch, Kanban projection, ToolSearch/SkillSearch, candidate intake.
     - `skill_graph_governance`: tool/capability registry, skill distillation, compatibility scoring, promotion gates.
     - `visual_ingest_runtime`: multimodal observation/input pipeline.
     - `multimodel_conductor_architecture`: multi-agent/multi-model roles, model capability profiles, generate/evaluate/refine loops.

## Fit assessment pattern

When comparing Hermes to Google's agent architecture, report:

- **Strong fit**:
  - taskpool/Kanban lifecycle gives explicit orchestration;
  - tools/scripts/MCP/browser/terminal/skills give action surfaces;
  - local-brain/provenance/evidence give memory/context;
  - permission tiers, completion gates, truth gates, proof/selfcheck give strong governance.
- **Partial fit / improvement areas**:
  - live execution may be concentrated in `brain-mirror` while specialist profiles are only available seats;
  - per-profile **Agent Cards** may not be explicit enough;
  - model capability profiles and role-specific prompting may still be evolving rather than default runtime;
  - tool/skill discovery and delayed loading may still be under taskpool review.

## Recommended Agent Card fields

If the user asks how to make Hermes more Google-agent-aligned, propose class-level Agent Cards per profile/domain with:

- `agent_id`
- `role`
- `responsibilities`
- `model_profile` / routing policy
- `tools_allowed`
- `memory_scope`
- `action_scope`
- `permission_tier`
- `escalation_policy`
- `completion_gate`
- `evaluation_criteria`
- `handoff_contract`

This turns implicit profile/domain metadata into the explicit role + tools + policy form Google describes.

## Pitfalls

- Do not conflate **profile** with **domain**: a profile is an execution seat; a domain is an architecture capability area.
- Do not claim every on-disk profile is an active agent. Use live assignee/task counts.
- Do not judge Google alignment only by LLM prompts. Check tools, memory, orchestration, and governance.
- Do not force task lifecycle changes just to improve alignment or coverage; classify from existing evidence first.
