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

### Full-landing semantics

Scope: complex implementation, workflow/control-plane, UI/API, or automation tasks where the user says “全盘推进”, “完整落地”, “推进至需人工介入”, or equivalent. Applicability: when the request is to build or repair the actual working system, not only advise. Anti-condition: do not use this wording to bypass permission, value-judgement, destructive, external-side-effect, credential, or evidence-insufficient gates.

For these requests, the default completion target is not a plan, draft, read-only projection, mock, visual-only button, copy-only change, local-only placeholder, or test stub. Start from the target model and carry the work through the real layers that define the intended effect: UI/interaction, API/contract, SSOT/ledger, adapter or executor boundary, persistence, read-back, tests, browser/runtime verification, and scoped commit. If a lower layer is intentionally the endpoint, label it explicitly (for example “record-only; adapter apply not opened”).

If the work reaches a boundary requiring human choice or authority, do not silently downgrade to a weaker layer and call it done. Also do not stop with only “cannot continue.” For self-advancing/workflow-kernel work, the dry-run acceptance bundle is a real scheme boundary: it is safe to land contract/projection/acceptance artifacts, but local executor/runtime/taskpool write-through requires a fresh human gate. Switch into boundary realignment:

1. Restate the initial objective and the full-landing target that is still in force.
2. Identify the exact boundary class: permission/authority, evidence insufficiency, destructive or external side effect, credential/secret, value judgment, or safety/legal risk.
3. Mark confirmed vs unconfirmed facts, including what evidence would remove the boundary.
4. Continue any safe read-only, local, reversible, dry-run, patch-preparation, rollback-design, or verification work that does not cross the boundary.
5. Produce a compact intervention packet for the blocked action: requested authorization or choice, blast radius, rollback/escape hatch, verification after execution, and the default safe next step.
6. Stop only at the smallest necessary confirmation point, preserving the original plan and dependency order.

For complex tasks, run these steps before substantive execution:

1. **Objective & cost function**
   - Define success in concrete terms.
   - List hard constraints/red lines.
   - State what to minimize: risk, regression, user steering, downtime, token cost, migration cost, data loss, etc.

2. **Situation model**
   - Identify key objects, actors, state stores, dependencies, invariants, and permissions.
   - Separate facts already evidenced from assumptions.
   - For project work, locate the canonical source of truth before editing.

3. **Candidate paths**
   - Generate at least two viable paths unless only one is technically possible.
   - Include the “do nothing / defer / ask human” path when authority or evidence is insufficient.

4. **Consequence prediction**
   - For each path, predict likely outcome, failure mode, blast radius, rollback path, and verification burden.
   - Prefer paths that preserve existing behavior, are reversible, and produce evidence quickly.

5. **Selection and execution plan**
   - Choose one path and say why it wins against the cost function.
   - Convert it into small verifiable steps.
   - If action has side effects beyond granted scope, stop and ask or record a taskpool candidate.

6. **Evidence verification**
   - Before claiming completion, attach real evidence: test output, diff, logs, HTTP responses, screenshots, readback, or source citations.
   - If verification is blocked, report the blocker and what was still completed.
   - For multi-repo work, check branch names and pre-existing dirty files before committing. If the active branch is unrelated to the task or unrelated local changes are present, stop at verified working-tree changes and report a scoped commit boundary instead of mixing them into a commit.
   - When a task name can refer to multiple repositories, apps, dashboards, or similarly named artifacts, verify the target artifact path before editing. If the user intends one artifact but wants you to borrow patterns or authority boundaries from another, treat the latter as a reference model, not as the edit target.

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
- For taskpool/control-plane work, combine with `taskpool-control-plane`; task records and evidence ledgers remain canonical.
- For user-facing UI work, add visual/UI verification and avoid mock-only acceptance.

## Control-plane resume verification

When a governed mission/taskpool/control-plane workflow is unblocked and the user asks to “continue,” do not stop at recording the decision. Verify the canonical ledger, clear the human gate through the real decision command/API, wake the executor or scheduler, then read back fresh evidence. See `references/mission-control-resume-verification.md` for the detailed checklist and pitfalls.

When a Mission is blocked by exhausted tick budget rather than an open human decision, first close and commit the current verified slice, then run bounded multi-model continuation sizing, authorize only the narrow budget delta, record the budget event + stage report, wake the governed dispatch path, and read back board/doctor/cron state. See `references/mission-budget-continuation.md` for the session-derived checklist and tick sizing heuristic.

## Runtime Prompt-Gate Landing

When operationalizing this workflow as a Hermes runtime/system-prompt gate:

- Keep the architecture claim bounded: this is configurable prompt guidance, not a learned world model.
- Add an explicit config switch and avoid injection when the runtime lacks the relevant tool/skill capability.
- Test enabled, disabled, and tool-unavailable paths, then smoke-test the final built prompt for both the guidance text and the skill name.
- If modifying the gateway that carries the active conversation, do not restart it casually inside the reply chain; land code/tests/commits first and state the safe-restart boundary.
- See `references/runtime-prompt-gate-landing.md` for the session-derived checklist and verification evidence pattern.

## Pitfalls

1. **Marketing-word trap**: “world model” vocabulary is a planning metaphor here, not proof of JEPA-like architecture or environment learning.
2. **Plan-as-proof trap**: a clean plan is not completion. Completion requires real evidence.
3. **Over-triggering**: applying the full form to every small request wastes time and tokens. Use compressed or skip when risk is low.
4. **Single-path bias**: if only one path is considered, the model is probably still “顺嘴生成”. Compare alternatives unless the task is truly constrained.
5. **Memory pollution**: do not save one-off task choices as memory. Durable procedure belongs in skills; scoped evidence belongs in SSOT docs or task records.
6. **Authority expansion**: user trust in “全盘推进” does not authorize destructive cleanup, secret handling, payment, credential entry, broad config rewrites, or external publishing without the relevant scope and gates.

## Verification Checklist

- [ ] Objective and hard constraints were explicit before execution.
- [ ] At least two paths or a justified single-path constraint were considered.
- [ ] The selected path was chosen against a cost function, not convenience.
- [ ] The execution plan was broken into verifiable steps.
- [ ] Completion claims are backed by real evidence.
- [ ] Unverified assumptions and boundary stops are labeled honestly.
- [ ] Durable learnings were landed in the right boundary, not dumped into memory.
