# Sakana-inspired conductor pattern for Hermes

Use this reference when the user asks to absorb Sakana AI / "AI conductor" / multi-model conductor ideas into Hermes.

## Evidence boundary

Fresh official-source checks in May 2026 found that Sakana AI now does use `Conductor` as official research terminology, and has announced a productized multi-agent orchestration system:

- `Sakana Fugu: A Multi-Agent Orchestration System as a Foundation Model` — `https://sakana.ai/fugu-beta/`; describes Sakana Fugu as a commercial beta product coordinating pools of frontier foundation models, based on Trinity and Conductor research.
- `Learning to Orchestrate Agents in Natural Language with the Conductor` — `https://sakana.ai/learning-to-orchestrate/`; describes training a 7B Conductor model with RL to write effective custom instructions/workflows for a pool of other models.
- `Trinity: An Evolved LLM Coordinator` — `https://sakana.ai/trinity/`; describes an evolved coordinator for orchestrating specialized AIs.

Older Sakana evidence remains useful for the broader pattern:

- Nature-inspired AI, evolution, and collective intelligence: `https://sakana.ai/evolutionary-model-merge/`
- Multi-model knowledge composition / Evolutionary Model Merge: `https://sakana.ai/evolutionary-model-merge/`
- AI Scientist as a comprehensive automated scientific-discovery workflow: `https://sakana.ai/ai-scientist/`
- Agentic CUDA workflow using sequential generation, evolutionary meta-generation, robust evaluation, and LLM-based verifiers: `https://sakana.ai/ai-cuda-engineer/`
- Self-adaptive LLMs / Transformer²: `https://sakana.ai/transformer-squared/`

Safe wording: "Sakana Conductor/Fugu-inspired conductor pattern". Still avoid implying that Hermes has access to Sakana's proprietary Fugu/Conductor weights or product unless explicitly configured and verified.

## Absorbable pattern

The useful class-level pattern is not adding another model. It is upgrading multi-model orchestration from static fan-out to a conductor layer:

1. Model capability profiles: strengths, weaknesses, preferred roles, prompt style, cost tier.
2. Role assignment: scout / planner / implementer / critic / verifier / arbiter.
3. Generate → evaluate → select/refine loop.
4. Verifier-first evidence gates: multi-model agreement is not truth verification.
5. Outcome traces before learning: record role assignment/profile version/instruction hash/evidence result before automatically changing profiles.

## Hermes-native implementation shape

Prefer extending existing Hermes surfaces; do not introduce a second runtime stack.

Relevant surfaces:

- `~/.hermes/config/quorum.yaml` — current tier/quorum/planner lists; add optional `conductor.enabled: false` and `role_plan` here.
- `~/.hermes/config/model_profiles.yaml` — proposed profile store, schema like `hermes_model_profiles_v1`.
- `~/Code/personal-hermes-brain/hermes/scripts/consult_models.py` — `build_planner_prompt(...)`, planner selection, consensus, truth/evidence bundle handling.
- `~/.hermes/hermes-agent/agent/task_router.py` — fail-soft hints pattern; keep default routing unchanged unless explicitly enabled.
- `~/.hermes/scripts/post-update-check.py` — add conductor regression once implemented so local hardening survives updates.

Default-off config sketch:

```yaml
conductor:
  enabled: false
  profile_file: ~/.hermes/config/model_profiles.yaml
  role_plan:
    T1:
      scout: [mimo-v2.5-pro]
      implementer: [gpt-5.5]
      critic: [deepseek-v4-pro]
      arbiter: null
    T2:
      architect: [claude-opus-4-7]
      implementer: [gpt-5.5]
      critic: [deepseek-v4-pro]
      scout: [mimo-v2.5-pro]
      arbiter: claude-opus-4-7
```

Model profile sketch:

```yaml
schema: hermes_model_profiles_v1
models:
  gpt-5.5:
    strengths: [codegen, refactor, implementation_planning]
    weaknesses: [may_overfit_to_patch_path]
    preferred_roles: [implementer, planner]
    prompt_style: direct_constraints_json_first
    cost_tier: high
  claude-opus-4-7:
    strengths: [architecture, arbitration, risk_review]
    weaknesses: [expensive, may_be_verbose]
    preferred_roles: [architect, arbiter, critic]
    prompt_style: principled_tradeoff_evidence_first
    cost_tier: premium
  deepseek-v4-pro:
    strengths: [code_review, contradiction_detection, low_cost_reasoning]
    weaknesses: [may_need_strict_schema]
    preferred_roles: [critic, verifier]
    prompt_style: strict_schema_find_bugs
    cost_tier: medium
  mimo-v2.5-pro:
    strengths: [cheap_triage, broad_first_pass]
    weaknesses: [lower_confidence_on_architecture]
    preferred_roles: [triager, scout]
    prompt_style: short_decision_with_uncertainty
    cost_tier: low
```

## Prompting rules

When adding model-specific instructions:

- Call them `model_specific_instruction` or `capability_profile`, not "PUA".
- Keep them short, ideally 3–6 lines, to avoid prompt/cache bloat.
- Treat them as advisory. They must not override system/developer instructions, evidence gates, or truth gates.
- Make model-specific instructions role-focused and failure-mode-focused, e.g. critic/verifier should prioritize contradictions, missing evidence, rollback risk, and unsupported claims.

## Implementation status (2026-05-18)

The conductor pattern has been implemented and ENABLED in Hermes (no longer default-off):

- `~/.hermes/hermes-agent/agent/conductor_runtime.py` — TaskLedger, ConversationIntentRouter, FuguAdapter, MultiModelConductor, load_model_profiles
- `~/.hermes/config/model_profiles.yaml` — role profiles for default_main, GPT, Claude, DeepSeek, MiMo, Fugu; conductor.enabled=true
- `~/.hermes/scripts/hermes_conductor_runtime.py` — CLI smoke helper (config/route/create-task/fugu-probe/role-plan)
- `~/.hermes/scripts/hermes_background_task_worker.py` — durable background task worker (probe/run)
- `agent/conversation_loop.py` — `_run_conductor_intent_router()` wired after cognitive pipeline; actively manages TaskLedger (create tasks, update directives, read status)
- `~/Code/personal-hermes-brain/hermes/scripts/consult_models.py` — `build_conductor_enhanced_prompt()` and `generate_conductor_trace_for_consult()` for role-based planner prompt augmentation
- `tests/agent/test_conductor_runtime.py` — 9 tests covering ledger, router, conductor, worker, isolation
- `post-update-check.py` — `conductor_runtime_productization_regression` gate (conductor=enabled, fugu=fail-soft, role-plan=enabled)
- Config switches enabled: `conductor.enabled=true`, `conductor.intent_router.enabled=true`, `openclaw_control_plane.activation_hints=true`, `openclaw_control_plane.scoped_policy_context=true`, `tool_loop_guardrails.hard_stop_enabled=true`, `verification.adversarial.enabled=true`

Fugu adapter remains disabled (beta API not yet available).

For detailed implementation patterns, see `references/hermes-conductor-runtime-scaffold.md`.

## Acceptance bar

A complete implementation should prove:

- Default behavior unchanged with `conductor.enabled: false`.
- Profile schema validates and unknown/invalid role fields fail closed in validators.
- Planner prompts include deterministic short model-specific instructions only when enabled.
- `conductor_trace` records role assignments, profile version/hash, instruction hashes, and evidence-gate result.
- `truth_gate` / `evidence_bundle` remains the authority; consensus alone cannot certify truth.
- Verification includes py_compile, relevant consult_models tests/selfcheck, and post-update-check coverage once productized.
