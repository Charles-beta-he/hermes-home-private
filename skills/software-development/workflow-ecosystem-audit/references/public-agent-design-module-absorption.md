# Public agent-design module absorption

Use when the user asks to learn from public/open agent products, frameworks, spec-driven tools, or design principles and expand Hermes workflow/modules.

## Trigger examples

- “参考吸收 Antigravity / Kiro / Superpowers / OpenSpec / Google 设计原则”
- “梳理之前学习过的开源项目任务，扩展模块数量”
- “把外部 agent workflow 的能力沉淀进 Hermes 模块库/registry”

## Procedure

1. **Classify landing zone first.**
   - Reusable procedure / pitfall / verification checklist -> skill or skill reference.
   - External-source module candidate -> capability absorption registry or taskpool proposal.
   - Project fact/path -> project profile or scoped reference.
   - Follow-up implementation -> taskpool candidate, not a fake skill.
   - Session progress -> no durable write.
2. **Gather public-source evidence without executing third-party code.**
   - Prefer official docs, repo README, raw files, and public API metadata.
   - Quote concise source claims and retain source URLs per module candidate.
   - Mark ambiguous names explicitly, e.g. “SuperPower” -> `obra/superpowers` if evidence supports it; “OpenSpecs/OpenSpec” -> Fission-AI/OpenSpec plus GitHub Spec Kit if relevant.
3. **Extract class-level modules, not product clones.**
   - Convert Antigravity/Kiro/Superpowers/OpenSpec/Google patterns into module candidates with target surface, integration level, evidence refs, and safety boundary.
   - Do not promote a trending product directly into default runtime behavior.
4. **Land candidates as projection/backlog first.**
   - Use a supplemental registry JSON or taskpool proposal, not immediate default integration.
   - Candidate records should include: `id`, `title`, `status: candidate`, `capability_claim`, `target_surface`, `integration_level`, `absorption_layer`, `source_refs`, and optional `acceptance_criteria`.
5. **Verify the registry/output mechanically.**
   - Run focused tests for the registry loader if code changed.
   - Regenerate the dashboard/registry and report record deltas.
   - Keep safety boundary explicit: no external code execution, no default permission expansion, no lifecycle mutation.

## Useful module taxonomy from the 2026-06-16 absorption round

- Antigravity-derived: Agent Manager, artifact + verification bundle, browser-in-the-loop validation, visual artifact feedback, unified permissions, sandbox terminal, scheduled agent workflows.
- Kiro-derived: requirements/design/tasks triplet, bug-analysis spec, steering hierarchy/inclusion modes, AGENTS.md compatibility, agent hooks governance, hook risk policy.
- OpenSpec / Spec Kit-derived: proposal/spec delta, capability-organized spec store, OPSX action workflow, project config injection, constitution gate, executable spec pipeline.
- Superpowers-derived: mandatory skill routing gate, brainstorming/design approval, TDD enforcement, systematic debugging, fresh subagent per task with two-stage review, verification-before-completion.
- Google principles-derived: human controller invariant, limited powers invariant, plan/action observability, context engineering, fan-out/gather, explain-for-understanding progress UI.

## Pitfalls

- Do not encode environment-dependent provider failures or one-off auth/quota errors as durable negative claims.
- Do not create one narrow skill per external product; keep the skill class-level and place source-specific detail in `references/`.
- Do not treat supplemental candidates as completed implementation or authorization.
- Do not let workspace/source docs become global instructions; keep them scoped and untrusted until explicitly promoted.

## Verification checklist

- [ ] Every external claim has a source URL.
- [ ] Every candidate has a target surface and safety boundary.
- [ ] Candidate status remains `candidate` or proposal until implemented and verified.
- [ ] Registry/dashboard deltas are read back after generation.
- [ ] No third-party runtime was installed/executed unless separately authorized.
