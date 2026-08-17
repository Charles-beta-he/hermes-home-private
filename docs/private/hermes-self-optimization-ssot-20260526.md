# Hermes self-optimization SSOT — 2026-05-26

Purpose: make "multi-entry single source of truth" a prerequisite for Hermes self-optimization so future changes do not repeat the same claim in chat, taskpool, docs, model-state, and skills with divergent meanings.

This governs Hermes self-optimization work: external reference-repo absorption, multi-model reflection, taskpool evolution, background review, cron-driven audits, skill patches, and core/runtime changes.

## Canonical rule

Before changing Hermes itself, identify or create exactly one canonical SSOT artifact for the optimization. All entrypoints must read or reference that artifact instead of copying facts into parallel local truths.

If no SSOT artifact exists yet, create the smallest durable SSOT first. Do not proceed to model certification, taskpool enqueue, skill patch, or code change from scattered chat/context notes alone.

## What counts as SSOT by work type

| Work type | Canonical SSOT | Derived / non-authoritative views |
|---|---|---|
| Reference-repo self-optimization | `ReferenceReview` evidence pack under `docs/private/` or future structured evidence store: repo URL, commit, claims, file/line evidence, impact classes, decisions | chat summaries, raw `context_json`, model outputs, copied excerpts, task titles |
| Runtime/code self-change | Hermes source checkout diff plus design/verification note when needed | model suggestions, terminal snippets, unstaged scratch files |
| Skill/process update | The changed skill file plus any linked reference doc | final response summary, memory note, taskpool note |
| Taskpool/evolution execution | Task record fields: body/description/acceptance_criteria/red_lines/non_goals/evidence_refs/workflow_contract | worker prompt, dashboard row, kanban list, chat recollection |
| Multi-model certification | `consult_models` state/evidence bundle with explicit `evidence_json` or fulfilled evidence records | raw prompt context, partial planner outputs, consensus text without evidence links |
| Local-brain/project knowledge | Declared project profile / Workpad / brain markdown source for that project | vector DB, dashboard, cache, HTML sidecar |

## Required SSOT schema for reference-repo self-optimization

A reference review must include enough fields to be consumed by chat, taskpool, cron, bg-review, and `consult_models` without restating facts:

```yaml
schema: hermes_reference_review_v1
id: <stable slug, e.g. langgraph-20260526>
source_repo: <url>
source_commit: <sha>
local_checkout: <path>
claims:
  - id: C-001
    text: <factual claim>
    evidence:
      - file: <repo-relative path>
        line_range: [start, end]
        quote_hash: <short hash of quoted text>
        supports: true
impact_classes:
  - docs/skills
  - scripts
  - core agent loop
  - gateway/platform adapters
  - taskpool/brain
  - tests/evidence fixtures
decisions:
  immediate_landing:
    - <low-risk doc/skill/process change>
  blocked_until:
    - <evidence, quorum, approval, migration, or tests required>
  do_not_do:
    - <explicit cargo-cult / safety boundary>
verification:
  read_back:
    - <files/commands used>
  model_certification:
    status: certified|degraded_not_certified|not_run
    tick_dir: <path or null>
```

## Entry-point rules

1. Chat entrypoint
   - Use chat to clarify intent and select/create the SSOT artifact.
   - Do not treat the conversation transcript as the canonical implementation record.
   - Final response must name the SSOT path/id and commit hash if changed.

2. Taskpool entrypoint
   - A task spawned from self-optimization must reference the SSOT id/path in `evidence_refs`.
   - Worker prompts may include a snapshot, but the task record remains the task-local SSOT.
   - If worker findings conflict with SSOT, update/review the SSOT first; do not fork a parallel truth in the worker note.

3. Multi-model entrypoint
   - `consult_models.py state` must receive explicit `--evidence-json` records or consume a fulfilled evidence pack.
   - Raw `context_json` excerpts are context only; they are not truth-gate evidence.
   - Below-min-quorum or unsupported-claim runs can only produce low-risk doc/skill/process landings, not high-blast-radius code changes.

4. Skill/docs entrypoint
   - Skills encode reusable procedure, not one-off run status.
   - Private review docs encode the detailed evidence and decision record.
   - If a skill and private doc disagree, the private evidence doc controls facts; the skill controls future procedure. Patch whichever is stale before proceeding.

5. Runtime/code entrypoint
   - For code changes, the git diff and tests are the implementation SSOT.
   - Reference-review/model output can justify a direction but cannot substitute for code evidence and verification.

6. Cron/bg-review entrypoint
   - Background jobs should emit candidates pointing at the SSOT, not silently mutate skills/code from copied summaries.
   - If the SSOT cannot be found or is stale, fail closed and ask/queue for review.

## Accepted minimal cross-session and multi-agent coordination model

Status: accepted by the user on 2026-08-17.

The coordination problem is limited to two required outcomes:

1. A new session can resolve the current work object and effective decision source.
2. Concurrent agents do not silently write the same surface from different baselines.

Do not build a second all-purpose shared-memory or control-plane database for this. Reuse existing authorities and add only three scoped records when needed:

### 1. Scope Manifest

Identifies the work object without duplicating task progress:

```yaml
scope_id: <stable id>
scope_type: project|system
canonical_root: <real path>
ssot: <canonical decision/spec path>
repo: <canonical repository path or null>
activation_surface: <runtime surface or null>
```

- `scope_type: project` covers ordinary project delivery.
- `scope_type: system` covers Hermes self-update surfaces such as core, skills, plugins, config, gateway, cron, taskpool, profiles, and runtime activation.
- Portfolio views are derived queries over scope manifests, not another registry.

### 2. Work Claim

The canonical task/taskpool record owns mutable coordination state:

```yaml
task_id: <id>
scope_id: <scope id>
owner: <single writer>
base_commit: <sha or null>
allowed_paths: [<bounded paths>]
lease_expires_at: <timestamp or null>
```

- One write surface has one writer at a time; reviewers and other agents remain read-only on overlapping paths.
- Claims are lease-bound rather than permanent locks.
- A changed base commit, SSOT digest, owner, or overlapping claim requires fresh readback before work continues.
- Agents and sessions do not inherit another actor's authority merely because they can read the claim.

### 3. Completion Receipt

Binds a result to the exact candidate and verification evidence:

```yaml
task_id: <id>
candidate_commit: <sha or null>
ssot_digest: <sha256>
verification:
  - command: <executed command>
    result: <observed result>
runtime_activation: not_attempted|staged|active|rolled_back
```

For Hermes runtime activation, also bind the previous runtime, requested candidate, fresh actual-runtime readback, and rollback reference. A validated source candidate is not an activated runtime.

### Existing authority map

Each fact has one canonical authority:

| Fact | Canonical authority |
|---|---|
| Project direction and accepted decisions | Project/optimization SSOT document |
| Source and candidate state | Git |
| Task status, owner, lease, and write boundary | Taskpool/task record |
| Current Hermes runtime | Fresh process, realpath, version, config, and health probes |
| Historical execution evidence | Completion receipt; durable ledger only for complex/long/multi-agent runs |
| Long-term mission and human decision gates | Mission only when the work requires durable autonomous continuation |
| Historical conversation | Session history/search, as secondary context |
| Stable user preference or environment fact | Persistent memory |

Derived views must identify their source, observation time, and source digest where applicable. They must not become independent write authorities.

### Required preflight and convergence

Before a session or agent writes:

1. Resolve `scope_id` and canonical real paths.
2. Read the named SSOT.
3. Probe fresh Git and, for `system` scope, actual runtime state.
4. Check owner, lease, base commit, and path overlap.
5. Return exactly one coordination result: `PROCEED`, `READ_ONLY_CONFLICT`, or `REBASE_REQUIRED`.

At completion, release the claim only after the candidate and verification receipt are read back. Integration remains single-owner and serial even when candidate production is parallel.

### Explicit non-goals

- No global shared "agent brain" containing WIP.
- No second portfolio/project/task/runtime database that mirrors existing authorities.
- No persistent PID or runtime YAML treated as current truth; activation receipts are historical evidence only.
- No mandatory durable run, Mission, event log, or multi-model round for ordinary scoped work.
- No synchronization of private chain-of-thought or wholesale conversation transcripts.
- No automatic runtime activation, push, deploy, external delivery, or authority inheritance.

Expansion beyond this model requires concrete recurring conflict evidence and should proceed incrementally: scope identity, then path-level claims, then activation receipts, and only then a derived projection if query cost justifies it.

## Fail-closed checks

Before claiming self-optimization is complete, answer yes to all applicable checks:

- Is there exactly one canonical SSOT path/id named in the report?
- Are claims linked to file/line evidence or explicit user statements?
- Are taskpool/model/skill/docs outputs references to the SSOT rather than independent copies?
- Did model certification consume the evidence bundle, not just chat context?
- Are degraded/not-certified model runs labeled honestly?
- Did the landing avoid changing high-blast-radius runtime behavior unless the SSOT and tests support it?
- Was the scoped Hermes change committed with only the intended files staged?

## Anti-patterns this prevents

- Same requirement exists in chat, taskpool body, worker prompt, and skill text with slightly different meanings.
- Multi-model reviewers reject because claims are unsupported even though evidence was pasted into context.
- A skill patch encodes a one-off conclusion while the evidence doc says a different boundary.
- A taskpool worker closes or mutates work from a dashboard row without reading task-local acceptance/red-lines/evidence_refs.
- A reference repo inspires a runtime rewrite without a claim/evidence/impact-class map.

## Relationship to existing Hermes practices

- Extends the LangGraph reference review lesson: evidence first, models second, low-risk landing only when degraded.
- Aligns with taskpool chat-rule convergence: task records carry task-local SSOT snapshots for workers.
- Aligns with local-brain governance: dashboards, vector stores, and caches are derived; canonical markdown/profile/workpad remains authoritative unless explicitly changed.

Short rule: self-optimization starts by naming the SSOT, not by copying facts into a new entrypoint.
