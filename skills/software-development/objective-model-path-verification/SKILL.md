---
name: objective-model-path-verification
description: "Use when a task is complex, high-risk, multi-path, or explicitly asks for production-grade/全盘推进/想清楚再做; run an objective-driven gate before execution: objective and cost, situation model, candidate paths, consequence prediction, selected plan, and evidence verification. Do not use for simple Q&A, trivial edits, or urgent small tasks where the overhead exceeds risk."
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [planning, verification, self-evolution, objective-driven, complex-tasks]
    related_skills: [agent-boundary-audit, project-evidence-grounding, test-driven-development, systematic-debugging, taskpool-control-plane]
---

# Objective–Model–Path–Verification Gate

## Overview

This skill turns a vague “think carefully” instruction into a compact, auditable gate before non-trivial work. It borrows the useful part of world-model / objective-driven planning vocabulary without claiming that Hermes has changed its underlying model architecture.

The rule: **do not render or execute the first plausible answer when the task is high-risk. First define the objective/cost, model the situation, compare paths, predict consequences, choose, then verify with evidence.**

## When to Use

Use this skill when any of these are true:

- The user says: `全盘推进`, `生产级`, `长期方案`, `想清楚再做`, `别顺嘴生成`, `用世界模型工作法`, `规划出来的`, or equivalent.
- The task has multiple plausible implementation paths and the wrong path is costly.
- The task touches production, release, data, money, auth, permissions, user-visible UI, lifecycle state, or taskpool/agent control-plane behavior.
- A code change spans multiple files, changes architecture, or could remove/alter existing behavior.
- The user asks for self-evolution, workflow governance, or reusable process landing.
- Evidence requirements matter: real backend/API/UI/tests/logs are required, not mocks.

Do **not** use this skill for:

- Simple factual Q&A after evidence lookup.
- Trivial formatting, small copy edits, or one-command tasks with obvious execution.
- Cases where the user explicitly asks for only a terse answer and risk is low.
- Replacing real tool execution with a plan. This gate decides how to act; it is not proof that action succeeded.

## Core Gate

Detailed `Core Gate` guidance moved to `references/core-gate.md`.

Load it when this subproblem is directly active. Minimum in-root rule: preserve the current skill's safety/verification boundaries and read the reference before executing this specialized branch.
## Compact Output Forms

### Full form for high-risk work

```text
【目标 & 成本】成功标准 / 最小化代价 / 硬约束
【情境模型】关键对象 / 状态源 / 依赖 / 已证据化事实 / 假设
【候选路径 & 后果】A/B/C → 结果、风险、回滚、验收成本
【选择】选中路径 + 对照成本函数的理由
【执行】小步行动清单
【证据】真实命令/文件/接口/UI/日志/截图
【边界】未做什么、为何停、需人工介入项
```

### Compressed form for medium-risk work

```text
目标: ...
约束: ...
选路: A over B because ...
验证: ...
```

### Internal-only form

When the user wants concise output, perform the gate internally and final only the decision, evidence, and next boundary. Do not expose long deliberation unless it helps the user decide.

## Integration with Other Skills

- For self-evolution or durable learning, combine with `agent-boundary-audit` and classify outputs into memory, skill, SSOT doc, taskpool candidate, or do-not-do.
- For software changes, combine with `test-driven-development`, `systematic-debugging`, and `project-evidence-grounding`; this skill does not replace tests.
- When a candidate path depends on disputed causal assumptions or several explanations fit the same evidence, use `scientific-inquiry-evidence-update` inside the situation model: keep alternatives live, derive discriminating predictions, run the smallest valid probe, and update confidence before selecting an intervention.
- For exact staged-artifact review under possible concurrent index mutation, use `references/exact-staged-artifact-concurrent-review.md`: pin the initial binary-diff hash and blob IDs, test pinned bytes rather than an unpinned worktree, guard against stale Python bytecode, and recompute scope/hash immediately before verdict. Index drift blocks certification of the original artifact; a concurrent fix requires its own review.
- For taskpool/control-plane work, combine with `taskpool-control-plane`; task records and evidence ledgers remain canonical. For external repo/video/demo capability absorption, create the taskpool candidate with source/claim/red-lines, then land the next safe bounded implementation slice and write exact proof back to the task record. See `taskpool-control-plane` reference `references/external-capability-absorption-proof-loop.md`.
- For local-brain/workflow auto-constraint layers, do not stop at a final plan or a separate multi-model review artifact. Fold supporting functions (retrieval/index filtering + RouteReview/multi-model routing) back into the canonical BrainConstraintGate, then land the safe ladder: dry-run CLI → `brainctl preflight` → task-intake embedding/blocking → reversible local pre-commit hook. Keep runtime hard gates, taskpool lifecycle writes, cron, external dispatch, publish/deploy, destructive actions, and credential/payment gates closed until exact target/rollback/receipt/readback are separately authorized. See `references/local-brain-auto-constraint-gate-landing.md`.
- For “本地大脑” session recall or local-brain safety-gate progress checks, disambiguate before acting: do not conflate taskpool `human_escape_guard` with local-brain search/indexing or side-effect-gate control-plane sessions. Search for the exact term, identify the CLI session by kickoff/final bookends, then report session id, changed artifacts, receipts, and the remaining boundary. See `references/local-brain-session-disambiguation-and-s7-targets.md`.
- For external web-scraping / web-cleaning / RAG ingestion tools, first absorb them as local-file evidence preprocessors, not as authoritative domain decision-makers or global MCP/network agents. Keep extraction success advisory until domain readback/certification exists. See `references/external-web-scraper-to-evidence-preprocessor.md`.
- When a user asks to drain a taskpool to empty, treat it as a governed drain loop rather than permission to force completion: repeatedly run review close, blocked resolve, retry promotion, boundary reclass, subtask sync, dispatch, and worker readback; release orphaned running claims only through lifecycle commands back to retry; stop at hard gates such as missing artifacts or multimodel quorum. See `taskpool-control-plane` reference `references/drain-to-empty-and-orphan-claim-recovery.md`.
- If taskpool `review -> done` is blocked by `PASS_ADVISORY_ONLY`, do not treat the advisory multimodel result as completion authority. Add concrete lifecycle evidence (`command: ... test/verification PASS`, `artifact:...`, and explicit UI/API non-applicability proofs only for governance-only tasks), then retry the normal transition; avoid `--force`. See `taskpool-control-plane` reference `references/semantic-profile-and-advisory-closeout.md`.
- When the user approves absorbing an external/social/demo effect and asks to add it as a project or land it across ends, do not stop at a chat summary or claim runtime completion. Create a governed project profile/SSOT/contract/roadmap/evidence index/progress ledger, register it in Portfolio OS when available, and create per-end implementation cards with evidence gates. See `references/external-demo-to-cross-end-project.md`.
- For user-facing UI work, add visual/UI verification and avoid mock-only acceptance.
- For nested status-only health checks, use `references/bounded-readonly-health-probes.md`: budget the complete inner timeout plus padding below the outer runner timeout, force no-browser/no-auto-auth/no-business-read/no-external-write invariants, and treat a specific bounded degraded result as observability success rather than dependency health.
- When a full-landing task uses an external/design-tool screen as the target (Stitch, Figma-like tools, generated mockups), land the design as a named SSOT, wire a read-only design gate, add separate runtime/interaction and visual-structure gates, and preserve semantic boundaries between design copy and runtime capability claims. See `references/design-ssot-to-runtime-gate.md`.

## Control-plane resume verification

Detailed `Control-plane resume verification` guidance moved to `references/control-plane-resume-verification.md`.

Load it when this subproblem is directly active. Minimum in-root rule: preserve the current skill's safety/verification boundaries and read the reference before executing this specialized branch.

## Continuation Exit Gate

When the user says `继续推进`, `全盘推进`, `不以阶段/人工接入为中止借口`, `直至方案全部落地`, or equivalent, load `references/continuation-exit-gate.md` and apply it before any final response. Passing tests/build/doctor for one slice is only a checkpoint. Finalize only after the next safe local/reversible slice list is empty, or the remaining work is blocked by a concrete authority/evidence boundary such as credentials, external dispatch, lifecycle mutation, payment/legal/device effect, destructive operation, production target without rollback/readback, or missing evidence after attempted retrieval.

For requests to continue until an entire Agent OS/control plane is `global certified`, also load `references/global-certification-authority-evidence-closure.md`. It defines the inventory → procedure E2E → operational health → independent-receipt conjunction, strict proof/artifact migration evidence, local-CLI origin limitations, exact AuthorityRequest construction, OAuth human gates, dirty-worktree ownership boundaries, and the rule that scoped verifier PASS must never be promoted into global certification.

## Runtime Prompt-Gate Landing

When operationalizing this workflow as a Hermes runtime/system-prompt gate:

- Keep the architecture claim bounded: this is configurable prompt guidance, not a learned world model.
- Add an explicit config switch and avoid injection when the runtime lacks the relevant tool/skill capability.
- Test enabled, disabled, and tool-unavailable paths, then smoke-test the final built prompt for both the guidance text and the skill name.
- If modifying the gateway that carries the active conversation, do not restart it casually inside the reply chain; land code/tests/commits first and state the safe-restart boundary.
- See `references/runtime-prompt-gate-landing.md` for the session-derived checklist and verification evidence pattern.

When a default-off advisory prompt/readback surface is implemented and the user gives broad wording such as “全部允许”, consume only the smallest live advisory-config boundary first. Enable the config via the canonical CLI, read back that the advisory surface is true, and also read back that real routing/tool invocation/external dispatch remain false. Do not invent a real execution target from broad authorization. See `references/live-advisory-config-enable-boundary.md`.

Scope: agent-control-plane / workflow-control-plane boundary advancement. Applicability: a local advisory/route-preflight surface is already enabled and the user authorizes continuing, but the next safest advancement is to expand review/certification rather than execution. Anti-condition: do not use this to open tool invocation, scheduler/worker, lifecycle-write, external dispatch, publish/deploy, or destructive gates. Add a default-off multi-model/adversarial review preflight, prove neighboring gates remain false, run deterministic tests + independent code review + no-action multi-model certification, and repair evidence-ID mismatches before claiming certification. See `references/multimodel-review-preflight-boundary.md`.

- When a broad Agent OS / personal AI OS advancement packet has already landed, do not stop merely because a roadmap phase completed or a generic “human intervention” label appears. If the next step is still local, read-only, reversible, and authority-safe, continue into native projection surfaces such as CLI status/doctor commands or authenticated dashboard readback endpoints, while keeping executor/lifecycle/external/secret/payment/device gates closed. See `references/personal-ai-os-projection-to-native-surface.md`.

After native Agent OS projection surfaces exist and the user continues authorizing safe progress, keep advancing the read-only control-room ladder before stopping: authenticated dashboard panels, local filters, URL deep-links, receipt packets, operator handoff summaries, and browser-local integrity hashes. Preserve hard gates (execution/lifecycle/external/secret/payment/legal/device) and verify with tests + browser interaction + console readback. See `references/personal-ai-os-readonly-control-room-progression.md`.
- After a read-only native projection surface exists, the next safe local slices can be operator-readback improvements rather than executor gates: detail panels, local filters with `Showing X of Y` counts, URL-query/deep-link filter hydration, deterministic receipt packets with all side-effect flags false, and read-only handoff summaries. Treat these as display/projection work only: no clipboard/file export, external send, lifecycle write, or tool execution without a separate authority gate.
- When the user asks to keep advancing to authorized items after a validated local projection/contract slice, do not stop at the first green card or endpoint if safe projection-state coverage remains. Add read-only state galleries/aggregates for success, human-gate/blocked, and budget/error/known-limits states; verify tests + runtime readback + browser visual readback; keep executor/taskpool/model/external/hardware/deploy/secret/payment/destructive gates closed. See `references/authorized-local-projection-state-gallery.md`.
- When native `hermes agent-os status --json` is unhealthy because `06-projection/` or `07-shadow/` artifacts are missing while a subpacket such as `12-personal-ai-os/` is healthy, treat it as native readback artifact-contract drift. Use `references/agent-os-native-readback-artifact-drift.md`: regenerate/source-read, adapt into native paths, create a real shadow report, add coverage-registry dimension, and verify with status/doctor/route + JSON/readback assertions without opening execution/external gates.
- For forked/downstream release workflows, separate ordinary install updates from maintainer upstream synchronization: ordinary update checks compare against the downstream release target, while owner/dev checks compare that release target to the upstream source in an explicit read-only mode first. See `references/downstream-release-vs-upstream-sync-boundary.md`.

## Pitfalls

1. **Not-claimed-without-cooperation trap**: When reporting remaining unclaimed scope after a certification/全盘推进 pass, do not leave a vague list of “not certified / not claimed” items. Classify each remaining item by what the user must provide or whether no user input is needed: `needs-user-target` (exact id/platform/env), `needs-user-payload` (exact message/command/content), `needs-user-acceptance` (taste/grade/scope threshold), `needs-human-secret` (credential/payment/password must be entered by the human), or `no-user-input-needed` (safe local/reversible work remains; continue instead of asking). Broad authorization lets the agent continue safe local/reversible slices, but high-side-effect execution still needs exact target + rollback/readback before action.

2. **Backlog-as-boundary trap**: When the user asks for “企业生产级别”, “可交付用户体验”, “全盘推进”, or equivalent, do not leave safe local product gaps as “后续建议” merely because they were listed in a workflow backlog. A backlog item is only a stop point if it crosses a real authority/evidence/safety boundary. Otherwise continue the next safe slice, update the PRD/workflow/backlog to mark it done, and verify with tests/UI evidence. Also separate test fixtures from product experience: mocks may prove behavior, but user-facing UI must not expose mock/demo/debug fields as if they were product copy.
2. **Single-safe-slice stop trap**: If the user explicitly says “继续推进”, “不以推进阶段与人工接入为中止借口”, or “直至方案全部落地”, do not stop after landing one safe slice just because tests/build/doctor passed. Treat “next safe local slice exists” as the continuation condition: immediately continue through the safe read-only/reversible ladder until the remaining backlog is either completed/local-equivalent or blocked by a concrete authority boundary (credentials, external dispatch, lifecycle mutation, payment/legal/device effects, destructive change, or missing evidence). Final reports may mention next safety surfaces only after you have either landed them or proved they cross a real gate.
2. **Inventory-as-proof trap**: For “真实模型/节点/adapter 是否可用” work, a module scan or registry listing is only discovery, not delivery. If safe and reversible, continue through an isolated runtime setup, real non-stub smoke (`/health` plus the actual inference/API endpoint), fail-visible no-stub-fallback gate, UI readiness readback, docs/PRD sync, and tests before calling it integrated. If the smoke uses a synthetic/blank frame, bound the claim to runtime/API execution and do not imply domain recognition quality.
2. **Reference-effect absorption trap**: When the user asks to learn an external/open-source project’s “effect” and land it as an owned production-grade capability without changing existing interaction logic, do not cargo-cult the reference UI/runtime or add new always-on behavior by default. First classify transferable capabilities vs rejected mechanics, then land a reversible owned boundary such as a read-only readiness profile, diagnostics surface, contract, or governance wrapper that preserves current commands/flows and existing side-effect gates. Only proceed to UX/runtime changes after a separate explicit authority gate.
2. **Design-artifact-as-proof trap**: A generated Stitch/Figma/mockup screen is not proof that the product has the behavior, and a passing runtime test is not proof that the design layer is governed. For full landing, keep both: named design SSOT + read-only design gate + local artifact/readback + browser interaction smoke + visual-structure or screenshot gate. Explicitly mark future/design-only elements and runtime semantic boundaries so the UI does not imply model/recognition/safety capability that the backend has not evidenced.
3. **Taskpool-as-proof trap**: Adding an external capability absorption task to the pool is only tracking, not delivery. If the user also says “全盘推进”, continue with the next safe bounded slice immediately, verify with real tests/UI/diagnostics, commit scoped changes, and write the proof/commit hashes back to the task record. Stop only at true gates such as default-on microphone/wake-word privacy, credentials, destructive actions, external publish/send, or failed certification.
3. **Marketing-word trap**: “world model” vocabulary is a planning metaphor here, not proof of JEPA-like architecture or environment learning.
2. **Plan-as-proof trap**: a clean plan is not completion. Completion requires real evidence.
3. **Over-triggering**: applying the full form to every small request wastes time and tokens. Use compressed or skip when risk is low.
4. **Single-path bias**: if only one path is considered, the model is probably still “顺嘴生成”. Compare alternatives unless the task is truly constrained.
5. **Memory pollution**: do not save one-off task choices as memory. Durable procedure belongs in skills; scoped evidence belongs in SSOT docs or task records.
6. **Authority expansion**: user trust in “全盘推进” does not authorize destructive cleanup, secret handling, payment, credential entry, broad config rewrites, or external publishing without the relevant scope and gates.
7. **Promoted-path overwrite trap**: after promoting a shadow/staging artifact to production, existing deterministic cron jobs or fallback writers may still target the same production path and silently overwrite the promoted result. Reconcile, pause, or retarget old writers before calling the promoted path steady-state.


## Common Pitfalls

1. Applying this skill mechanically after the user's goal has shifted. Re-check the current request before acting.
2. Treating a plan, stale memory, or prior report as proof of completion. Verify with fresh readback.
3. Ignoring neighboring skills or narrower workflows that better match the task. Prefer the most specific applicable skill.

## Verification Checklist

- [ ] Objective and hard constraints were explicit before execution.
- [ ] At least two paths or a justified single-path constraint were considered.
- [ ] The selected path was chosen against a cost function, not convenience.
- [ ] The execution plan was broken into verifiable steps.
- [ ] Completion claims are backed by real evidence.
- [ ] For `继续推进` / `全盘推进` / full-landing tasks, the Continuation Exit Gate was run: no safe local/reversible next slice remains, or every remaining item is a concrete authority/evidence boundary.
- [ ] Unverified assumptions and boundary stops are labeled honestly.
- [ ] Durable learnings were landed in the right boundary, not dumped into memory.
