---
name: task-framing-governance
description: "Use when frame taskpool work, repo/article ingestion, and architecture follow-ups around long-term maintainable mainline changes instead of minimal-slice patches; encode dependencies, execution order, and systemic template fixes when wording drifts."
---

# Task Framing Governance

## Overview

Frame taskpool work, repo/article ingestion, and architecture follow-ups around long-term maintainable mainline changes instead of minimal-slice patches; encode dependencies, execution order, and systemic template fixes when wording drifts. This skill is maintained as a `pipeline`-shaped contract: it should guide ordered multi-stage work with gates, evidence, retries, and closure states without stealing adjacent workflows or relying on unstated assumptions.

## When to Use

Use this skill when the user's request matches `task-framing-governance` and requires ordered multi-stage work with gates, evidence, retries, and closure states.

Do not use it for:
- generic one-off questions that do not need this workflow;
- neighboring specialist workflows with a narrower matching skill;
- durable memory or project-profile writes unless this skill explicitly governs that landing zone.

Use this when:
- Converting external repos, articles, or research into taskpool tasks
- Reframing existing tasks after the user corrects the approach
- Auditing recently created tasks for duplication, weak framing, or bad default wording
- Designing memory/local-brain work where short-term patches would create long-term maintenance drag

## Core rule

Default to **long-term maintainable mainline architecture** framing, not "smallest verifiable slice" framing, when the task is about:
- architecture evolution
- memory/local-brain changes
- taskpool/control-plane governance
- repo/article absorption into Hermes

Minimal slices are acceptable only as execution evidence inside a larger mainline plan. They must not become the task's primary framing.

## What to encode in the task

For this class of work, make the task answer these questions explicitly:
1. What durable architecture delta should Hermes absorb?
2. What is the execution order / dependency order?
3. What should be absorbed vs explicitly rejected?
4. What skills/scripts/docs/self-checks must be added or updated?
5. What systemic source might be reintroducing bad framing (template, generator, checklist, umbrella skill)?

Prefer language such as:
- "长期可维护主链方案"
- "执行顺序 / 依赖顺序"
- "架构边界"
- "阶段性证据"
- "治理基座 / 上游接口 / 状态机 / 回写路径"

Avoid centering the task on language such as:
- "smallest verifiable slice"
- "最小落地切片"
- "最小闭环改造点"
- "至少一个可派发执行切片"

## Recommended framing by task type

### 1) Repo / article ingestion
Do not create a generic research task.
Frame it as:
- evidence extraction
- Hermes current-state contrast
- architecture delta
- adoption / rejection boundary
- ordered mainline follow-up plan

### 2) Memory / local-brain work
Do not reduce the task to a recall patch.
Frame it around:
- provider boundaries
- retrieval/index architecture
- consolidation state machine
- writeback/evidence paths
- multi-agent sharing boundaries

### 3) Taskpool / workflow governance work
When you find bad wording or weak defaults in multiple tasks, do **not** only hand-edit the affected tasks.
Also create or prioritize a **systemic source-fix task** for the generator/template/checklist that keeps reintroducing the wording.

## Audit checklist for recently created tasks

Check for:
- duplicate scope with older analysis tasks
- weak dependency encoding
- wrong architecture target
- minimal-slice phrasing that conflicts with maintainable-mainline intent
- acceptance evidence that stops at a local patch rather than durable governance artifacts
- template-generated wording that should be fixed at the source

If the problem is systemic, create a follow-up governance task instead of scattering one-off edits.

## Pitfalls

- Do not treat "do something maintainable" as an excuse for vague scope; still name interfaces, boundaries, and order.
- Do not convert every task into a giant rewrite; the mainline plan can still be staged.
- Do not leave the generator/template untouched if it keeps recreating bad framing.
- For this user, memory-related changes should prefer maintainable architecture over minimal viable patches.

## Example adaptation

Bad:
- "研究 repo X，给一个最小可吸收切片。"
- "先加一个字段验证想法。"

Better:
- "提炼 repo X 对 Hermes 的长期可维护架构增量，明确吸收/拒绝边界、执行顺序，以及需要新增或修订的技能/脚本/文档/自检项。"
- "先对照现有记忆体系，拆出 provider 边界、retrieval/index、capture/consolidation、evidence writeback 的主链顺序。"

## When the user corrects framing

If the user says tasks/solutions should not be framed as minimal landing slices:
1. Patch the current tasks immediately.
2. Update the governing task-framing skill.
3. Check whether a generator/template/checklist caused the wording.
4. If yes, create a dedicated source-fix task so the correction persists.

## Verification Checklist

- [ ] Preconditions, scope, and tool availability were checked before following this workflow.
- [ ] The key output artifacts, commands, or side effects were verified by read-back or direct inspection.
- [ ] Any remaining uncertainty, blocker, or human handoff was stated explicitly.
- [ ] Every stage passed its gate before the next stage advanced, with evidence recorded.
