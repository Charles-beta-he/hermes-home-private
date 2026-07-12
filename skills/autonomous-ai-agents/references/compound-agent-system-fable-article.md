# Compound agent system pattern from X/Fable article

Scope: class-level absorption of the X Article `Build self-improving agent system with Fable 5 in 14 steps : loops, dynamic workflows, routines` (`https://x.com/0xCodez/status/2065089060104720776`, article `https://x.com/i/article/2065077530571264000`).

Authority boundary: the X article is a secondary/social source. Model/product-specific claims such as exact Fable/Mythos pricing, release timing, safety behavior, or benchmark numbers must be verified against Anthropic docs/news/system cards before being treated as facts. The transferable lesson below is workflow architecture, not proof of any provider capability.

## Transferable model

Do not treat a frontier model as a better chat box. Treat it as one node in a compounding system:

```text
primitives -> orchestration loop -> scoped memory -> independent verification -> writeback/ratchet -> next run
```

The system improves because verified environment state, rules, rubrics, and skills accumulate outside the model. This is not self-learning or weight updates; it is governed external state plus evidence-backed procedural refinement.

## Capability graph

1. **Orchestrator role**
   - Handles long-horizon planning, decomposition, routing, and synthesis.
   - Should be expensive/high-capability only when the task requires multi-stage reasoning, large-context integration, or durable writeback.
   - Cannot close its own completion claims without objective evidence.

2. **Worker roles**
   - Execute bounded subtasks in isolated contexts.
   - Use cheaper/faster models when work is simple, repetitive, or locally verifiable.
   - Output artifacts and command/readback evidence, not just summaries.

3. **Verifier role**
   - Independent from the worker/maker context where practical.
   - Judges artifact + rubric + evidence, not the maker's reasoning trail.
   - Returns pass/warn/fail/blocked with missing evidence and exact next action.

4. **State/memory layer**
   - Project state file / SSOT: current facts, attempts, decisions, open risks.
   - Skill/procedure layer: reusable “how to do this class of work” lessons.
   - Evidence ledger: command outputs, screenshots, logs, URLs, artifacts.
   - Retention policy: do not store secrets, raw private payloads, or stale task progress in reusable memory/skills.

5. **Writeback/ratchet layer**
   - Only confirmed lessons get promoted.
   - Failed or uncertain observations stay as evidence notes or task-local state.
   - Skills are patched when a repeated class-level procedure is improved; project facts remain scoped to project SSOT.

## Loop patterns worth reusing

- **Goal/outcome loop:** define a measurable end condition before execution; iterate until an independent grader passes or a budget/safety gate stops.
- **Fan-out and synthesize:** split independent evidence or implementation slices into clean contexts, then synthesize with source-linked claims.
- **Adversarial verification:** run maker and verifier separately; verifier should have artifact/rubric/evidence but not maker-private rationalization.
- **Loop until no-new-findings:** continue investigation until logs/tests/searches produce no new relevant findings, or a stop condition fires.
- **Classify-and-route:** route by capability surface and risk, not by default model preference.
- **Worktree/isolated workspace safety:** parallel code experiments need isolated workspaces to avoid file collisions and contaminated evidence.

## Hermes mapping

- `/goal`-like behavior maps to: explicit acceptance criteria + evidence contract + budget/authority gate + verifier/readback.
- “Routines” map to cron/pipeline/taskpool only after exact schedule, deliver target, rollback, and receipt/readback are authorized.
- “Skills that compound” maps to `skill_manage` patches for reusable procedures, not memory writes of task progress.
- “STATE.md” maps to project SSOT/profile/ledger artifacts, not global memory unless the fact is stable across sessions.
- “Vision self-check” maps to real screenshot/visual audit evidence; UI completion still requires uIMax/browser evidence when requested.
- Provider safety/classifier boundaries map to explicit fallback routes and blocked states, not silent downgrade or fake completion.

## Anti-patterns

- Prompt-and-close: no state, no proof, no writeback, no compounding.
- Self-critique as proof: the maker grades itself without objective evidence.
- Skill pollution: writing unverified social claims or one-off task progress into global skills.
- Model monoculture: using the top model for lint/doc/simple refactor work where cheaper workers suffice.
- Runtime overclaim: claiming an agent loop exists because a document describes it.
- Unbounded autonomy: loops without budget, stop condition, readback, rollback, or human gate.

## Minimum implementation contract

```yaml
goal: observable desired state
acceptance: commands/screenshots/logs/files/API readbacks
budget: max_turns/max_cost/max_runtime
workspace: isolated path/worktree when writing code
maker: executor model/tool contract
verifier: independent rubric + evidence-only context
state_read: project SSOT + relevant skills
state_write: evidence ledger first; skill/project writeback only after verification
gates: permission, external write, publish/deploy, destructive, credentials, retention
closure: pass/warn/fail/blocked with evidence refs
```

## Verification checklist

- [ ] Source claims are separated from verified provider docs.
- [ ] The loop has an objective, budget, and stop condition.
- [ ] Maker and verifier roles are separated or self-review is justified by deterministic evidence.
- [ ] State writeback target is correct: project SSOT vs skill vs memory vs no-write.
- [ ] Evidence is read back before completion is claimed.
- [ ] External writes, schedules, deployments, and credentials remain gated.
