# SkillClaw intake / gap analysis (2026-06-10)

## Source identity

- Repo: https://github.com/AMAP-ML/SkillClaw
- Live metadata via `gh repo view AMAP-ML/SkillClaw`: stars 1833, forks 176, default branch `main`, MIT license, not archived, pushed 2026-06-02, updated 2026-06-10.
- Inspected local clone: `/Users/charles/.hermes/runs/skillclaw-intake-2026-06-10`
- Inspected commit: `bf4dc2ee9430ecffb60e19630d26f57dfa2bd326`
- User framing: “分析添加任务池：SkillClaw项目的GitHub地址：github.com/AMAP-ML/SkillClaw”

## Evidence inspected

- `README.md`: positions SkillClaw as collective skill evolution for AI agents; explicitly supports Hermes/OpenClaw/Codex/Claude Code and other claw agents.
- `README.md` lines 140-150: architecture has Client Proxy plus optional Evolve Server; shared storage can be Alibaba OSS / S3 / local filesystem; skill format is `SKILL.md`.
- `README.md` lines 235-260: Hermes integration rewrites `~/.hermes/config.yaml` to point Hermes at SkillClaw local proxy; `skillclaw doctor hermes` and `skillclaw restore hermes` exist.
- `README.md` lines 302-327: optional validation worker stages candidate skills before publication.
- `README.md` lines 369-460: evolve server supports workflow engine and OpenClaw-driven agent engine.
- `pyproject.toml`: Python >=3.10, CLI entrypoints `skillclaw` and `skillclaw-evolve-server`, optional extras `embedding`, `evolve`, `sharing`, `server`, `all`.
- `skillclaw/skill_manager.py`: AgentSkills/OpenClaw-compatible `SKILL.md` parser, preserves extra frontmatter, supports template and embedding retrieval.
- `skillclaw/claw_adapter.py`: modifies configs for openclaw/hermes/codex/claude/qwenpaw/ironclaw/etc.; this is a high-authority side-effect surface.
- `evolve_server/pipeline/summarizer.py`: builds compact session trajectories and metadata such as `_skills_referenced`, `_avg_prm`, tool errors.
- `evolve_server/pipeline/aggregation.py`: groups sessions by referenced skill or no-skill.
- `evolve_server/pipeline/skill_verifier.py`: LLM verifier gate for candidate skills before shared publication.
- `evolve_server/engines/EVOLVE_AGENTS.md`: agent engine workspace boundary; sessions and skills copied into a workspace and skill changes are self-validated before finalizing.
- Tests observed under `tests/`: dashboard, Nacos hub/versioning, skill bundle support, Hermes/Codex/Claude-style API integrations, validation worker, session upload trigger.

## Capability mapping to Hermes

### High-value transferable patterns

1. **Post-task skill evolution loop**
   - SkillClaw separates task-time agent execution from post-task evolution.
   - Hermes already has skills + memory + taskpool; the useful delta is a governed post-session “experience → candidate skill patch → validation → publish” pipeline.

2. **Session compression for skill learning**
   - SkillClaw stores compact trajectories, skill references, tool outcomes, PRM/ORM signals.
   - Hermes can map this to existing session_search / tool-call transcripts / taskpool proof logs without routing all model traffic through an external proxy.

3. **Skill candidate publication gate**
   - SkillClaw’s verifier checks grounding, preservation of existing value, specificity/reusability, and safe publication.
   - This aligns with Hermes skill_manage policy and user preference: patch existing umbrellas first; no generic slop; evidence-backed skill updates.

4. **Validation worker / staged publish mode**
   - Candidate skills can be staged for review before entering shared skill store.
   - Hermes should absorb the staged gate pattern, not auto-merge generated skill changes.

5. **Multi-agent / multi-device skill sharing model**
   - SkillClaw’s shared storage / group model is relevant to Hermes profiles and possible future skill federation.
   - Initial Hermes task should keep this as architecture mapping, not enable OSS/S3/Nacos or modify profiles.

### Hermes landing zones

- `skill-graph`: primary target. SkillClaw directly concerns skill lifecycle, deduplication, trigger quality, sharing, verification, and publication gates.
- `local-brain`: secondary. Session trajectory compression and taskpool proof logs can feed skill candidate generation.
- `provider-quota`: tertiary only. PRM/LLM verification costs need budget gates, but this is not the core intake target.

## Risks / red lines

- Do not run `skillclaw setup`, `skillclaw start`, or any adapter that rewrites `~/.hermes/config.yaml` during intake.
- Do not route Hermes traffic through SkillClaw proxy without explicit user approval and rollback plan.
- Do not upload local Hermes skills/session/taskpool data to OSS/S3/Nacos/cloud services during intake.
- Do not treat shared SkillClaw outputs as trusted skills without Hermes-native validation.
- Do not create a parallel skill SSOT. Hermes skill store remains canonical; SkillClaw patterns may inform staged candidate workflow.
- Do not import third-party skill bundles or execute OpenClaw agent engine in this phase.

## Recommended taskpool task

Title: `评估 SkillClaw 集体技能进化架构并映射到 Hermes skill-graph 棘轮`

- lane: `evolution`
- priority: `P2`
- project: `hermes-agent`
- architecture_target: `skill-graph`
- capability_delta: introduce evidence-backed post-session skill evolution loop, candidate staging, validation gates, dedup/trigger optimization patterns, and multi-profile skill sharing map.
- anti_drift_check: source evidence must come from inspected SkillClaw repo/commit; no install/config rewrite/cloud upload; Hermes skill store stays SSOT; patch existing Hermes skills before creating new ones.
- acceptance_evidence: this gap doc, source inventory, mechanism-to-Hermes mapping, security/privacy gate, smallest verifiable local prototype proposal, proof-check/selfcheck.
- dependency_order: source-review -> security/privacy boundary -> gap mapping -> minimal Hermes-native candidate workflow design -> optional prototype task.
- parallel_boundary: no third-party execution, no SkillClaw daemon, no secrets/cloud storage, no Hermes config mutation.

## Smallest verifiable next slice

Design a Hermes-native “skill candidate staging” harness:

1. Input: one local transcript/task proof bundle, existing relevant skill, and candidate patch proposal.
2. Output: a staged candidate JSON/markdown under `~/.hermes/evidence/skill-evolution-candidates/`, not directly applied.
3. Gate: deterministic checks for frontmatter, trigger breadth, referenced files, and evidence links.
4. Human/skill_manage apply only after review.

This keeps the useful SkillClaw idea while respecting Hermes governance and avoiding proxy/cloud/config side effects.
