# LazyCodex / OmO reference self-optimization review — 2026-07-02

## Status

- Source class: external reference repositories, source-verified locally.
- Target: Hermes workflow/control-plane and skill/process layer, not core runtime mutation in this slice.
- Landing state: low-risk docs + skill-reference guidance only.
- Side effects in this slice: local file writes under `~/.hermes/docs/private/` and a Hermes skill reference file; no external dispatch, no publish/deploy, no credential use, no destructive action.

## Source pins

- LazyCodex: `https://github.com/code-yeongyu/lazycodex`
  - Local review path: `/Users/charles/.hermes/runs/lazycodex-reference-review-20260702`
  - Commit: `44aa8c47d90afaba443bb48df80267f6c28ab69b`
- OmO / oh-my-openagent: `https://github.com/code-yeongyu/oh-my-openagent`
  - Local review path: `/Users/charles/.hermes/runs/oh-my-openagent-reference-review-20260702`
  - Commit: `e8ea7faf2de0a38c462ff754c1cea4191f721890`

## Iceberg complexity scan

User correction: before learning from a reference and directly advancing, first run an iceberg scan to decide whether this is a complex task.

Scan result: complex task.

Reasons visible above the waterline:

1. External-reference absorption, not a simple Q&A.
2. Hermes self-optimization / workflow-control-plane target.
3. Multiple plausible landing zones: memory, skill, docs/private SSOT, experience-ratchet, taskpool, core code, runtime gate.
4. Risk of cargo-culting third-party harness mechanics into Hermes core.
5. User expects direct advancement, not a report only.

Submerged complexity:

1. Authority boundary: external agent harness patterns include hooks, lifecycle state, subagents, model routing, plugin installs, telemetry, and autonomous permissions; Hermes must not treat those as automatically authorized runtime behavior.
2. Scope boundary: LazyCodex is Codex Light / Hephaestus-focused, not the full OmO Ultimate harness.
3. Evidence boundary: marketing claims and model consensus are not proof; only source lines, local commands, tests, and readbacks count.
4. Abstraction boundary: transferable pattern is evidence-bound complex-task orchestration, not the exact Codex plugin implementation.
5. Landing boundary: safe immediate advancement is docs/skill/process. Core loop, taskpool lifecycle mutation, cron, external dispatch, or deploy/push require later exact target and verification.

Chosen path after scan:

- Treat as complex but safe for a bounded local documentation/skill slice.
- Create this SSOT evidence note.
- Add a Hermes skill reference that makes the iceburg/iceberg complexity scan and LazyCodex transfer rules reusable.
- Do not mutate Hermes core/runtime in this slice.

## Source evidence

### LazyCodex is a thin Codex distribution over OmO

- `README.md:49`: `npx lazycodex-ai install` is shorthand for `npx --yes --package oh-my-openagent omo install --platform=codex`.
- `packages/web/content/docs/overview.md:1`: LazyCodex is a light port of OmO into Codex and does not ship the full harness.
- `packages/web/content/docs/overview.md:7`: `lazycodex-ai` runs the OmO installer targeting Codex; features come from the `omo` plugin.
- `packages/web/content/docs/overview.md:22`: OmO full harness includes Sisyphus, `.omo/boulder.json`, Hephaestus, specialists, multi-model routing, hooks, and team mode; LazyCodex packages the focused Codex setup.

### Installed capability surface

Local manifest readback from `/Users/charles/.hermes/runs/lazycodex-reference-review-20260702/plugins/omo`:

- Plugin version: `4.15.1`
- Hook count: `21`
- MCP servers: `grep_app`, `context7`, `codegraph`, `git_bash`, `lsp`
- Skills: `ast-grep`, `coding-agent-sessions`, `comment-checker`, `debugging`, `frontend`, `git-master`, `init-deep`, `lcx-contribute-bug-fix`, `lcx-doctor`, `lcx-report-bug`, `lsp`, `lsp-setup`, `programming`, `refactor`, `remove-ai-slops`, `review-work`, `rules`, `start-work`, `teammode`, `ultimate-browsing`, `ulw-loop`, `ulw-plan`, `ulw-research`, `visual-qa`.

### Complex-task orchestration evidence

- `README.md:111`: `$ulw-loop` is a self-referential loop until Oracle-verified completion.
- `README.md:112`: `$ulw-plan` writes a plan and never writes product code.
- `README.md:113`: `$start-work` executes a plan until every checkbox is done.
- `README.md:123-130`: `$init-deep` generates hierarchical `AGENTS.md` project memory for complex directories.
- `packages/web/content/docs/overview.md:28-32`: Hephaestus flow is Explore → Plan → Implement → Verify → Manual QA, with parallel explore subagents, workflows, skills, hooks, model routing, and verification defaults.
- `packages/web/content/docs/ulw-loop.md:5`: a `<promise>DONE</promise>` claim does not end the loop; Oracle verification is required.
- `packages/web/content/docs/ulw-loop.md:15`: closure requires a real captured artifact from HTTP, tmux, browser, plus adversarial pass and cleanup receipt.
- `plugins/omo/skills/ulw-loop/references/full-workflow.md:18-33`: Manual-QA evidence channels are HTTP, tmux, browser, computer-use, and auxiliary CLI/DB/config surfaces; dry-run and “looks correct” do not count.
- `plugins/omo/skills/ulw-loop/references/full-workflow.md:35-52`: parent conducts, workers play; delegation must be right-sized, parallel where independent, and worker prompts must include goal/scope/verification/evidence.
- `plugins/omo/skills/start-work/SKILL.md:120-130`: each checkbox requires plan reread, automated verification, manual QA, adversarial QA, and cleanup evidence recorded to a ledger.
- `plugins/omo/skills/start-work/SKILL.md:132-160`: worker DoneClaim is not final; an independent AdversarialVerify must confirm before FullyDone.
- `plugins/omo/skills/start-work/SKILL.md:171-184`: completion requires final verification plus Global Review and Debugging Gate.

## Transferable Hermes pattern

Name: Iceberg-gated evidence-bound complex-task harness.

Context:

- Use when the user asks Hermes to learn/absorb an external agent workflow, advance itself, govern multi-agent work, or run “全盘推进/direct推进” rather than answer only.

Problem:

- Agents over-apply reference systems: copying hooks, model names, or plugin mechanics into the wrong runtime, and claiming completion from self-report/tests-only evidence.

Forces:

- User wants forward progress, not endless planning.
- Hermes core must stay narrow and cache-stable.
- Complex tasks need durable state and evidence.
- External systems may contain useful patterns but also incompatible mechanics.

Solution:

1. Run iceberg complexity scan first.
2. If simple: answer or do the minimal safe action.
3. If complex: create/identify SSOT, pin source evidence, model authority/side effects, then land the smallest reversible slice.
4. Transfer relationships, not entities: project memory, decision-complete plan, wave/worker decomposition, evidence ledger, independent verifier, cleanup receipt, continuation state.
5. Keep runtime/core/side-effect gates closed until exact target, rollback/readback, and verification exist.

Anti-conditions:

- Do not use the full harness for trivial one-line edits or low-risk Q&A.
- Do not import third-party code/plugins into Hermes core by default.
- Do not treat a Codex/OpenCode hook or role name as a Hermes runtime requirement.
- Do not claim UI/runtime/product completion from docs/skill/process landing.

Falsifiers:

- If a task has one obvious low-risk action with no side effects or durable learning, the iceberg scan should classify it simple and avoid the heavy path.
- If source evidence shows LazyCodex behavior changed, re-pin and re-evaluate before applying this note.
- If a Hermes runtime feature already implements the same gate with stronger evidence, use the runtime feature rather than this docs/skill reference.

## Immediate Hermes landing decision

Landed now:

1. This SSOT note under `docs/private`.
2. A reusable Hermes skill reference under `hermes-agent` for LazyCodex/OmO complex-task harness absorption.

Deferred gates:

1. Core code changes to conversation loop or tool schema.
2. New Hermes runtime hooks or taskpool lifecycle automation.
3. Cron/worker writes or external dispatch.
4. Importing LazyCodex/OmO code or installing third-party plugins.
5. Telemetry or attribution behavior.

## Verification performed

Commands/readbacks:

- `git clone --depth 1 https://github.com/code-yeongyu/lazycodex.git /Users/charles/.hermes/runs/lazycodex-reference-review-20260702`
- `git clone --depth 1 https://github.com/code-yeongyu/oh-my-openagent.git /Users/charles/.hermes/runs/oh-my-openagent-reference-review-20260702`
- `git rev-parse HEAD` in both repos returned the commits listed above.
- Local manifest parser read plugin version, hook count, MCP servers, and skill names.
- `node bin/lazycodex-ai.js --dry-run install --no-tui --codex-autonomous` returned the exact `npx --package oh-my-openagent omo install --platform=codex ...` command.
- `node --test test/aggregate-manifest.test.mjs test/bootstrap-setup.test.mjs test/ulw-research-skill-contract.test.mjs` passed 14 tests and failed 1 due to missing shallow-clone workspace dependency `@oh-my-opencode/shared-skills`; this is recorded as degraded test coverage, not as product/runtime proof.

## Next safe slices

1. Add an explicit “iceberg complexity scan” preflight to Hermes planning/goal-calibration skill surfaces if repeated use confirms it helps.
2. Build a local, default-off evidence-ledger command for Hermes complex tasks before runtime hooks.
3. Add eval prompts: simple task should not trigger heavy harness; external-reference self-optimization should trigger SSOT + evidence-gated absorption.
4. Only after those pass, consider a runtime-facing “complex task harness” scaffold with config-off default.
