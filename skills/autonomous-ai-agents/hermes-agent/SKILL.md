---
name: hermes-agent
description: Use when extending or operating Hermes Agent including CLI/setup, skills, tools, profiles, gateway, taskpool hooks, certified auto-done, blocked-task closure, memory-cap selfcheck, and self-evolution / PUA-loop workflows. See references/ for taskpool hook debugging, evolution-task add rules, pre-ingest triage, memory compaction, bad-case to proposal to benchmark self-optimization, `references/budget-handoff-automation.md` for default-safe budget/context exhaustion behavior, `references/budget-relay-debugging.md` for delegated continuation / relay pitfalls, and other Hermes-specific deep dives.
---

Reference addendum: `references/agent-team-failfast-model-fallback.md` captures multi-model fallback chain (GPT-5.5→Claude→MiMo), infrastructure error detection (SDK crash, MCP loop, client closed, auth/quota), workspace sync barrier, and trace events for `agent_team_controller.py` parallel workers.

Reference addendum: `references/provider-version-drift-and-codex-breaker.md` captures the workflow for separating Hermes runtime package skew from local source drift when provider/version mismatch or `agent.codex_circuit_breaker` incidents appear.

Reference addendum: `references/dreaming-outcomes-skill-review-and-evaluator.md` maps Dreaming-style post-run procedure distillation and Outcomes-style independent evaluator gates into Hermes skill review, memory hygiene, taskpool proof logs, and fail-closed lifecycle advancement.

Reference addendum: `references/yd-ai-wf-stop-hook-auto-review.md` captures the user-provided yd-ai-wf + Stop Hook pattern: workflow init/planning/parallel specialist agents, per-task code review, P0-only auto-fix loop, AGENTS.md self-learning, and a bounded stop-time dirty-worktree review hook that fails open on infrastructure errors.

Reference addendum: `references/external-skill-to-brain-overlay.md` captures the governed workflow for absorbing an external Agent Skills package into Hermes as a discoverable brain overlay with registry routing, skill discovery, diagnostics, taskpool evidence, and fail-closed review/done handling.

Reference addendum: `references/rokid-lingzhu-sse-bridge.md` captures the workflow for exposing Hermes to Rokid smart glasses through the Rokid Rizon/Lingzhu custom third-party agent SSE protocol, including FastAPI bridge shape, Cloudflare temporary/named tunnel handling, macOS LaunchAgent recovery, Rizon custom-agent API fallback, and verification gates.

Reference addendum: `/Users/charles/.hermes/docs/private/vercel-reference-self-optimization-20260526.md` captures the Vercel monorepo review pattern for Hermes self-optimization: first-class `AGENTS.md`, named validation surfaces, affected-check fail-safe broadening, fixture/evidence protection, release/evidence notes, and reference-repo analysis without cargo-culting the source stack.

Reference addendum: `/Users/charles/.hermes/docs/private/hermes-self-optimization-ssot-20260526.md` is the canonical multi-entry SSOT rule for Hermes self-optimization. Before changing Hermes itself through chat, taskpool, cron/bg-review, multi-model certification, skill patches, or code edits, identify/create exactly one SSOT artifact and make all derived entrypoints reference it rather than copying parallel facts.

Reference addendum: `references/event-governed-agent-control-plane.md` captures the Hermes-owned Event-Governed Agent Control Plane pattern. Scope: Hermes Agent self-architecture only. Applicability: lifecycle control, worker permission, gateway/cron ingress, Control Tower, persistent learning, and external side-effect governance. Anti-condition: ordinary Q&A/read-only/simple project work should not inherit this heavy control-plane flow. Key invariant: workers submit evidence/proposals instead of directly mutating lifecycle.

Reference addendum: Hermes mission control plane (`hermes mission ...`) is the default-off scaffold for high-abstract directions that should advance over time: create budget-bound missions, install dynamic agent cron ticks with `hermes mission install-cron`, record durable evidence via `hermes mission stage-report`, create human gates via `hermes mission handoff`, review waiting decisions with `hermes mission inbox`, inspect portfolio state with `hermes mission board`, verify runtime readiness with `hermes mission doctor`, block on open decision packets, and report from the mission ledger. Mission advancement is event-primary: actionable mission/taskpool events enqueue `mission_flow_signals`, `hermes mission signals <id>` shows pending signals, `hermes mission dispatch-events <id>` schedules the installed cron job for immediate pickup, `hermes mission dispatch-events <id> --run-due` explicitly runs the governed cron scheduler once for manual/test close-the-loop recovery, and ordinary cadence remains a maintenance/watchdog path. `stage_report` is durable read-back evidence only, not an actionable wake signal, because cron agents are required to write stage reports and otherwise self-trigger indefinitely. Relevant Hermes self-architecture taskpool events are bridged by `brain_task_orchestrator.py` into `taskpool_status_changed` mission events, fail-soft and local-ledger only. Control Tower exposes `mission_flow_signals` and `mission_taskpool_bridge` as read-only operator projections; the dashboard `Mission event flow` panel renders signal counts, stale age, consumed latency, and recent bridge events without becoming a lifecycle/executor owner. Use Mission as objective/ledger/human-gate scaffolding, not as an unrestricted executor.

Reference addendum: Mission blockage auto-recovery pattern. When a self-advancing Mission is active, has no open human decision, and is blocked by exhausted tick budget or stale/pending flow signals, the expected automation is: (1) close out the current local diff/slice first with focused verification and scoped commit when code changed; (2) run multi-model review to decide continue/stop and bounded tick count; (3) auto-authorize only the selected local mission budget extension when the user has granted that authority, recording a `budget_authorized`/stage-report ledger event; (4) wake the executor via `hermes mission dispatch-events <id> --run-due`; (5) read back board/doctor/report/git status. Authority remains bounded: no push, deploy, secret, destructive delete, external delivery, payment, or production side effect; weak or not-certified model discussion may still support a bounded continuation only when all model recommendations agree on continue and dissent is only tick count, with the risk recorded. Default bounded-tick ceiling: a mission may auto-extend through this loop only up to total `max_ticks=60` for one explicit authorization interval unless the user grants a different ceiling. At or beyond 60, stop on a human authorization packet that offers concrete next authority tiers, such as another bounded tick ceiling, taskpool-ingestion/implementation automation, or external/publish authority. If older notes mention 30, treat them as superseded by the user's June 12 correction that one maximum authorization interval should be 60 ticks.

# Hermes Agent

## Overview

Use when extending or operating Hermes Agent including CLI/setup, skills, tools, profiles, gateway, taskpool hooks, certified auto-done, blocked-task closure, memory-cap selfcheck, and self-evolution / PUA-loop workflows. See references/ for taskpool hook debugging, evolution-task add rules, pre-ingest triage, memory compaction, bad-case to proposal to benchmark self-optimization, `references/budget-handoff-automation.md` for default-safe budget/context exhaustion behavior, `references/budget-relay-debugging.md` for delegated continuation / relay pitfalls, and other Hermes-specific deep dives. It is organized as a gated workflow: advance through explicit stages, preserve evidence at each boundary, and leave neighboring domains to their own skills.

## When to Use

Use this skill when the request matches the `hermes-agent` trigger and the domain-specific boundaries in this skill apply.

Do not use it for:
- generic one-off questions that do not need this workflow;
- neighboring specialist workflows with a narrower matching skill;
- durable memory or project-profile writes unless this skill explicitly governs that landing zone.

Use this skill when operating or extending Hermes Agent itself: CLI behavior, setup, update/upgrade workflows, built-in tools, memory system, gateway/taskpool hooks, self-evolution loops, certified auto-done, and related local-control-plane hardening.

## Triggers

Use this skill when the user asks to:
- inspect, update, repair, or self-check Hermes itself
- modify Hermes core code, skills, hooks, memory, gateway, or taskpool behavior
- troubleshoot Hermes-specific regressions after upstream pulls or self-updates
- run Hermes-local benchmarking, post-update validation, or self-evolution workflows

## Absorbed Hermes operations lanes

These former narrow Hermes skills are now references under this umbrella. Load only the relevant reference after the request is known to be Hermes-specific:

- `references/hermes-tool-availability.md` — diagnose or repair Hermes `hermes doctor` Tool Availability warnings, system dependency prompts, and tool readiness drift.
- `references/hermes-voice-console-integration.md` — integrate or troubleshoot Hermes voice conversation, custom TTS providers, desktop notification sounds, and console audio UX.

Applicability: Hermes Agent setup/operation/extension work. Anti-condition: do not use these lanes for generic OS audio, non-Hermes dependency checks, or unrelated app troubleshooting.

## Conductor / async multi-model orchestration

When adding Sakana/Fugu/Conductor-inspired behavior to Hermes, use the default-off scaffold pattern in `references/hermes-conductor-runtime-scaffold.md`: land isolated router calls, durable task ledger, optional Fugu fail-soft adapter, model profile placeholders, and post-update regression before mainline conversation-loop wiring. Critical invariant: a default-main-model bootstrap/router call never counts as a later planner/implementer/arbiter participant. For the evidence-based Sakana pattern and model profile sketches, see `references/sakana-conductor-pattern.md`.

## Self-optimization SSOT prerequisite

Before any Hermes self-optimization landing, use `/Users/charles/.hermes/docs/private/hermes-self-optimization-ssot-20260526.md` as the controlling rule:

1. Identify or create exactly one canonical SSOT artifact for the change before model certification, taskpool enqueue, skill patch, or code edit.
2. Make every entrypoint reference that SSOT instead of copying facts into parallel truths: chat, taskpool, cron/bg-review, gateway, `consult_models`, docs, skills, and git/code diffs.
3. For reference-repo reviews, the SSOT is a `ReferenceReview`/evidence pack with repo URL, commit, claims, file/line evidence, impact classes, decisions, and verification.
4. For taskpool execution, task record fields (`body`, `description`, `acceptance_criteria`, `red_lines`, `non_goals`, `evidence_refs`, `workflow_contract`) are the task-local SSOT; worker prompts and dashboard rows are derived snapshots.
5. If an entrypoint discovers conflicting facts, update/review the SSOT first; do not fork a second truth in memory, skill text, task notes, or model state.
6. If no SSOT can be named, fail closed and land only the smallest SSOT document/evidence pack first.

## Reference-repo self-optimization workflow

When a user asks to analyze an external repository to improve Hermes itself, first apply the SSOT prerequisite above, then use the Vercel-derived pattern in `/Users/charles/.hermes/docs/private/vercel-reference-self-optimization-20260526.md` and the LangGraph-derived evidence-gating addendum in `/Users/charles/.hermes/docs/private/langgraph-reference-self-optimization-20260526.md`:

1. Clone/read the reference repo under `~/.hermes/runs/`.
2. Read `AGENTS.md`/`CLAUDE.md`, README, package manifests, build/test config, and fixture/error/skill directories before drawing conclusions.
3. Create/update the reference-review SSOT artifact with source repo, commit, claims, evidence links, impact classes, decisions, and verification; all later chat/taskpool/model/docs outputs must reference this artifact.
4. Extract explicit claim-linked evidence before asking models to certify conclusions. If using `consult_models.py state`, pass `--evidence-json` records with source file/line references or run `consult_models.py fulfill-evidence` before `run --discussion`; raw excerpts inside `context_json` are not enough for the truth gate.
5. Separate transferable governance patterns from stack-specific implementation details.
6. Map findings to Hermes impact classes: docs/skills, scripts, core agent loop, gateway/platform adapters, taskpool/brain, or tests/evidence fixtures.
7. If multi-model fanout drops below `min_quorum` or truth gating reports unsupported claims, report degraded/not-certified and land only low-risk docs/skills/process improvements; do not claim architecture certification or make high-blast-radius code changes from that run.
8. Implement only scoped, low-risk self-optimizations immediately unless the user explicitly asks for a larger code change.
9. Validate by the changed impact class, then make a scoped local commit and report the commit hash plus SSOT path/id.

## Core workflow

1. Identify the target object first.
   - If the user explicitly names Hermes (for example, "Hermes自检更新"), operate on the local Hermes installation/repo.
   - If the user uses a short verb like “自检 / 更新 / 同步” without an object, default to assistant-self clarification/correction behavior rather than expanding into project-level repo actions.
2. Inspect current state before acting.
   - `hermes --version`
   - `git -C ~/.hermes/hermes-agent status --short --branch`
   - `git -C ~/.hermes/hermes-agent remote -v`
3. For self-update, prefer:
   - `hermes update --backup --yes`
4. Immediately run update validation/repair:
   - Prefer the Hermes repo venv Python so modern type syntax in local scripts does not fail on an older system `python3`:
     - `~/.hermes/hermes-agent/venv/bin/python ~/.hermes/scripts/post-update-check.py --fix`
   - Fallback only if needed: `python3 ~/.hermes/scripts/post-update-check.py --fix`
5. Re-verify after update:
   - `hermes --version`
   - `git -C ~/.hermes/hermes-agent status --short --branch`
   - `git -C ~/.hermes/hermes-agent log --oneline -1`
   - `git -C ~/.hermes/hermes-agent stash list --max-count=5`
6. Report both success and leftovers.
   - version change / up-to-date state
   - whether worktree is still dirty
   - whether autostash remains
   - whether any post-update guard still shows `FIX_FAILED`

## Pitfalls

Detailed `Pitfalls` guidance moved to `references/pitfalls.md`.

Load it when this subproblem is directly active. Minimum in-root rule: preserve the current skill's safety/verification boundaries and read the reference before executing this specialized branch.
## Gemini CLI / OAuth provider wiring

Detailed `Gemini CLI / OAuth provider wiring` guidance moved to `references/gemini-cli-oauth-provider-wiring.md`.

Load it when this subproblem is directly active. Minimum in-root rule: preserve the current skill's safety/verification boundaries and read the reference before executing this specialized branch.
## Runtime friction capture and consult_models prompt files

When a Hermes runtime/CLI problem is encountered while operating Hermes itself (unsupported flag, hook parse failure, provider/router friction, taskpool event-hook error), do not save it as memory or leave it only in chat. Capture it as evidence-backed work:

1. For long multi-model prompts, use `python3 ~/.hermes/scripts/consult_models.py state --prompt-file <utf8-prompt.txt> --out <state.json>` instead of shell-substituting `$(cat file)`.
2. If the runtime issue is a candidate for future repair, record it with `python3 ~/.hermes/scripts/runtime_issue_capture.py --mode suggest --source-command ... --error-excerpt ... --impact ... --expected-behavior ...`.
3. Use `--mode enqueue` only when the issue is deduped, redacted, has reproduction/evidence, and should become a governed taskpool item. Default `suggest` is safe and append-only.
4. Never auto-close runtime issue candidates; they need normal implementation evidence and verification.

## Verification

- Confirm the Hermes version again after update.
- Confirm the repo branch/upstream and whether local modifications remain.
- Confirm whether `git stash list` contains a fresh `hermes-update-autostash-*` entry.
- Read the post-update-check summary and call out every non-OK item explicitly.

## References

Detailed `References` guidance moved to `references/references.md`.

Load it only when this specialized branch is directly active; preserve root safety and verification rules.
## Related umbrella skills

- `software-development` — general development workflow and verification discipline
- `devops` — infrastructure/deploy operations that are not Hermes-specific
## Common Pitfalls

1. Applying this skill mechanically after the user's goal has shifted. Re-check the current request before acting.
2. Treating a plan, stale memory, or prior report as proof of completion. Verify with fresh readback.
3. Ignoring neighboring skills or narrower workflows that better match the task. Prefer the most specific applicable skill.
## Verification Checklist

- [ ] The current user request still matches this skill's trigger class.
- [ ] Required files, tools, commands, or external state were checked before action.
- [ ] Outputs, edits, or side effects were verified by readback or direct inspection.
- [ ] Boundaries, unresolved assumptions, and any deferred work were stated clearly.
