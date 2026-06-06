# Lowfat reference review for Hermes tool-output governance

Date: 2026-06-06T19:37:15+08:00
Task boundary: hermes-lowfat-output-governance
Reference repo: https://github.com/zdk/lowfat
Reference commit: 48c30f073f43aa82bb1230100447482c3ab1e858
GitHub API evidence: full_name=zdk/lowfat; description="lowfat - slim your command output. strips noise, saves tokens."; language=Rust; default_branch=main; pushed_at=2026-06-06T00:55:08Z.
Local clone used for review: /tmp/agent-team-2026-06-06----lowfat-e1ebe8dc7c4b/lowfat

## Scope and red lines

This is a reference review only. I did not install lowfat, did not run cargo install or brew install, and did not connect any third-party binary into Hermes. The output-governance rules below preserve Hermes proof, permission, taskpool, and mission-envelope gates.

Non-negotiable Hermes safety constraints for any future implementation:

- Never delete or hide command failures, stderr, stack traces, test failures, proof artifacts, mission-envelope evidence, approval/permission decisions, or diff context required to verify a change.
- Secret handling must run before any lossy summarization where possible; lossy filtering must not become a way to bypass redaction or proof gates.
- Any lowfat-like behavior must be default-off or narrowly opt-in, auditable, and reversible.
- Third-party binaries must not be added to the Hermes main execution path. If the design is absorbed, implement the safe subset natively in Hermes or behind explicit hooks/config.

## Source evidence from lowfat

### 1. Product framing: local-first, composable CLI-output slimming

README.md lines 8 and 14-19 state that lowfat reduces AI token costs by filtering CLI output before it reaches an agent, with a small local-first, composable, user-owned design. README.md lines 31-77 list integration modes: Claude Code PreToolUse hook, shell integration gated by agent env vars, OpenCode plugin, direct `lowfat <cmd>`, and Pi agent shell prefix.

Transferable principle: output slimming should be treated as a local, composable mediation layer between tool execution and model context, not as a replacement for the real command or proof store.

### 2. Architecture: runner + config + plugins + builtins + SQLite metrics

`docs/ARCHITECTURE.md` lines 5-36 show the core flow: user/agent calls lowfat, the CLI dispatches to a runner, the runner executes the real command, resolves a pipeline from config/plugins, filters a chain, and emits filtered output plus SQLite metrics. Lines 41-55 map components: CLI, Runner, Config, Plugins, Builtins, and SQLite metrics at `$XDG_DATA_HOME/lowfat` / `LOWFAT_DATA`.

Transferable principle: separate four concerns that Hermes currently blends at the tool-result seam: command execution, output transformation, metrics, and final result serialization.

### 3. Config and pipeline model

`docs/CONFIG.md` lines 5-21 define three levels: `lite`, `full`, and `ultra`, with `full` default and environment override via `LOWFAT_LEVEL`. Lines 31-57 describe `.lowfat` config discovery and settings: `level`, `disable`, `filters`, `pipeline.<cmd>`, and conditional pipelines for `.error`, `.empty`, and `.large`. Lines 82-120 show one-line pipelines for arbitrary commands and conditional large/error/empty handling. Lines 122-142 enumerate built-in processors such as `grep`, `grep-v`, `head`, `truncate`, `cut`, `strip-ansi`, `token-budget`, `dedup-blank`, `normalize`, and `redact-secrets`.

Transferable principle: Hermes should not only have a byte cap. It needs a typed, inspectable output-policy pipeline with conditions keyed by exit status and output size, plus a conservative path for error output.

### 4. Secret redaction as trusted core, not a lossy plugin

`docs/CONFIG.md` lines 143-162 describe built-in secret redaction with default patterns plus global/project `redact.conf`; malformed patterns report on stderr and fall back to built-in defaults. `crates/lowfat-core/src/redact.rs` lines 1-12 explicitly say redaction is trusted in-process Rust because plugin failure degrades to passthrough and would leak secrets. The same file lines 42-76 list default patterns for AWS, GitHub, GitLab, Slack, API keys, bearer tokens, JWTs, private keys, password URLs, and common secret/token/password assignments.

Transferable principle: in Hermes, redaction must remain a trusted core phase. Filters may be fail-open for usability, but redaction should be fail-closed to at least the built-in baseline.

### 5. Declarative filter DSL and conservative error contract

`docs/PLUGINS.md` lines 47-80 define `lf-filter`: first matching selector, built-in operations (`keep`, `drop`, `head`, `tail`, `or`, `raw`, `split`), and top-to-bottom pipeline semantics. Lines 81-104 define cascades guarded by `exit failed/ok`, level, and flags. Lines 301-310 provide the filter contract: `ultra` emits verdict lines, `full` strips progress/noise but keeps diffs/errors/structure, `lite` trims gently, and `$exit != 0` should be conservative and preserve error blocks.

Transferable principle: Hermes should encode preserve-on-failure as a first-class policy rule, not a guideline hidden in prompt text. For taskpool and code work, `exit_code != 0` should default to raw or high-context output.

### 6. Escape hatches exist but are bounded

`docs/PLUGINS.md` lines 105-111 allow `shell:` and `python:` escape hatches only when built-ins are insufficient; lines 291-299 require runtime dependencies to be declared and prewarmed by `plugin doctor`. `crates/lowfat-runner/src/process.rs` lines 20-38 run shell filters with `env_clear`, a sanitized allowlist, and explicit LOWFAT env vars. `crates/lowfat-plugin/src/security.rs` lines 20-56 validate plugin entry paths against traversal/absolute escapes and regular-file constraints; lines 58-107 reject obviously dangerous install/update/remove hooks; lines 147-162 define the sanitized environment and exclude secrets such as AWS/GitHub tokens in tests at lines 263-269.

Transferable principle: Hermes should not copy lowfat's shell/plugin escape hatches into core by default. If extensions are needed, prefer a Python-native policy DSL or existing Hermes plugin hooks with env sanitization, path boundaries, and explicit opt-in.

### 7. Metrics, history, audit, and candidate ranking

`docs/CONFIG.md` lines 163-179 explain `lowfat history` ranks real usage by frequency, raw tokens, and remaining cost; it stores only command plus first non-flag arg, capped at 10k rows, never full args/output/secrets. `crates/lowfat-core/src/db.rs` lines 124-168 create SQLite tables for lifetime `commands`, plugin `audit`, and capped `invocations`. Lines 245-268 insert invocation records and evict old rows past `INVOCATIONS_CAP=10_000`. Lines 371-423 compute history ranking from `SUM(filtered_tokens)`, raw averages, savings percentage, plugin registration, in-scope and reduced ratios. Lines 488-524 implement audit log insert/read for plugin actions.

Transferable principle: Hermes should add per-tool output governance metrics without storing sensitive raw output. The most useful ranking is not “tokens saved” alone, but “remaining noisy tokens still flowing into the model by tool/command class.”

### 8. Hooks and shell/agent integration

`crates/lowfat/src/commands/hook.rs` lines 5-43 implement a Claude Code PreToolUse hook: read JSON, require `tool_name == Bash`, rewrite via canonical `rewrite_command`, and return updated command plus `permissionDecision=allow`. `crates/lowfat/src/commands/rewrite.rs` lines 3-8 declare one canonical rewrite function shared by Claude hook and OpenCode; lines 11-19 skip empty/already-wrapped/disabled commands; lines 21-35 wrap commands only when a builtin, plugin, command pipeline, or wildcard pipeline applies. `crates/lowfat/src/commands/shell_init.rs` lines 20-30 generate shell wrappers only when `CLAUDECODE=1`, `CODEX_ENV` is set, or `LOWFAT_ENABLE=1`. `crates/lowfat/embedded/opencode/lowfat.ts` lines 1-8 describe a thin OpenCode plugin delegating to `lowfat rewrite`; lines 29-37 rewrite only if the command changes and pass through on failure.

Transferable principle: the safe pattern is a single canonical rewrite/policy decision function shared by all integrations, with skip-already-wrapped and pass-through-on-failure behavior. For Hermes, the analogous seam is the terminal/tool-result post-processing hook, not shell aliasing.

### 9. Failure tee and raw-output preservation

`crates/lowfat-core/src/tee.rs` lines 4-7 save raw output on command failure; lines 8-10 only save when exit code is nonzero and output is at least 500 chars; lines 21-24 write the raw file; lines 26-42 retain max 20 and print the file path. `crates/lowfat/src/commands/run.rs` lines 160-165 call tee-on-failure before printing filtered output.

Transferable principle: if Hermes ever applies lossy filtering, it needs an auditable raw-output retention path for failure/proof cases, ideally encrypted/private and bounded by retention policy. For taskpool proof, raw or proof-critical output must remain accessible, not just summarized.

## Current Hermes gap mapping

Observed Hermes source state in `/Users/charles/.hermes/hermes-agent`:

- `tools/terminal_tool.py` lines 2311-2329 already exposes a `transform_terminal_output` plugin seam before default truncation. This is the closest existing integration point for lowfat-style output policy.
- `tools/terminal_tool.py` lines 2332-2343 applies a hard output cap using a fixed head/tail split. This is deterministic but semantically blind: it can still cut out critical middle evidence, structured test summaries, or diff context.
- `tools/terminal_tool.py` lines 2345-2352 strips ANSI and redacts secrets after the transform hook and after truncation. That protects common leaks before serialization, but if a transform hook removes context before redaction, hook output becomes the redaction input. A native policy should make redaction ordering explicit.
- `tools/terminal_tool.py` lines 2358-2368 returns only `{output, exit_code, error, ...}` to the model. There is no standardized per-tool policy metadata such as raw size, filtered size, omitted classes, policy name/version, safety mode, or raw-output handle.
- `cron/scheduler.py` lines 1060-1065 redacts script stdout/stderr before any return path, and lines 1181-1183 have an 8000-character injected-context cap. This is another output-governance surface but separate from terminal output.
- `tools/code_execution_tool.py` lines 22-25 already states a token-saving pattern: intermediate tool results from code-exec do not enter the context; only script stdout is returned. This is a strong Hermes-native precedent for deliberate context mediation.

Gap summary:

1. Hermes has deterministic caps and redaction, but not a declarative, inspectable output-policy pipeline.
2. Hermes has a plugin seam, but not a governed built-in policy registry with per-tool defaults and safety classes.
3. Hermes has no persistent lightweight history ranking by tool/command/output-cost to guide where slimming matters.
4. Hermes has no standard proof-safe raw-output retention handle for lossy-filtered terminal output.
5. Hermes does not expose output-policy decisions as audit metadata in tool results.

## Transferable patterns to absorb

1. Native policy pipeline, not third-party binary integration

Implement a Hermes-native output policy abstraction for tool outputs:

- phases: `redact`, `normalize`, `classify`, `preserve_critical`, `trim`, `annotate`;
- conditions: `exit_code != 0`, `output_empty`, `output_large`, `tool_name`, `command_class`, `taskpool_context`, `proof_required`;
- deterministic processors: strip ANSI, line caps, token/char budget, regex keep/drop, head/tail, structured table compaction, diff hunk budget, test-summary preservation;
- metadata: policy id/version, raw bytes/chars, returned bytes/chars, omitted bytes/chars, preserved categories, raw-handle if any.

2. Default-off staged rollout

Start behind config such as:

```yaml
tool_output_governance:
  enabled: false
  mode: observe   # observe | annotate | filter
  raw_retention: failures_only
  preserve_on_error: true
  protect_taskpool_proof: true
```

Observe mode records metrics only. Annotate mode adds metadata/truncation notices without reducing beyond current caps. Filter mode is opt-in per tool/command class.

3. Error/proof-safe default boundaries

For terminal/code/test contexts:

- `exit_code != 0`: preserve raw or use a very high-context error policy; never apply aggressive `ultra`.
- command likely running tests/lint/build: preserve failure lines, summary counts, file paths, tracebacks, and final command exit status.
- git diff/show/status: preserve file headers, hunk headers, changed lines around modifications, and staged/untracked status needed for audit.
- taskpool/proof contexts: policy must not remove acceptance evidence, proof log paths, transition evidence, permission decisions, or PROOF_JSON.

4. Lightweight history/stats without raw output

Record only non-sensitive metadata:

- tool name, command class, first safe subcommand token, exit code class;
- raw chars/tokens estimate, returned chars/tokens estimate, saved estimate;
- policy id/version and whether it was observe/annotate/filter;
- timestamp bucket and project/workdir hash or allowlisted basename, not full private args;
- never raw output, never full arguments, never secrets.

Ranking should surface “remaining output cost” by tool/command and “weak policy” rows, mirroring lowfat's candidate ranking.

5. Canonical decision function

All entrypoints should call one policy resolver:

- terminal foreground output;
- background process `process.log`/`poll` excerpts;
- cron context injection;
- browser snapshots/console output if later extended;
- code-exec stdout.

Do not let each adapter invent its own truncation policy.

## Non-transferable or high-risk lowfat details

- Do not pipe Hermes terminal commands through `lowfat <cmd>` or install lowfat globally. This violates the task red line and would put a third-party binary in the main tool path.
- Do not copy shell alias injection into Hermes. Hermes already controls the tool boundary; shell wrappers are unnecessary and harder to audit.
- Do not allow arbitrary user shell filters in the default Hermes output path. Lowfat contains env sanitization and path checks, but Hermes proof/permission gates are stricter and should prefer native deterministic processors.
- Do not make user plugins override built-in safety processors such as redaction or proof-preservation. Lowfat allows plugin override of builtins for user ownership; Hermes should not allow override of safety-critical phases.
- Do not use `!no-defaults`-style removal for Hermes redaction defaults without a stronger compliance gate. Hermes should permit adding redaction rules, not dropping the baseline in normal mode.
- Do not rank or persist full command args/output. Lowfat intentionally stores command + first non-flag arg; Hermes should be at least as conservative.

## Proposed phased implementation plan

Phase 0 — SSOT and observe-only metrics

- Create a Hermes output-governance design SSOT or ADR referencing this review.
- Add an observe-only metrics hook at the terminal result seam after command execution and before current truncation/redaction serialization.
- Record raw/returned size estimates and command class, but do not alter output.
- Verification: focused unit tests for metadata redaction/no-raw-output storage; terminal smoke showing unchanged output.

Phase 1 — Native safety ordering and metadata

- Refactor terminal output post-processing into named phases: transform hook, strip ANSI, redact, built-in cap, serialize.
- Decide whether redaction should run before third-party `transform_terminal_output` hooks or whether hooks must be treated as trusted/admin-only. Safer default: redaction before lossy plugin transforms and again before serialization.
- Add tool-result metadata fields for truncation/filter decisions without changing displayed output semantics.
- Verification: tests that secret-like output is redacted in both normal and transformed paths; tests that truncation notices include omitted counts.

Phase 2 — Declarative built-in policy registry, still default-off

- Add a Python-native policy registry with deterministic processors equivalent to the low-risk lowfat built-ins: `strip_ansi`, `normalize`, `dedup_blank`, `head_tail_budget`, `grep_keep`, `grep_drop`, `token_budget_estimate`, `preserve_error_blocks`.
- Add conservative built-in policies for `git status`, `git diff`, test runners, and generic long logs.
- Keep `enabled=false` by default; allow per-session/per-profile opt-in.
- Verification: golden fixture tests for git diff/test failure/log outputs; assert failure/proof lines survive.

Phase 3 — Raw retention for failure/proof cases

- Add bounded private raw-output handles for outputs filtered in failure/proof contexts. Store under Hermes profile state with retention caps and redaction-aware metadata.
- Surface handles in tool-result metadata, not as public attachments.
- Verification: failure command stores raw handle; successful small output stores none; retention cap deletes oldest; taskpool proof consumers can still access required evidence.

Phase 4 — History/stats and tuning loop

- Add `hermes tool-output stats/history` or fold into existing observability tooling.
- Rank by remaining model-visible output cost and weak policy coverage.
- Add export/prune commands that never include raw output.
- Verification: SQLite/JSON store migration tests; prune/export tests; no secret/raw output snapshots.

Phase 5 — Optional plugin extension governance

- Only after native policies prove insufficient, expose a tightly scoped Hermes plugin API for output transforms.
- Require manifest, safe env, no filesystem escape, no shell by default, and no override of redaction/proof phases.
- Verification: malicious plugin fixtures for path traversal, secret env exposure, and failed transform pass-through.

## Minimum regression tests if implementation starts

Focused tests should cover:

1. `exit_code != 0` preserves stderr, traceback, failing test names, and exit status.
2. Secret redaction is applied before final serialization and cannot be disabled by a slimming policy.
3. Taskpool proof strings (`PROOF_JSON`, proof log file paths, acceptance criteria evidence) are never filtered.
4. Diff policy preserves file headers, hunk headers, changed lines, and enough context for review.
5. History/stats persistence stores only command class/subcommand, token/char counts, policy id, and exit code class; no raw output or full args.
6. Default configuration leaves current terminal output behavior unchanged.
7. Rollback: disabling config returns to the current hard-cap path.

## Recommendation

Adopt lowfat's methodology, not its binary. The strongest Hermes migration is a native, default-off output-governance layer that makes today's hard cap auditable and policy-driven while preserving proof gates. The immediate next bounded step should be an observe-only design/metrics phase at `tools/terminal_tool.py`'s existing output seam, with no filtering enabled until golden fixtures prove that errors, secrets, tests, diffs, and taskpool proof evidence are preserved.

## Validation performed

- `git clone --depth 1 https://github.com/zdk/lowfat.git lowfat` in `/tmp/agent-team-2026-06-06----lowfat-e1ebe8dc7c4b`; reviewed commit `48c30f073f43aa82bb1230100447482c3ab1e858`.
- GitHub API probe confirmed repo identity, description, language, pushed_at, and default branch.
- `python3 /Users/charles/.hermes/scripts/brain_task_orchestrator.py list --json` completed and returned `status`, `generated_at`, `task_count`, `rows`, and `tasks` with `task_count=7`.
- Reviewed Hermes source evidence in `tools/terminal_tool.py`, `tools/code_execution_tool.py`, and `cron/scheduler.py` without modifying Hermes source code.

## Residual risks

- This review is source-based, not a runtime benchmark of lowfat. That is intentional because the task forbids installing/connecting the third-party binary and the objective is reference absorption.
- Lowfat is very new and moving quickly; any future implementation should pin the reviewed commit and rerun source review before copying details.
- Hermes source tree and `~/.hermes` had many pre-existing unrelated local modifications; this task changed only this review note.
