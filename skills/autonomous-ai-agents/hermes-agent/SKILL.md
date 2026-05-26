---
name: hermes-agent
description: Use when extending or operating Hermes Agent including CLI/setup, skills, tools, profiles, gateway, taskpool hooks, certified auto-done, blocked-task closure, memory-cap selfcheck, and self-evolution / PUA-loop workflows. See references/ for taskpool hook debugging, evolution-task add rules, pre-ingest triage, memory compaction, bad-case to proposal to benchmark self-optimization, `references/budget-handoff-automation.md` for default-safe budget/context exhaustion behavior, `references/budget-relay-debugging.md` for delegated continuation / relay pitfalls, and other Hermes-specific deep dives.
---

Reference addendum: `references/provider-version-drift-and-codex-breaker.md` captures the workflow for separating Hermes runtime package skew from local source drift when provider/version mismatch or `agent.codex_circuit_breaker` incidents appear.

Reference addendum: `references/dreaming-outcomes-skill-review-and-evaluator.md` maps Dreaming-style post-run procedure distillation and Outcomes-style independent evaluator gates into Hermes skill review, memory hygiene, taskpool proof logs, and fail-closed lifecycle advancement.

Reference addendum: `references/external-skill-to-brain-overlay.md` captures the governed workflow for absorbing an external Agent Skills package into Hermes as a discoverable brain overlay with registry routing, skill discovery, diagnostics, taskpool evidence, and fail-closed review/done handling.

Reference addendum: `references/rokid-lingzhu-sse-bridge.md` captures the workflow for exposing Hermes to Rokid smart glasses through the Rokid Rizon/Lingzhu custom third-party agent SSE protocol, including FastAPI bridge shape, Cloudflare temporary/named tunnel handling, macOS LaunchAgent recovery, Rizon custom-agent API fallback, and verification gates.

Reference addendum: `/Users/charles/.hermes/docs/private/vercel-reference-self-optimization-20260526.md` captures the Vercel monorepo review pattern for Hermes self-optimization: first-class `AGENTS.md`, named validation surfaces, affected-check fail-safe broadening, fixture/evidence protection, release/evidence notes, and reference-repo analysis without cargo-culting the source stack.

Reference addendum: `/Users/charles/.hermes/docs/private/hermes-self-optimization-ssot-20260526.md` is the canonical multi-entry SSOT rule for Hermes self-optimization. Before changing Hermes itself through chat, taskpool, cron/bg-review, multi-model certification, skill patches, or code edits, identify/create exactly one SSOT artifact and make all derived entrypoints reference it rather than copying parallel facts.

# Hermes Agent

Use this skill when operating or extending Hermes Agent itself: CLI behavior, setup, update/upgrade workflows, built-in tools, memory system, gateway/taskpool hooks, self-evolution loops, certified auto-done, and related local-control-plane hardening.

## Triggers

Use this skill when the user asks to:
- inspect, update, repair, or self-check Hermes itself
- modify Hermes core code, skills, hooks, memory, gateway, or taskpool behavior
- troubleshoot Hermes-specific regressions after upstream pulls or self-updates
- run Hermes-local benchmarking, post-update validation, or self-evolution workflows

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
   - `python3 ~/.hermes/scripts/post-update-check.py --fix`
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
- For bg-review taskpool integration, distinguish safe candidate extraction from side effects: `background_review.taskpool.mode: suggest` only records candidates in status/HTML, while `mode: enqueue` mutates the taskpool. See `references/background-review-taskpool-suggest-mode.md`.
- For bg-review summary regressions, remember the review agent inherits the parent conversation snapshot. Both successful action summaries and failed tool-result summaries must skip tool messages already present in `messages_snapshot` by `tool_call_id`/content; otherwise resolved main-turn tool failures can be re-announced as false `Self-improvement review failed` notifications.

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
- `references/prompt-builder-cache-layers.md` — 3-tier stable/context/volatile prompt cache architecture
- `references/layered-prompt-cache-implementation.md` — implementation pattern for Anthropic system content blocks, internal `_hermes_cacheable` markers, native tool cache markers, byte-stability fallback, and regression tests
- `references/evolution-lane-cert-loop.md` — evolution lane multimodel certification deadloop pattern and prevention

## Related umbrella skills

- `software-development` — general development workflow and verification discipline
- `devops` — infrastructure/deploy operations that are not Hermes-specific
