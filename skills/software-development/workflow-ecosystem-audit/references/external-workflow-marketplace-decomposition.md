# External Workflow Marketplace Decomposition Pattern

Scope: reusable workflow-audit pattern for analyzing an external skill/plugin/command marketplace or similar process library. Applicability: use when a user asks to “分析补充完整工作流”, “梳理工作流”, or adapt an external workflow library into the active system. Anti-condition: do not copy a repository’s local names or counts as global rules; treat them as source facts for the current analysis only.

## Analysis sequence

1. **Source grounding**
   - Open the media/article/post that introduced the library.
   - Extract visible claims: artifact name, author, date, caption, engagement, and frame text.
   - Verify the actual external artifact directly (repository/site/docs), not only the post.

2. **Repository/library model**
   - Read agent guidance (`AGENTS.md`, `CLAUDE.md`, README, manifests) before interpreting structure.
   - Identify hierarchy: marketplace → plugin/module → skill/reference → command/workflow → validation script.
   - Run provided validators when safe/read-only to separate real structure from marketing claims.

3. **Workflow map**
   - Map each command/workflow to a lifecycle stage, not just a folder name.
   - Distinguish nouns/concepts (skills/frameworks) from verbs/processes (commands/workflows).
   - Build an end-to-end lifecycle: intake → discovery → evidence → strategy → PRD/spec → risk gate → planning → build/verification → launch → measure → retro/ratchet.

4. **Gap analysis**
   - Look for missing evidence gates, state machine, SSOT/project storage, real-system integrations, quality evals, and post-launch decision closure.
   - Call out whether follow-up suggestions are merely prose or machine-readable next-state transitions.

5. **Adaptation plan**
   - Convert useful patterns into class-level workflows for the active environment.
   - Prefer a small number of high-leverage chains before broad import.
   - For agent/control-plane systems, preserve evidence ledgers, taskpool candidates, read-back verification, and ratchet/skill updates.

## Output shape

```text
事实源：media/post + verified artifact + validator/readback evidence
核心判断：what the system really is
结构模型：marketplace/plugin/skill/command/validator
完整工作流：stage-by-stage lifecycle
缺口：evidence/state/SSOT/integration/eval/closure
适配：which workflow chains to implement first
边界：what was not verified or should not be copied
```

## Pitfalls

- Do not flatten a marketplace into a long list of narrow skills; preserve class-level domains and workflow chains.
- Do not mistake command follow-up prose for a durable workflow state machine.
- Do not treat README counts as truth if a validator or file enumeration can verify them.
- Do not copy protected or third-party skills blindly; extract transferable patterns and cite the source facts.