# LazyCodex / OmO complex-task harness absorption

Scope: Hermes self-architecture, workflow-control-plane, and external agent-workflow absorption.

Applicability: use when the user asks Hermes to learn from LazyCodex, OmO, Codex/OpenCode harnesses, or similar public agent workflows and then “directly advance”, “全盘推进”, “落地”, or otherwise improve Hermes beyond a report.

Anti-condition: do not use this for simple Q&A, one-line edits, or ordinary project work where no reusable workflow/control-plane learning is being landed.

Canonical source note: `/Users/charles/.hermes/docs/private/lazycodex-omo-reference-self-optimization-20260702.md`.

## Iceberg complexity scan first

Before action, classify whether the request is simple or complex.

Above-water triggers:

- external reference repo/video/workflow is being absorbed;
- target is Hermes self-optimization, workflow/control plane, taskpool, skills, hooks, or autonomous execution;
- user asks to “directly advance”, “全盘推进”, “落地”, “生产级”, or “learn and apply”;
- multiple landing zones are plausible: memory, skill, docs/private SSOT, experience-ratchet, taskpool, core code, runtime gate;
- the result could create durable rules or future autonomous behavior.

Submerged triggers:

- authority or side-effect ambiguity;
- risk of cargo-culting third-party mechanics;
- distinction between marketing claims and source evidence matters;
- claim of completion would need real command/file/UI/API/log evidence;
- a wrong abstraction could pollute global memory/skills or widen Hermes core.

Classification:

- If 0-1 above-water trigger and no submerged trigger: simple. Do the minimal answer/action; do not start the heavy harness.
- If 2+ above-water triggers or any submerged trigger: complex. Use objective-model/path gate and create or identify an SSOT before durable writes.
- If the only missing piece is a user preference that changes authority, ask one focused question; otherwise proceed with the safest reversible default.

## Transferable LazyCodex pattern

Transfer relationships, not entity names:

1. Project memory: LazyCodex `$init-deep` uses hierarchical AGENTS context; Hermes equivalent is scoped project/profile/AGENTS/SSOT context, not global memory dumping.
2. Plan before execution: `$ulw-plan` is decision-complete planning and does not write product code; Hermes equivalent is a bounded plan artifact or taskpool card before implementation authority.
3. Durable execution: `$start-work` uses Boulder/ledger state; Hermes equivalent is taskpool/mission/SSOT/evidence ledger, not chat-only TODOs.
4. Evidence-bound loop: `$ulw-loop` treats DONE as a claim until Oracle/verifier confirms with observable evidence; Hermes equivalent is completion-claim gate plus criterion-level evidence.
5. Manual-QA surfaces: HTTP, tmux, browser, computer-use, CLI stdout, DB diff, or parsed config dump are first-class evidence; tests alone do not prove user-facing completion.
6. Worker claim isolation: subagent DoneClaim is not proof; parent/root must read back diff/artifacts and independent verifier must confirm.
7. Cleanup receipt: runtime resources spawned for QA must be torn down before PASS is recorded.
8. Final gate: significant work needs final verification, review/debugging gate, and redacted evidence before done/PR/handoff.

## Hermes landing ladder

Use the smallest safe rung first:

1. Evidence note / SSOT under `docs/private/`.
2. Skill reference or skill patch with scope, applicability, anti-conditions, falsifiers.
3. Experience-ratchet atom/proposal if the pattern needs repeated validation.
4. Taskpool/mission candidate for future implementation.
5. Local-only script/CLI scaffold with no external side effects.
6. Default-off runtime gate or hook.
7. External adapter/write/publish/deploy only with exact target, rollback, receipt, and readback.

Do not jump from reference analysis to core loop mutation, cron worker writes, external dispatch, or plugin installation.

## Evidence checklist

For every claimed transfer, record:

- source repo URL + commit;
- source file/line evidence;
- target Hermes landing zone;
- side-effect class;
- what was actually changed;
- verification command/readback;
- what remains unproven.

## Pitfalls

1. Treating LazyCodex as the full OmO Ultimate harness. Source docs say LazyCodex is a light Codex port focused on Hephaestus/workflows.
2. Importing Codex/OpenCode hooks or role names into Hermes instead of extracting the governing relationship.
3. Claiming runtime capability from docs/skill landing.
4. Saving active task progress or reference-specific paths to global memory.
5. Letting “directly advance” bypass the iceberg complexity scan or authority gates.
6. Using tests-only evidence for a user-facing claim.

## Verification

After landing this pattern, read back:

- the SSOT note path;
- this reference file;
- any patched skill root that points to it;
- git/status or file diff for the scoped changes.
