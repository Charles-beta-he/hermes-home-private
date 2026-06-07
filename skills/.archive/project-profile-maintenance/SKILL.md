---
name: project-profile-maintenance
description: "Use when maintain canonical project profiles by recovering historical context, mining prototype/source repos, and writing durable code-grounded navigation maps back into the profile. See references/prototype-source-grounded-admin-correction.md for the correction pattern when prototype source, local admin implementation, and backend truth diverge. See references/prototype-source-vs-implementation-repos.md for the base pattern when prototype source code and local implementation repos diverge (especially admin surfaces), and references/prototype-source-three-repo-domain-maps.md for the deeper three-repo/domain-map/persistence/acceptance pattern."
---

# Project Profile Maintenance

## Overview

Maintain canonical project profiles by recovering historical context, mining prototype/source repos, and writing durable code-grounded navigation maps back into the profile. See references/prototype-source-grounded-admin-correction.md for the correction pattern when prototype source, local admin implementation, and backend truth diverge. See references/prototype-source-vs-implementation-repos.md for the base pattern when prototype source code and local implementation repos diverge (especially admin surfaces), and references/prototype-source-three-repo-domain-maps.md for the deeper three-repo/domain-map/persistence/acceptance pattern. This skill is maintained as a `memory`-shaped contract: it should guide retrieval, durable context selection, notes, or knowledge-management workflows without stealing adjacent workflows or relying on unstated assumptions.

## When to Use

Use this skill when the user's request matches `project-profile-maintenance` and requires retrieval, durable context selection, notes, or knowledge-management workflows.

Do not use it for:
- generic one-off questions that do not need this workflow;
- neighboring specialist workflows with a narrower matching skill;
- durable memory or project-profile writes unless this skill explicitly governs that landing zone.

Use when you need to update a canonical project profile / project memory file after historical work, resume sessions, prototype repo discovery, or codebase archaeology.

## Triggers
- User asks to "更新项目画像", "refresh canonical profile", or restore project context from older sessions.
- You need to reconcile prototype sources, current frontend/backend code, and historical transcripts into one durable profile.
- You need a reusable landing map from product/prototype domains to current implementation files.

## Goals
1. Preserve only durable project facts.
2. Ground every profile addition in code, routes, migrations, or session evidence.
3. Separate stable profile facts from session-specific detail.
4. Produce navigation aids that future sessions can use immediately.

## Workflow
1. Locate the current canonical profile.
   - Check agent-owned profile stores first (for example Hermes project-profiles JSON).
   - Treat the profile as the write target unless the repo docs explicitly say another file is the source of truth.

2. Recover historical evidence before editing.
   - Read the referenced session transcript/log.
   - Extract durable facts only: changed modules, durable UX rules, architecture shifts, route groups, verified data flows, prototype anchors.
   - Ignore transient items: branch state, temporary TODOs, one-off failures, raw credentials, ephemeral timestamps unless they explain profile lineage.

3. Inspect current code to confirm the facts still exist.
   - Frontend: routes, screen directories, services, stores, tests.
   - Backend: controllers first, then imported services/domain/repository anchors, migrations, tests.
   - Prototype/source repos: App.tsx/router declarations, page/screen folders, README/PRD anchors.

4. Add profile data in layers.
   - Durable conventions: UX rules, versioning pipelines, architecture invariants.
   - Prototype anchors: hosted prototypes, source repos, commit/hash when relevant.
   - Navigation index: route groups and file indexes for prototype apps.
   - Domain landing maps: prototype domain -> current frontend -> backend controller anchors.
   - Deep maps for priority domains: prototype -> frontend -> backend -> test/evidence entrypoints.

5. Record lineage.
   - Append a compact profile_update_history entry with date, source repo/session, and truth status.
   - Keep history declarative; do not paste the whole task narrative.

6. Validate the profile.
   - Re-load the JSON/YAML after writing.
   - Sanity-check key sections and counts.

## What belongs in the profile
- Stable route/domain structure.
- Durable frontend/backend landing points.
- Verified integration architecture.
- Canonical prototype/source locations.
- Cross-session UX constraints that affect future implementation.
- Project-specific facts needed by `development-closure-consensus` to compile an executable project closure consensus: repo topology, truth-source order, red lines, validation gates, main business chains, and delivery constraints.

## What does NOT belong in the profile
- Temporary task progress.
- Unverified guesses.
- Secrets/tokens.
- Resolved environment hiccups.
- Large transcript dumps.

## Recommended structures
- `prototype_source_repo`: remote, local clone path, commit, scope.
- `prototype_source_navigation_index`: per app route groups, screen/page indexes, PRD anchors.
- `prototype_business_domain_map`: prototype domain -> current frontend/backend landing points.
- `prototype_business_domain_deep_map_v1`: priority-domain four-layer maps.

## Domain Rule Propagation Pattern

See `references/schema-change-guardrail-propagation-example.md` for a full worked example (uvisa DB migration guardrail).

When a production incident or session analysis reveals a new guardrail/rule, first classify its scope:

- Hermes-wide development/public process consensus → update the appropriate Hermes skill/reference (for example `development-closure-consensus` or `github-pr-workflow`). This includes globally reusable best-fix-point rules learned from a project case, such as choosing the correct implementation layer from the actual repository boundary instead of the nearest visible symptom.
- Project-specific durable rule → update the project profile JSON under `~/.hermes/project-profiles/`.
- Repo-local docs such as `AGENTS.md` are not the default write target. Only update them when the user explicitly asks for repo-contained guidance or the repo docs are declared as the project's source of truth.

### 1. Project profile JSON (`~/.hermes/project-profiles/<project>.json`)
```python
import json
with open("~/.hermes/project-profiles/<project>.json") as f:
    profile = json.load(f)

# Add to conventions (behavioral rules)
profile['conventions'].append("新规则描述...")

# Add to red_flags (blocking guardrails)
profile['red_flags'].append("阻断条件描述...")

with open("~/.hermes/project-profiles/<project>.json", "w") as f:
    json.dump(profile, f, ensure_ascii=False, indent=2)
```

### 2. Repo-local docs (`<project-root>/AGENTS.md`, optional)
Only update repo-local guidance when explicitly requested or when the repository declares it as the canonical project guidance file. Otherwise, keep project-specific durable rules in the Hermes project profile to avoid polluting project repos with assistant-operational consensus.

If explicitly requested, add to the `## Red Lines` section (or equivalent):
```markdown
- 新规则描述（与 profile conventions 对应）
```

**Why profile-first:** Profile JSON is the canonical source for Hermes routing/triage and project-specific execution consensus. Repo docs are shared project artifacts and should not be mutated by default for assistant-only operating rules.

**Example (uvisa 2026-05-16):**
- Incident: `Unknown column 'gsalary_quote_id'` in production → Flyway migration not applied
- Profile convention: "Entity 字段变更必须检查 Flyway migration 存在性 + 确认 prod 已执行"
- Profile red_flag: "Entity 字段变更无对应 migration → 阻断"
- AGENTS.md Red Line: "Entity 类字段新增/重命名/删除时，必须同步检查对应 Flyway migration SQL 文件是否存在..."

## Pitfalls
- Do not stop at prototype routes; always map them to current code.
- Do not stop at backend controllers; capture imported service/domain/repository anchors so later sessions know where to descend.
- Do not mix session-local details into the canonical profile; put them in a reference file instead.
- Do not treat admin prototype routes as current C-end UI features if the active product repo has no matching admin shell.
- Do not claim exhaustiveness without stating the boundary, such as "visible routes in App.tsx" versus dynamic/lazy routes.

## Verification

## Reference add-ons
- `references/uvisa-canonical-profile-mapping.md` — UVISA-derived pattern for recovering Claude resume context, extracting visible prototype routes from `App.tsx`, building domain-to-landing maps, and writing executable profile sections back to the canonical JSON.

 checklist
- Canonical profile file re-parses successfully.
- Every newly-added section points to real files/routes/controllers.
- History entry added.
- Exhaustion boundary stated when claiming broad coverage.
- Session-specific detail moved to a reference file when useful.

## References
- See `references/uvisa-project-profile-refresh.md` for a concrete example of transcript recovery + prototype repo mining + four-layer mapping.
