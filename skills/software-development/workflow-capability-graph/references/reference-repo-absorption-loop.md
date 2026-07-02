# Reference Repo Absorption Loop

Scope: absorbing public-media or open-source agent/workflow/tool projects into Hermes as reusable capability, not as unverified hype. Applicability: external agent harnesses, memory runtimes, skill/tool catalogs, MCP/A2A systems, workflow automation frameworks, and similar projects. Anti-condition: if the user only asks for a quick summary, keep output lightweight; if the user asks to install/run, use an isolated exact-target benchmark gate first.

## Source pattern

Derived from the Raven/EverOS absorption pack:

- SSOT: `/Users/charles/wechat_video_analysis/project_absorption/raven-everos-absorption-ssot/`
- Evidence: `evidence/source-evidence.json`
- Graph: `graph/raven-everos-capability-graph.json`
- Experience atom: `raven-everos-absorption-76b1d0cec9ea`

## Loop

Do not stop at a chat report when the user authorizes absorption. Run this closed loop to the next safe boundary:

1. **Source identity gate**
   - Resolve canonical repo/site/package.
   - Pin URL, owner, default branch, HEAD/commit, license, README/docs paths, and relevant file/line evidence.
   - Separate media claims from repo/docs facts.

2. **Claim map**
   - List each transferable claim as: `claim`, `evidence_refs`, `unverified_parts`, `risk`, `source_boundary`.
   - Convert marketing phrases into verification requirements.

3. **Capability graph**
   - Create CapabilityNodes for reusable modules, gates, adapters, artifact templates, and agent wrappers.
   - For agent-harness/self-improving-agent references, start from these required node classes unless source evidence disproves them: `source_reference_intake`, `memory_ownership_model`, `skill_evolution_ratchet`, `agent_template_profile`, `doctor_onboard_readiness`, `sentinel_nudge_governance`, and `edge_harness_boundary`.
   - Add AgentWrappers such as `reference_reviewer`, `capability_graph_designer`, and a future gated `runtime_executor` only when the authority boundary is explicit.
   - Every agent wrapper must declare `wraps`, `policy`, `authority`, `produces`, and `cannot_do`.
   - Every gate must expose pass/warn/fail/blocked outcomes.

4. **Landing-zone audit**
   - Apply Memory Ownership Gate when the result might become memory, skill, profile, project doc, taskpool, or experience-ratchet proposal.
   - Keep project-specific evidence in SSOT/project docs, not global memory.

5. **Proposal atoms**
   - For reusable cross-project lessons, create experience-ratchet atoms with applicability, anti-condition, falsifier, and evidence.
   - Promote at most to `promoted_candidate` unless there is independent review/verification for the target landing zone.

6. **Owned next slice**
   - If a safe local prototype/checker/schema/reference patch is available, continue to land it.
   - If the next step crosses install, external dispatch, credentials, publish/deploy, destructive action, or live runtime authority, produce an exact authorization packet with target, rollback, receipt, and readback.

## Checker

Use `scripts/check_reference_absorption_pack.py <ssot-root>` to validate the local pack shape: required files, source evidence identity, capability nodes, agent wrappers, gate outcomes, proposal manifest, authority boundary, and final report not-done terms. Regression tests live at `scripts/test_check_reference_absorption_pack.py`.

## Do-not-do

- Do not install or run upstream projects merely because a video/repo claims value.
- Do not bulk-import external skills, hooks, prompts, memory, or gateway defaults.
- Do not treat model consensus or star counts as evidence.
- Do not convert project facts into global memories.
- Do not use “needs human review” as a blanket stop; continue SSOT/proposal/schema/reference work until the next real authority boundary.

## Verification checklist

- [ ] Source repo/site/package identity pinned.
- [ ] File/line evidence extracted for every accepted claim.
- [ ] Capability graph has nodes, wrappers, gates, side-effect classes, closure states.
- [ ] Landing zones classified and WIP excluded from memory.
- [ ] Proposal atoms validate or skill/reference patches read back.
- [ ] Remaining blocked actions name exact missing authority/evidence, not vague caution.
