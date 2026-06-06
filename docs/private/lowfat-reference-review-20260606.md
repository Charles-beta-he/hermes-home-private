# lowfat reference review for Hermes tool-output governance

Date: 2026-06-06
Task boundary: hermes-lowfat-output-governance
Source repo: https://github.com/zdk/lowfat
Reviewed commit: 48c30f073f43aa82bb1230100447482c3ab1e858
Commit metadata: 2026-06-06T07:55:08+07:00, "Merge pull request #6 from BioInfo/docs/architecture-data-dir"
Local review checkout: /tmp/agent-team-2026-06-06----lowfat-e1ebe8dc7c4b/lowfat
Scope: reference review only; no Hermes implementation in this task.

## Executive summary

lowfat is a local-first CLI wrapper/filter layer that reduces token costs by executing the real command, resolving a command-specific filter/pipeline, transforming stdout+stderr, and recording local SQLite usage metrics. Its strongest transferable ideas for Hermes are:

1. Make output slimming a policy layer with auditable stages, not ad-hoc truncation.
2. Prefer deterministic in-process transforms first; keep subprocess filters as explicit escape hatches with sanitized environments.
3. Treat non-zero exits, empty output, large output, secrets, tests, diffs, and proof artifacts as separate output classes.
4. Track savings and weak rows locally so future filter work is evidence-driven.
5. Integrate through a narrow rewrite/hook seam while preserving pass-through defaults and rollback switches.

For Hermes, the safe next step is not to import lowfat or invoke its binary. The maintainable path is to design a default-off native Hermes output-policy layer around existing tool-output seams, especially terminal output, process logs, file reads, cron/script outputs, and browser snapshots. The policy must preserve errors, secret handling, taskpool proof, permission decisions, mission-envelope evidence, test failures, diffs, and acceptance evidence.

## Source evidence read

Repository-level documentation:

- README lines 8-19 state the core product claim: filter unnecessary CLI output before it reaches an agent; local-first; composable UNIX-style pipes; history shows frequent commands for user customization.
- README lines 35-63 describe Claude Code hook, shell integration, OpenCode plugin, and direct command prefix modes.
- README lines 81-101 list state/usage commands: info, stats, history, level, plugin new/doctor, and filter --explain.
- docs/ARCHITECTURE.md lines 18-36 show the execution chain: exec real command -> resolve pipeline -> filter chain -> filtered output + SQLite metrics.
- docs/ARCHITECTURE.md lines 41-55 map components: CLI, Runner, Config, Plugins, Builtins, SQLite metrics under $XDG_DATA_HOME/lowfat or LOWFAT_DATA.

Config and pipeline:

- docs/CONFIG.md lines 5-21 define lite/full/ultra intensity levels and LOWFAT_LEVEL override.
- docs/CONFIG.md lines 43-57 define .lowfat settings: level, disable, filters, pipeline.<cmd>, pipeline.<cmd>.error, pipeline.<cmd>.empty, pipeline.<cmd>.large.
- docs/CONFIG.md lines 111-120 show conditional pipelines for error, empty, and large outputs.
- docs/CONFIG.md lines 122-141 list built-ins: grep, grep-v, head, truncate, cut, strip-ansi, token-budget, dedup-blank, normalize, redact-secrets.
- crates/lowfat-core/src/pipeline.rs lines 24-44 implement conditional pipeline selection: non-zero exit uses on_error first, then empty, then large > 1000 estimated tokens, otherwise default.
- crates/lowfat-core/src/pipeline.rs lines 196-205 classify built-in stages; unknown stages are treated as plugin stages.
- crates/lowfat-core/src/pipeline.rs lines 245-263 implement token-budget by trimming to an estimated token target and appending an explicit truncation notice.
- crates/lowfat-core/src/pipeline.rs lines 387-428 dispatch built-in processors and level-specific defaults.

Plugin DSL and safety boundary:

- docs/PLUGINS.md lines 47-63 define lf-filter as first-match selector rules over subcommand and level.
- docs/PLUGINS.md lines 64-79 define deterministic ops: keep, drop, head, tail, or, raw, split.
- docs/PLUGINS.md lines 81-103 define cascades with closed guards over exit failed/ok, level, and flags; no arbitrary expressions.
- docs/PLUGINS.md lines 105-111 allow shell/python escape hatches only where declarative ops cannot express the transformation.
- docs/PLUGINS.md lines 181-225 show a git diff rule where `if exit failed: raw` preserves failed diffs; this is the key safety pattern for Hermes.
- docs/lf-filter-v2.md lines 13-18 says v2 adds only cascades and remains a superset, keeping the DSL a match table rather than a programming language.
- docs/lf-filter-v2.md lines 61-89 explain the closed guard vocabulary and explicitly reject general expressions, comparisons, parentheses, and `or` operator growth.
- crates/lowfat-runner/src/lf_filter.rs lines 47-68 degrade execution errors to passthrough and log an error, never making output worse than no filter.
- crates/lowfat-runner/src/process.rs lines 20-37 run shell filters under sh with env_clear plus a sanitized env and explicit LOWFAT_* context vars.
- crates/lowfat-plugin/src/security.rs lines 20-56 validate plugin entry paths against path traversal and non-file entries.
- crates/lowfat-plugin/src/security.rs lines 58-107 block obviously dangerous install/update/remove hooks.
- crates/lowfat-plugin/src/security.rs lines 149-162 sanitize environment variables and tests assert AWS_SECRET_ACCESS_KEY/GITHUB_TOKEN are not passed.

Command execution, history, stats, and audit:

- crates/lowfat/src/commands/run.rs lines 41-49 execute the real command and return execution errors directly.
- crates/lowfat/src/commands/run.rs lines 51-69 skip filtering for tiny outputs under 128 estimated tokens but still record invocation metadata.
- crates/lowfat/src/commands/run.rs lines 71-83 resolve built-in/external filters and the pipeline.
- crates/lowfat/src/commands/run.rs lines 125-157 track full command savings plus usage-history rows that store command+subcommand, token counts, plugin coverage flags, and exit code.
- crates/lowfat/src/commands/run.rs lines 160-165 save raw output on failure, print filtered output, and return the original exit code.
- crates/lowfat-core/src/db.rs lines 77-79 cap invocation history at 10,000 rows.
- crates/lowfat-core/src/db.rs lines 124-214 create SQLite tables for commands, audit, and invocations, including token counts, savings, plugin source, and exit code.
- crates/lowfat-core/src/db.rs lines 245-268 record invocation rows and evict oldest rows above the cap.
- crates/lowfat-core/src/db.rs lines 371-423 rank command/subcommand pairs by remaining filtered tokens, hiding low-value trivia unless show_all is requested.
- crates/lowfat-core/src/db.rs lines 425-460 compute lifetime savings and top commands.
- crates/lowfat-core/src/db.rs lines 488-524 record and read audit entries.
- crates/lowfat/src/commands/stats.rs lines 5-16 route stats to lifetime gains or recent plugin audit.
- crates/lowfat/src/commands/history_export.rs lines 6-32 export invocation rows as JSON.
- crates/lowfat/src/commands/history_prune.rs lines 5-29 prune invocation history, with default conservative older-than-90-days behavior.

Agent hooks and shell integration:

- crates/lowfat/src/commands/rewrite.rs lines 3-8 define rewrite_command as the single source of truth shared by Claude Code hook and OpenCode plugin.
- crates/lowfat/src/commands/rewrite.rs lines 11-19 skip empty input, already-wrapped commands, or disabled commands.
- crates/lowfat/src/commands/rewrite.rs lines 21-35 wrap only commands with a builtin, plugin, command pipeline, or wildcard pipeline.
- crates/lowfat/src/commands/hook.rs lines 5-17 process only Claude Code Bash PreToolUse events; other tools pass through.
- crates/lowfat/src/commands/hook.rs lines 24-42 reuse rewrite_command and return permissionDecision=allow with updatedInput when a rewrite applies.
- crates/lowfat/src/commands/shell_init.rs lines 20-30 generate bash/zsh wrapper functions only when CLAUDECODE=1, CODEX_ENV is set, or LOWFAT_ENABLE=1.
- crates/lowfat/src/commands/shell_init.rs lines 33-43 do the same for fish.
- crates/lowfat/embedded/opencode/lowfat.ts lines 3-8 keep OpenCode integration thin: it delegates all policy to lowfat rewrite.
- crates/lowfat/embedded/opencode/lowfat.ts lines 18-38 hooks tool.execute.before and passes through if lowfat is absent or rewrite fails.

Hermes current-state evidence relevant to the gap mapping:

- /Users/charles/.hermes/hermes-agent/tools/tool_output_limits.py lines 1-29 centralize hardcoded output caps behind config.tool_output; defaults remain unchanged.
- /Users/charles/.hermes/hermes-agent/tools/tool_output_limits.py lines 36-41 define default max_bytes=50000, max_lines=2000, max_line_length=2000.
- /Users/charles/.hermes/hermes-agent/tools/terminal_tool.py lines 2311-2329 expose a foreground terminal output transform hook; the first valid string returned by plugins wins, and hook exceptions pass through.
- /Users/charles/.hermes/hermes-agent/tools/terminal_tool.py lines 2332-2343 perform fixed head/tail truncation after transforms.
- /Users/charles/.hermes/hermes-agent/tools/terminal_tool.py lines 2348-2352 strip ANSI and redact secrets after truncation/transform.
- /Users/charles/.hermes/hermes-agent/tests/tools/test_terminal_output_transform_hook.py lines 61-149 verify no hook/invalid hook/failing hook leaves output unchanged, valid hook output is used, long replacement is still truncated, and strip/redact still run.
- /Users/charles/.hermes/hermes-agent/tests/tools/test_terminal_output_transform_hook.py lines 152-172 verify output transform does not change approval or exit-code meaning.

## Transferable design patterns

### 1. A typed output-policy pipeline, not just truncation

lowfat separates stage resolution from stage execution. Pipelines can be composed from built-ins and plugins, and conditional pipelines choose error/empty/large/default arms before transformation. Hermes can adopt this as a native `ToolOutputPolicy` for terminal/process/file/browser/cron outputs:

- input metadata: tool_name, command/action, args redacted, exit_code/status, approval state, mission/task id, output byte count, estimated tokens, source channel, proof-sensitive flag;
- policy result: transformed output, dropped/retained segment manifest, token estimates before/after, safety class, redaction summary, passthrough reason;
- deterministic stages: strip_ansi, redact, collapse_blanks, head_tail, keep_patterns, drop_patterns, token_budget, preserve_errors, preserve_tail, proof_pin, diff_context_pin;
- default: disabled or observe-only until tests and explicit config enable it.

Why it transfers: Hermes already has a terminal output transform hook and central output caps, but the hook is a generic plugin string replacement. lowfat's pipeline gives a stronger typed contract, explainability, and per-condition routing.

### 2. Conditional preservation of high-risk outputs

The `if exit failed: raw` pattern is the most important lowfat safety lesson. Hermes should not blindly shrink command output when:

- exit_code is non-zero and no explicit safe error policy exists;
- output contains test failure markers, tracebacks, stack traces, panic/fatal/error blocks;
- output is a diff, proof artifact, taskpool closeout evidence, permission decision, secret-detection alert, or mission-envelope validation result;
- the tool result is already the user-requested artifact, e.g. a grep result, line-numbered file excerpt, or final proof log.

Hermes policy should classify these as `must_preserve`, `summarize_with_manifest`, or `eligible_for_slimming`; unknown high-risk cases fail closed to passthrough.

### 3. Local usage history to drive future filters

lowfat records command/subcommand, token counts, plugin coverage, shrink/no-shrink, source, and exit code while avoiding full arguments and output in invocation history. Hermes can add an output-governance ledger that stores:

- tool name and safe subcommand/action category;
- pre/post char/token estimates;
- policy id and version;
- reason codes: passthrough_small, passthrough_error, transformed_large, redacted, proof_sensitive, diff_sensitive;
- counts only by default, not raw output;
- retention cap and pruning/export controls.

This would allow token-cost governance without leaking private content or bloating memory. It also lets future work target high-cost tool outputs using real Hermes data instead of guesses.

### 4. In-process safe transforms first; escape hatches last

lowfat's `.lf` DSL is intentionally closed and analyzable. Hermes should prefer a Python-native transform registry over arbitrary shell filters:

- pure functions over strings/structured tool result objects;
- declarative config, closed guard vocabulary, no shell execution by default;
- allow external hooks only via existing plugin framework with opt-in, scoped permissions, sanitized env, and full passthrough fallback;
- every policy stage must be unit-testable with fixtures.

This is more appropriate than importing lowfat's Rust DSL or executing third-party binaries in Hermes' main tool path.

### 5. Thin integration seam and single source of truth

lowfat's rewrite command is the single policy authority for Claude hook and OpenCode plugin. Hermes should likewise avoid each tool inventing slimming logic. A central `agent/output_policy.py` or `tools/output_policy.py` should be called by terminal, process registry, execute_code, cron script ingestion, and eventually browser/file tools. Tool-specific wrappers should pass metadata and receive a typed result.

### 6. Auditable slimming

lowfat exposes info/stats/history/audit. Hermes needs an auditable record each time output is slimmed:

- transformed-by policy/version;
- before/after token estimates;
- omitted segment count and reason;
- preserved anchors: errors, last N lines, diff hunk headers, proof markers;
- whether redaction occurred;
- whether transformation was disabled due to red lines.

This audit can be appended to logs/status but should not pollute every assistant-facing tool result unless configured.

## Non-transferable or risky lowfat design choices

1. Do not cargo install, brew install, or call the lowfat binary from Hermes. The task red line forbids this, and Hermes should keep core tool behavior native and dependency-controlled.
2. Do not auto-wrap the user's shell commands globally. Hermes already owns tool execution; shell function rewriting is useful for external agents but would be too broad for Hermes' permission/proof gates.
3. Do not use arbitrary shell/python escape hatches in default Hermes policies. Hermes can keep plugin hooks for opt-in advanced users, but default governance should be in-process and typed.
4. Do not let user plugins override core safety filters such as redaction, permission evidence, taskpool proof, or mission-envelope validation.
5. Do not store full raw outputs in a history database by default. lowfat stores full raw/filtered strings in the commands table for gain tracking; Hermes should treat raw output as sensitive and store aggregate metrics unless an explicit evidence capture path is requested.
6. Do not apply token-budget truncation to proof artifacts, diffs, failures, or tests without a preservation manifest. A naive token budget can remove exactly the lines needed for deterministic verification.
7. Do not equate token savings with correctness. Savings metrics are useful only below red-line preservation gates.

## Hermes gap mapping

### Existing Hermes capabilities

- Configurable hard caps exist through `tool_output.max_bytes`, `max_lines`, and `max_line_length`.
- Terminal foreground output already has a plugin hook seam (`transform_terminal_output`) before default truncation.
- Terminal output redaction and ANSI stripping are already verified after hook transforms.
- Tests already assert transforms do not change approval/exit-code meaning.

### Gaps

1. No typed output-policy result. Current terminal transform hook returns a raw string, not a structured decision with reasons, token counts, preserved anchors, or audit metadata.
2. No central cross-tool policy. Terminal has a hook, file operations have pagination/line limits, cron has separate script-output handling, and browser snapshots have separate compaction. There is no shared governance ledger.
3. No conditional preservation matrix. Existing truncation is head/tail by byte cap; it does not classify error/test/proof/diff outputs before slimming.
4. No history/stats for tool-output token spend. Hermes has configurable caps but not lowfat-style command/action rankings or weak-filter discovery.
5. No explain mode. Users cannot ask why a tool output was reduced, which policy stage fired, or what was preserved.
6. Plugin hook is fail-open string replacement. This is good for safety but insufficient for audited slimming because a plugin can silently change important evidence unless core policy guards run after it.
7. Redaction order needs explicit policy review. Terminal currently truncates before stripping ANSI/redacting. That preserves cap behavior, but if a secret appears only in an omitted region, the assistant never sees it, while logs/history must also avoid retaining it. A future policy should make redaction-before-persistence mandatory and carefully define whether redaction is before or after slimming for each path.

## Recommended Hermes implementation plan

### Phase 0: Reference review only, complete in this artifact

Deliver this document as the SSOT reference review. No code changes and no third-party binary integration.

### Phase 1: Observe-only output governance ledger, default off for user-visible transforms

Add a native, default-off/observe-only module, e.g. `tools/output_policy.py`, with:

- `ToolOutputContext(tool_name, action, exit_code, status, command_class, proof_sensitive, permission_sensitive, mission_sensitive, output_len, estimated_tokens)`;
- `ToolOutputDecision(mode, reason_codes, before_tokens, after_tokens, policy_version, audit)`;
- no mutation by default, only metrics and classification;
- config: `tool_output_policy.enabled: false`, `tool_output_policy.observe: true`, `tool_output_policy.ledger_enabled: false` by default;
- rollback: remove/disable config; code path returns original output on any exception.

Focused tests:

- classification preserves non-zero exit outputs;
- proof markers force passthrough;
- secrets are never written to the ledger;
- malformed config falls back to passthrough.

### Phase 2: Terminal-only deterministic slimming, still conservative

Wire the policy after plugin transform and before final truncation/redaction in terminal foreground output, but only when `tool_output_policy.enabled: true`.

Rules:

- errors/test failures/proof/diff/permission outputs default to passthrough or preserve anchors;
- large success outputs can use keep/head-tail/token-budget with explicit omitted notice;
- strip/redact still run after any transform, and redaction-before-ledger is mandatory;
- keep current max_bytes cap as the final safety net.

Focused tests:

- existing `test_terminal_output_transform_hook.py` remains passing;
- new tests for policy disabled -> unchanged;
- enabled success large output -> transformed with audit;
- enabled non-zero output -> passthrough with reason;
- enabled proof marker -> passthrough with reason;
- transform exception -> unchanged output.

### Phase 3: Stats/history commands

Expose local stats without raw output:

- `hermes tool-output stats` or `hermes diagnostics tool-output`;
- rank by tool/action and remaining output tokens;
- show counts by reason code and policy version;
- prune/export with retention caps;
- no arguments, output, secrets, or proof body stored by default.

### Phase 4: Cross-tool rollout

Extend the policy to:

- process logs from background processes;
- execute_code stdout cap;
- cron script-output injection into agent prompts;
- browser snapshot compaction, only after separate UI/proof-preservation tests;
- file reads only for optional summarization, not line-numbered evidence reads.

### Phase 5: Optional plugin DSL or rule config

If native stages are not enough, add declarative per-tool policy config with a closed guard vocabulary inspired by lowfat v2. Avoid arbitrary shell filters. If external plugins are allowed, they must be opt-in, audited, and unable to override redaction/proof/permission gates.

## Default safety boundaries for Hermes

Any future implementation must enforce these boundaries:

- Default off for transformations; observe-only is the first safe mode.
- Always preserve non-zero exit evidence unless an explicit tested policy for that command class exists.
- Never remove or hide secret-risk warnings, redaction notices, permission decisions, taskpool proof gates, mission-envelope evidence, acceptance evidence, or test failures.
- Never weaken existing approval, Tirith/security, taskpool proof, permission, lifecycle, or mission-envelope gates.
- Never store raw outputs, full arguments, secrets, or proof bodies in the stats ledger by default.
- Always include a human-readable omitted notice when user-visible output is reduced.
- Every slimming decision must be auditable by policy id/version and reason code.
- Any exception in policy code returns the original output and logs a bounded diagnostic.
- Existing fixed caps remain as the last-resort safety net.

## Concrete Hermes policy sketch

Example policy config, intentionally default-off:

```yaml
tool_output_policy:
  enabled: false
  observe: true
  ledger_enabled: false
  default_mode: passthrough
  terminal:
    large_success:
      enabled: false
      max_tokens: 2000
      preserve_head_lines: 80
      preserve_tail_lines: 120
    protect_patterns:
      - "PROOF_JSON:"
      - "Traceback (most recent call last)"
      - "FAILED"
      - "AssertionError"
      - "permissionDecision"
      - "mission-envelope"
```

Example structured decision:

```json
{
  "policy_version": "tool-output-policy-v1",
  "mode": "passthrough",
  "reason_codes": ["exit_nonzero", "proof_sensitive"],
  "before_tokens_est": 12345,
  "after_tokens_est": 12345,
  "ledger_recorded": true,
  "raw_output_persisted": false
}
```

## Verification performed for this review

- `git -C /tmp/agent-team-2026-06-06----lowfat-e1ebe8dc7c4b/lowfat rev-parse HEAD` returned `48c30f073f43aa82bb1230100447482c3ab1e858`.
- `git -C /tmp/agent-team-2026-06-06----lowfat-e1ebe8dc7c4b/lowfat log -1 --format='%H %cI %s'` returned the reviewed commit metadata.
- `python3 /Users/charles/.hermes/scripts/brain_task_orchestrator.py list --json > /tmp/agent-team-2026-06-06----lowfat-e1ebe8dc7c4b/brain_task_orchestrator_list.json` completed successfully; the output artifact was 251190 bytes.
- Source files and docs listed above were read directly from the checkout and Hermes source checkout with line-numbered tool reads/searches.

## Final recommendation

Accept lowfat as a strong reference for output-governance methodology, not as a binary dependency. The immediate ratchet for Hermes should be a docs-backed Phase 1 design for a native, default-off, observe-only tool-output policy and metrics ledger. Implementation should be gated by focused regression tests that prove no weakening of errors, secrets, test failures, taskpool proof, permission, lifecycle, or mission-envelope evidence.
