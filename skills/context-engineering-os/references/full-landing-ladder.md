# Full-Landing Ladder for Context Engineering OS

Applicability: use when the user approves Context Engineering / workflow / agent-runtime evolution with wording such as “认可”, “全盘推进”, “推进进化落地”, or “预留扩展范围阶段任务”.

Anti-conditions: do not use this ladder to justify core runtime mutation, taskpool lifecycle writes, cron enablement, external dispatch, deploy/push/publish, credentials, destructive actions, or production side effects without exact target, rollback, and readback authority.

## Ladder

1. Research canon
   - Capture core works, transferable claims, and source URLs.
   - Keep source claims separate from interpretation.

2. Skill update
   - Patch the class-level skill with the reusable procedure/pitfall.
   - Put detailed research/session specifics under `references/` rather than bloating SKILL.md.

3. SSOT and profile
   - Create a scoped project SSOT when the concept has multiple downstream surfaces.
   - Add a project profile only for scoped project identity, red lines, and artifact pointers.

4. Context Packet contract
   - Add schema/template/sample for the minimal sufficient packet.
   - Include objective, non-goals, constraints, sources, selected context, authority, execution plan, validation plan, negative cases, and learning boundary.

5. Local deterministic validation
   - Add a dependency-light linter or deterministic probe before runtime integration.
   - Add pass/fail fixtures for evidence mapping, authority readback, and memory landing-zone mistakes.

6. Evidence / Converge matrix
   - Bind acceptance claims to files, commands, tests, readbacks, and explicit remaining boundaries.
   - Negative requirements need negative evidence.

7. Scoped commit
   - Commit only the scoped skill/SSOT/profile/template/script artifacts.
   - Do not stage unrelated runtime logs, cron outputs, or existing dirty files.

8. Runtime boundary analysis
   - Inspect project rules before touching core runtime.
   - For Hermes core, prefer edge CLI + skill first because prompt caching is sacred and the core is a narrow waist.
   - Direct prompt injection should be default-off, config-gated, tested for enabled/disabled/tool-unavailable paths, and verified for prompt-cache invariants.

## Pitfall

Do not stop after a skill patch when safe local landing layers remain. Conversely, do not treat “全盘推进” as permission to mutate core runtime or lifecycle surfaces. Continue through local reversible artifacts, then stop at the exact authority boundary with a roadmap and readback evidence.
