---
name: hermes-agent
description: Use when extending or operating Hermes Agent including CLI/setup, skills, tools, profiles, gateway, taskpool hooks, certified auto-done, blocked-task closure, memory-cap selfcheck, and self-evolution / PUA-loop workflows. See references/ for taskpool hook debugging, evolution-task add rules, pre-ingest triage, memory compaction, bad-case to proposal to benchmark self-optimization, `references/budget-handoff-automation.md` for default-safe budget/context exhaustion behavior, `references/budget-relay-debugging.md` for delegated continuation / relay pitfalls, and other Hermes-specific deep dives.
---

Reference addendum: `references/agent-team-failfast-model-fallback.md` captures multi-model fallback chain (GPT-5.5→Claude→MiMo), infrastructure error detection (SDK crash, MCP loop, client closed, auth/quota), workspace sync barrier, and trace events for `agent_team_controller.py` parallel workers.

Reference addendum: `references/provider-version-drift-and-codex-breaker.md` captures the workflow for separating Hermes runtime package skew from local source drift when provider/version mismatch or `agent.codex_circuit_breaker` incidents appear.

Reference addendum: `references/dreaming-outcomes-skill-review-and-evaluator.md` maps Dreaming-style post-run procedure distillation and Outcomes-style independent evaluator gates into Hermes skill review, memory hygiene, taskpool proof logs, and fail-closed lifecycle advancement.

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

- `hermes update` (git pull) overwrites vendor patches — use `post-update-check.py --fix` to detect and reapply.
- Brain task file status changes may be reverted by `dashboard --write` if multimodel state files still have FAIL — update both brain file AND kanban.db.
- Adding evolution tasks can trigger advisory/multimodel hooks that advance newly created tasks to `review`/`done` even though the user only asked to enqueue future work. After batch-adding taskpool items, verify their actual statuses and explicitly transition them back to `pending` when they are queued work, not completed implementation. Use evidence with an accepted prefix such as `command:` when calling `transition`; free-form evidence strings are rejected.
- Long `brain_task_orchestrator.py add` calls may time out while still creating the task file and firing hooks. Before retrying or declaring failure, search/read the taskpool for the expected titles and reconcile status; avoid duplicate task creation.
- `build_environment_hints()` contains dynamic CWD — MUST be in `context_parts`, NOT `stable_parts` (breaks prefix cache).
- Evolution lane certification deadloop: retry_count >= 2 triggers loop_non_convergence too aggressively. See `references/evolution-lane-cert-loop.md`.
- Taskpool multi-model fan-out must not run as a long synchronous tick/hook step. Use `multimodel-intervention-step --background` (or dispatch tick `--multimodel-step` without `--multimodel-foreground`) so T2/T3 consult_models fan-out is represented by a durable async job under `~/.hermes/state/taskpool-multimodel/jobs/`, with logs under `~/.hermes/logs/taskpool-multimodel/`. Check `multimodel-intervention-jobs --json` before retrying to avoid duplicate certification on the same task.
- Taskpool ordinary parallel worker execution must also avoid long synchronous tick waits. Default `brain_task_dispatch_tick.py --parallel-autorun` should start `agent_team_controller.py consume-claimed --background`, record durable worker jobs under `~/.hermes/state/taskpool-workers/jobs/`, and return quickly; use `--parallel-worker-foreground` only for manual debugging. Check `agent_team_controller.py worker-jobs` before retrying to avoid duplicate claimed-batch execution.
- Convergence subtasks don't auto-trigger parent ratification — must manually unblock parent after children are done.
- ContinuationPacket / auto-relay is recursive — keep max_relay_count <= 3 to avoid deep stack, and treat both `budget_exhausted` and `max_iterations_reached(...)` as relay-eligible exit reasons.
- Dashboard `active_count` only shows evolution lane tasks with multimodel scores, not all kanban ready tasks.
- For taskpool concurrency complaints, check `dispatchable` and `parallel_dispatch.selected_count` before tuning `max_parallel_agents`; zero dispatchable tasks means parallelism has nothing to execute.
- `post-update-check.py --fix` can exit 0 while still reporting a specific guard as `FIX_FAILED`; read the summary instead of trusting exit code alone.
- `post-update-check.py` includes `private_repo_governance`: verify `origin` remains the private Hermes repo, `upstream` remains official, `docs/private/` governance docs exist, and no `state.db` / source-local `.hermes/` runtime state leaks back into the code checkout.
- When vendor/local hardening patches are expected, run `post-update-check.py --fix` after every self-update before declaring Hermes healthy.
- Cron runtime provider/model resolution must share `hermes_cli.config.load_config()` normalization, not a parallel `yaml.safe_load(config.yaml)` path. Otherwise legacy-but-supported shapes like `model: {model: ...}` and root-level `provider:` / `base_url:` fallbacks diverge from CLI behavior. Preserve the existing no-stale-env invariant: do not pass `HERMES_INFERENCE_PROVIDER` as `requested` for unpinned cron jobs; pass `target_model` separately when the provider resolver needs model-specific API mode.
- For "cron job / daily report / scheduled message did not send" incidents, do not stop at `cronjob list`. Also inspect scheduler logs for `missed its scheduled time` and `Fast-forwarding to next run`; if Hermes or the gateway was offline past the job's grace window, the scheduler will skip the missed fire and jump to the next schedule.
- Historical `deliver=origin` warnings are not automatically the root cause of a current missed report. Verify the job's current `deliver` target and correlate with process start times plus the missed-run log line before concluding it is a routing problem.
- For "conversation ended but async/background work did not happen" incidents, split the mechanism first: background process notification, main-task continuation/relay, or background memory/skill review. Do not infer continuation from config names alone; verify code paths and logs. For bg-review specifically, look for `thread=bg-review`, the review prompt turn, successful/failed `skill_manage`/`memory` tool calls, and missing `Turn ended`/`agent_close` before concluding. See `references/background-review-async-debugging.md`.
- For Codex/OpenAI HTTP 400 `image data ... does not represent a valid image`, inspect `agent/image_routing.py` native attachment path before blaming provider auth/model. Native image parts are only safe for real JPEG/PNG/GIF/WEBP bytes; corrupt files or unsupported formats (BMP/TIFF/HEIC/SVG/ICO) must be skipped/fallback-texted instead of filename-guessed into `data:image/jpeg`.
- For bg-review taskpool integration, distinguish safe candidate extraction from side effects: `background_review.taskpool.mode: suggest` only records candidates in status/HTML, while `mode: enqueue` mutates the taskpool. See `references/background-review-taskpool-suggest-mode.md`.
- For bg-review summary regressions, remember the review agent inherits the parent conversation snapshot. Both successful action summaries and failed tool-result summaries must skip tool messages already present in `messages_snapshot` by `tool_call_id`/content; otherwise resolved main-turn tool failures can be re-announced as false `Self-improvement review failed` notifications.
- MCP server `args` containing `~` (tilde) are NOT expanded by the MCP launcher. The path `~/.hermes/scripts/foo.py` resolves relative to the hermes-agent venv directory (e.g. `/Users/charles/.hermes/hermes-agent/~/.hermes/scripts/foo.py`) instead of the user home. Always use absolute paths in MCP server `args` (e.g. `/Users/charles/.hermes/scripts/foo.py`). The error manifests as repeated `can't open file ... No such file or directory` in `~/.hermes/logs/mcp-stderr.log`, causing every worker that loads MCP to waste 7s × 3 retries on connection failure. Check with `grep '~' ~/.hermes/config.yaml` in the `mcp_servers` section.
- Gateway config smoke tests should use the real `GatewayConfig` shape: `config.platforms` is keyed by `Platform` enum values (e.g. `Platform.TELEGRAM`), and `TELEGRAM_BOT_TOKEN` env override populates `PlatformConfig.token`, not a string-keyed `platforms['telegram']` entry or `.bot_token`. When adding profile-level secret scanners, avoid internal variable names like `secret = ...` in staged code because the existing `uvisa_lark_git_guard.py` may flag secret-like assignments even when values are computed/redacted.
- Agent team controller (`agent_team_controller.py`) multi-model fallback: for codegen tasks, the fallback chain is GPT-5.5(openai-codex) → Claude Sonnet(anthropic) → MiMo(xiaomi). Each attempt must detect infrastructure failures (SDK null response crash, MCP connection loops, OpenAI client closed, auth/quota errors) and fail-fast to the next model instead of burning the 600s timeout. See `references/agent-team-failfast-model-fallback.md` for detection patterns and trace events.

## Gemini CLI / OAuth provider wiring

When the user asks to connect Gemini to Hermes because they already subscribed in the browser, do not assume a fresh login is required.

1. Check whether Hermes already has a reusable Gemini OAuth session before changing config.
   - Run `hermes doctor` and look for `Google Gemini OAuth (logged in ...)`.
   - If already logged in, prefer wiring the existing `google-gemini-cli` provider instead of forcing a new auth flow.
2. Verify the provider with a one-shot query before editing config.
   - Example: `hermes chat --provider google-gemini-cli -m gemini-3.1-pro-preview -q '只回复: GEMINI_OK'`
3. If the user did not explicitly ask to replace their main model, preserve the current primary provider and attach Gemini as a fallback first.
   - Use top-level `fallback_providers` in `~/.hermes/config.yaml`.
   - Example entry:
     ```yaml
     fallback_providers:
       - provider: google-gemini-cli
         model: gemini-3.1-pro-preview
     ```
4. Verify the wiring after config change.
   - `hermes fallback list`
   - another direct `hermes chat --provider google-gemini-cli ... -q ...` probe
5. Report the distinction clearly:
   - `google-gemini-cli` = Gemini CLI / Cloud Code Assist OAuth path
   - `gemini` = Google AI Studio API-key provider

### Multi-model integration points for Gemini OAuth

If Gemini should participate in Hermes multi-model orchestration (not just direct `/model` switching), wire every layer that resolves models by pricing/quorum metadata:

1. `/model` picker: `hermes_cli/model_switch.py` must ask `hermes_cli.auth.get_auth_status()` for `oauth_external` / `external_process` providers because `google-gemini-cli` login state lives in `~/.hermes/auth/google_oauth.json`, not generic `auth.json` or credential pool.
2. Provider display: `hermes_cli/providers.py` should label `google-gemini-cli` as `Google Gemini (OAuth)` so picker output is user-readable.
3. Main/fallback config: preserve current primary unless explicitly changed; set Gemini under top-level `fallback_providers`.
4. Pricing/router metadata: add canonical Gemini OAuth models such as `gemini-3.1-pro-preview` and `gemini-3-flash-preview` to `pricing.models` with `provider: google-gemini-cli` and candidate groups (`chat`, `codegen`, `reviewer`, optionally `hard_reasoning`/`arbiter`).
5. Multi-brain quorum: add the canonical Gemini model to `~/.hermes/config/quorum.yaml` tiers as an additional planner while keeping `min_quorum` below total planners so expired OAuth/capacity throttle does not block certification. If taskpool ratification has a hardcoded core panel (e.g. `REQUIRED_RATIFICATION_MODELS`), do **not** remove Gemini from quorum to silence `unexpected_*`; model it as an optional/allowed ratification participant and set T2/T3 `quorum` high enough to actually include it.
6. Script invocation: `~/.hermes/scripts/consult_models.py`, `~/.hermes/scripts/cross-patch.py`, and `~/.hermes/scripts/ensemble-vote.py` must treat `google-gemini-cli` as a supported Hermes provider so they pass `--provider google-gemini-cli` to `hermes chat`. Prefer augmenting from `hermes_cli.providers.HERMES_OVERLAYS` with a static fallback to avoid hardcoded-list drift.
7. Smart routing / verification: add Gemini models to `smart_model_routing.candidate_models` and, where useful, `verification.tiers.*.reviewers` rather than making Gemini the default producer.
8. Verification commands:
   - `./venv/bin/python -m pytest tests/hermes_cli/test_gemini_oauth_in_model_picker.py tests/agent/test_gemini_fast_fallback.py`
   - `./venv/bin/python -m py_compile ~/.hermes/scripts/consult_models.py ~/.hermes/scripts/cross-patch.py ~/.hermes/scripts/ensemble-vote.py`
   - `python3 ~/.hermes/scripts/consult_models.py status`
   - `hermes chat --provider google-gemini-cli -m gemini-3.1-pro-preview -q '只回复: GEMINI_OK' --quiet --max-turns 1 --ignore-rules`
   - `python3 ~/.hermes/scripts/model-router.py probe`
9. If the user says only “测试一下” after Gemini wiring, run the concise smoke-test triad instead of re-auditing everything:
   - Direct OAuth call: `hermes chat --provider google-gemini-cli -m gemini-3.1-pro-preview -q '只回复: GEMINI_OK' --quiet --max-turns 1 --ignore-rules`
   - Router probe: `python3 ~/.hermes/scripts/model-router.py probe`
   - Focused regression: `./venv/bin/python -m pytest tests/hermes_cli/test_gemini_oauth_in_model_picker.py tests/agent/test_gemini_fast_fallback.py`
- For multi-provider power users, switching the default model to Gemini without being asked can unnecessarily displace an existing primary workflow. Safer default: keep the current main provider and add Gemini as fallback unless the user explicitly wants Gemini as primary.
- `google-gemini-cli` and `gemini` are different Hermes providers; do not describe the OAuth path as AI Studio API-key setup.
- `anthropic` and `claude-code` are different Claude entitlement paths. For Claude Max / Claude Code OAuth users, canonical Claude models should resolve to runtime provider `claude-code` when the `claude` CLI is available; do not treat `hermes chat --provider anthropic ...` extra-usage errors as proof that Claude Code / Claude Max is offline or exhausted.

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
- `references/rokid-lingzhu-sse-bridge.md` — fixed-domain Rokid Lingzhu custom-agent integration pattern for Hermes: FastAPI SSE bridge, Cloudflare Tunnel, DNS route, launchd persistence, and end-to-end SSE verification.
- `references/budget-relay-delegation.md` — debugging pattern for Hermes budget-relay features that appear wired at the CLI layer but fail on delegated child-agent execution paths; includes the staged-vs-worktree check.

- `references/hermes-self-check-update.md` — explicit Hermes self-check/update workflow and reporting checklist
- `references/rokid-lingzhu-bridge.md` — Rokid 灵珠/Rizon custom-agent bridge architecture, schema, safety red lines, and public exposure options
- `references/hermes-rokid-lingzhu-bridge.md` — implementation/operations notes for FastAPI SSE bridge, temporary Cloudflare tunnels, launchd recovery, and endpoint refresh
- `references/budget-handoff-automation.md` — default-safe budget/context exhaustion handoff automation
- `references/self-evolution-pua-loop.md` — Hermes-hosted OpenClaw SE-AOS fusion
- `references/pa-evolution-daily-reporting.md` — scheduled PA health reporting workflow, trigger interpretation, and when not to create a skill from `unknown`
- `references/openclaw-inspired-hermes-control-plane.md`
- `references/sakana-conductor-pattern.md` — Sakana-inspired multi-model conductor pattern for Hermes: evidence boundary, model capability profiles, role-specific prompting, default-off role plans, and truth-gate-preserving integration points.
- `references/ratchet-upgrades.md` — ratchet upgrade pattern for combining upstream Hermes updates with local overlays using multi-model impact review, fail-closed patch replay, and verified baseline advancement. — OpenClaw/external agent framework → Hermes-local control-plane hardening
- `references/continuation-control-plane.md` — global durable packet architecture for unfinished work across conversation, delegation, taskpool, bg-review, cron, and gateway; includes `agent/continuation.py` contracts and verification commands
- `references/auto-relay-continuation.md` — budget/tool-iteration exhaustion auto-relay with relay packets; includes the `max_iterations_reached(...)` exit-reason pitfall and verification checklist
- `references/taskpool-parallel-dispatch-and-handoff-governance.md` — taskpool parallel dispatch runtime config, dry-run observability, and handoff backlog archive workflow
- New Hermes scripts `~/.hermes/scripts/brain_api.py` and `~/.hermes/scripts/edge_worker.py` implement a local cloud-edge prototype (Brain HTTP API + Edge execution proxy) for validating the brain-tentacle architecture. See `cloud-edge-architecture` skill for the full architecture pattern.
- `references/prompt-builder-cache-layers.md` — 3-tier stable/context/volatile prompt cache architecture
- `references/layered-prompt-cache-implementation.md` — implementation pattern for Anthropic system content blocks, internal `_hermes_cacheable` markers, native tool cache markers, byte-stability fallback, and regression tests
- `references/evolution-lane-cert-loop.md` — evolution lane multimodel certification deadloop pattern and prevention

## Related umbrella skills

- `software-development` — general development workflow and verification discipline
- `devops` — infrastructure/deploy operations that are not Hermes-specific
