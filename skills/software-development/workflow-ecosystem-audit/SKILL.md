---
name: workflow-ecosystem-audit
description: Use when asked to '梳理工作流', 'review workflow', 'skill gaps', '缺省流程', or when setting up a new project workspace.
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags:
    - workflow
    - audit
    - skills
    - gaps
    - planning
    - ecosystem
    related_skills:
    - domain
    - software-development
---

# Workflow Ecosystem Audit — 工作流全景梳理与缺省流程补充

## Overview


> 把散落在各 skill 里的流程拼成一张完整的地图，找到没盖住的地方，补上。

## When to Use

- 用户说"梳理工作流"、"review workflow"、"skill gaps"、"缺省流程"
- 新项目启动，需要确认 workflow 覆盖度
- 新增一批 skill 后，需要重新对齐工作流
- 发现 skill 引用 broken（references 指向不存在的文件）


- Don't use for: tasks outside this skill's trigger class, requests with a more specific neighboring skill, or situations where required evidence/tooling is unavailable.
## Core Principle

**Skills 是散落的拼图，Workflow 是拼完后的画面。** 单独每个 skill 可能完整，但拼在一起时可能有缝。

## Audit Steps

Reference: `references/external-workflow-marketplace-decomposition.md` documents the source-grounded pattern for analyzing external workflow/plugin marketplaces: verify the artifact directly, distinguish skills from commands/workflows, map a lifecycle, then identify evidence/state/SSOT/integration gaps before adapting it.

Reference: `references/layered-local-knowledge-coverage-audit-loop.md` documents the reusable audit-and-repair loop for Markdown-first local brains and knowledge vaults: separate structural, schema, link, index, runtime-read, test, dashboard, governance, and certification coverage; refresh derived projections in dependency order; add a bounded hash-bound live adapter selfcheck under TDD; classify remaining debt rather than bulk-filling metadata; and close with claim-level positive and negative evidence.

Reference: `references/open-source-absorption-module-registry.md` documents the pattern for turning scattered open-source/repo learning tasks into a machine-readable module registry, local-brain compiled knowledge entry, and formal minimum-slice-to-durable-delivery governance flow.

Reference: `references/composable-capability-graph-workflow-coverage.md` documents the composable module/workflow/agent ontology and cross-workflow abstraction coverage audit pattern: treat modules, workflows, and agents as views over capability nodes; require stable I/O, subnodes, AgentWrapper policy, gates, closure states, and coverage scoring across neighboring workflow families before promoting a demo-derived abstraction.

Reference: `references/goal-control-plane-production-audit.md` documents the production-grade audit pattern for agent/workflow systems that have `/goal`, hooks, taskpool/mission/cron, dynamic workflow, observer, or proof surfaces: separate control-plane contracts from executors, classify diagnostic/test-covered layers honestly, and land dry-run primitives before side effects.

Reference: `references/engineering-coverage-truth-audit.md` documents the evidence-calibrated engineering coverage audit: separate architecture, runtime integration, live health, and closure; route the exact user intent; require every registered system to be covered/missing/N/A; compare static readiness with real runtime smoke; reconcile current projections with event history; and bound failed multi-model review as not certified.

Reference: `references/smart-routing-coverage-audit.md` documents the audit pattern for intelligent routing coverage questions: separate conversation main model, pre-turn intent/workflow routing, task tier routing, multi-model execution/verification, taskpool event-hook routing, and existing-project profile/SSOT routing before claiming a workflow is covered.

### Step 1: Enumerate Skills by Category

```bash
# List all skills with categories
skills_list()
```

Filter by relevant category (e.g., `software-development`).

### Step 2: Load Each Skill & Check References

For every skill in the target category:

```python
skill_view("skill-name")
```

Check the `linked_files` field. If it references files that don't exist, mark as **broken reference**.

**Common broken reference pattern**: SKILL.md says "详细协议见 references/p*-protocol.md" as if a wildcard were a real file, but no concrete protocol file exists.

### Step 3: Map Skills to Workflow Stages

Define the standard workflow stages for your domain. For software development:

```
[0] 需求接收 → [1] 战略设计 → [2] 任务拆解 → [3] 编码实现
      → [4] 代码审查 → [5] 验证测试 → [6] 构建部署
      → [7] 上线验证 → [8] 事故复盘 → [9] 持续优化
```

Map each skill to the stage(s) it covers. A skill may cover multiple stages.

### Step 4: Identify Gaps

For each stage, check:
- Is there a skill that covers it?
- Is the skill complete (no broken references)?
- Does it have a Definition of Done?

Mark stages as:
- ✅ Covered — skill exists and complete
- ⚠️ Partial — skill exists but references broken
- ❌ Missing — no skill covers this stage

### Step 5: Create Missing Pieces

For each gap:

**Broken references** → Create the missing referenced file:
```bash
mkdir -p ~/.hermes/skills/{skill-name}/references/
# Write the protocol/template file
```

**Missing stage skill** → Create a new skill:
```bash
mkdir -p ~/.hermes/skills/software-development/{new-skill-name}/
# Write SKILL.md with Definition of Done
```

**Missing protocol** → Write the protocol document that the skill references.

### Step 6: Output Workflow Map

Generate a terminal-readable report with:
1. Workflow stage map (9 stages with status)
2. Role hierarchy diagram (P10 → P9 → P8/P7)
3. Trigger word cheat sheet
4. Key deliverable checklist (which doc → which stage → which role)
5. Remaining gaps that need project-specific customization

## Key Findings from This Pattern

### Broken References Are Silent Failures

Skills with `linked_files` pointing to non-existent files don't crash — they just fail to load the referenced content. The skill still "works" but misses critical context.

**Fix**: After creating a skill with linked files, always verify:
```bash
ls -la ~/.hermes/skills/{skill-name}/references/
```

### Skeleton Skills vs Complete Skills

A "skeleton skill" has:
- SKILL.md with description and "详细协议见 references/..."
- Empty or missing references/ directory

A "complete skill" has:
- SKILL.md with inline instructions OR
- SKILL.md + populated references/ with all linked files

Skeleton skills are common when skills are created incrementally. The audit catches them.

### Workflow Stages Are Domain-Specific

The 9-stage model above is for software development. Other domains need different stages:
- **Data Science**: [0]数据获取 → [1]清洗 → [2]探索 → [3]建模 → [4]验证 → [5]部署 → [6]监控
- **DevOps**: [0]需求 → [1]设计 → [2]IaC → [3]CI → [4]部署 → [5]观测 → [6]on-call

Adapt the stage model to your domain.

### Open-source Learning Task Registries

When the audit target is a history of source-review/open-source learning tasks, do not create a long flat list of repo-specific skills or modules. Use the bounded registry pattern in `references/open-source-absorption-module-registry.md`: keep original task notes as SSOT, create a human map plus machine-readable registry, count primary vs support tasks separately, and include a verifier that checks schema/module count/unique ids/path existence. The stable landing is a reusable module taxonomy plus next minimal verifiable slices, not a narrative recap.

### Goal / Hook / Dynamic Workflow Production Audits

When auditing an agent workflow system that already has `/goal`, hooks, taskpool, mission, cron, dynamic workflow, or proof concepts, do not treat design docs or isolated passing tests as production integration. Use `references/goal-control-plane-production-audit.md` and classify each surface as production-integrated, test-covered-but-unintegrated, diagnostic/prototype, advisory-only, or missing.

Preferred landing order:
1. Read the live runtime paths and persistence layer directly.
2. Add or verify a structured control-plane contract (for example a goal spec) before executor work.
3. Add or verify an advisory route/dry-run decision before lifecycle mutation.
4. Keep `/goal set` and status operations side-effect safe: no taskpool enqueue, mission write, cron create, DAG execution, or external side effect.
5. Convert concrete follow-up engineering gaps into taskpool/proposal candidates; do not encode them as narrow one-session skills.

Production-grade red flags:
- a migration doc says complete, but the main runtime path never calls the migrated component;
- hooks are fail-open observers but are described as safety gates;
- a judge accepts response text instead of proof/evidence bundles;
- checkpoint/resume stores only goal text/status, not plan/proof/remaining work;
- dynamic workflow code is test-covered in isolation but unreachable from the live goal/taskpool path.

### Roles Need Protocol Files

When a skill defines a role (P10, P9, P7), the role's behavioral protocol should be in a separate reference file, not buried in SKILL.md. This allows:
- Multiple skills to reference the same protocol
- Protocol updates without changing all skills
- Clear separation of "what to do" (SKILL.md) vs "how to behave" (protocol)

## Definition of Done

- [ ] **Outcome**: All workflow stages mapped to skills, broken references fixed, missing skills created, terminal report generated
- [ ] **Process**: Enumerate → Load & check → Map → Identify gaps → Create → Report
- [ ] **Style**: Report uses Unicode box-drawing characters, includes role hierarchy diagram, trigger word table, deliverable checklist
- [ ] **Efficiency**: Don't over-engineer — if a stage is intentionally uncovered (e.g., "数据库变更" for a frontend-only project), mark it as N/A rather than creating an unnecessary skill
- [ ] Pipeline control: each stage has an explicit gate before the workflow advances.
## Routing-Surface and Graph-Risk Audit

When auditing a skill ecosystem, do not stop at file existence or stage coverage. Skill descriptions, linked files, and adjacent trigger boundaries form a routing surface, so any new skill or description edit can create graph-level regressions.

For every changed or proposed skill, check:
- Which prompts should load this skill
- Which nearby prompts should load a neighbor skill instead
- Which prompts must not load this skill at all
- Which requests should remain no-skill/no-load

Mark the graph risk explicitly:
- Low: trigger boundary unchanged; only local wording clarified
- Medium: trigger widened/narrowed but neighbor boundaries still tested
- High: description, linked files, or umbrella relationships changed without regression evidence

Also audit progressive-loading pressure:
- Does the skill rely on linked files that are effectively always-read?
- Should some guidance move up into SKILL.md because it is no longer accessory?
- Are multiple sibling skills carrying duplicated references that should be normalized into a higher-level umbrella or shared support file?

A workflow audit report should call out routing regressions as first-class findings, not bury them under style or documentation issues.

## Common Pitfalls
1. **Assuming linked_files exist** — Always verify with `ls` or `read_file` before relying on referenced content
2. **Creating skills for project-specific gaps** — Some gaps (e.g., database migration flow) are project-specific, not generalizable. Only create skills for reusable patterns
3. **Overwriting existing content** — When fixing broken references, check if the referenced file was intentionally removed. Don't recreate deleted content without understanding why
4. **Terminal report too long** — Keep the report concise. If it exceeds 200 lines, split into sections and let the user ask for details

## Verification Checklist

- [ ] The task actually matches this skill's trigger class and the current route is still appropriate.
- [ ] All prerequisites, linked references, templates, scripts, and required tools have been checked before execution.
- [ ] The Definition of Done items above were explicitly checked, not assumed.
- [ ] Claimed outputs, commands, files, or external side-effects were read back or otherwise verified before completion.
- [ ] The audit distinguishes coverage gaps from routing-surface regressions.
- [ ] Any changed skill includes positive / neighbor / forbidden / no-load examples or an explicit note that this evidence is still missing.
- [ ] Linked files and accessory references were checked for progressive-loading pressure, not just existence.
