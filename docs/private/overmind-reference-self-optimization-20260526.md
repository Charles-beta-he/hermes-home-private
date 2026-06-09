# Overmind Reference Self-Optimization Review — 2026-05-26

Source boundary:
- Repository: https://github.com/DarthSim/overmind
- Cloned at: /Users/charles/.hermes/runs/overmind-reference-review-20260526-014644
- Commit: f57a6d00fc8b2eafd1d12014283eea25c7132d6e
- Scope: reference-architecture extraction for Hermes Agent hardening; no direct Overmind/tmux integration in this turn.
- Multi-model run: /Users/charles/.hermes/tick-20260525-174802-222443-p12907-490b36d3-4722623b

## Evidence read

- README.md lines 16-20: Overmind is a Procfile process manager built around tmux; its value proposition is preserving terminal-like output instead of treating process output as ordinary log files.
- README.md lines 40-49: differentiators include tmux-backed process sessions, attaching to a process, per-process restart, `can-die`, auto-restart, tmux control-mode output capture, and env-file configuration.
- main.go lines 36-69 and 175-203: command surface is explicit (`start`, `restart`, `stop`, `connect`, `quit`, `kill`, `run`, `echo`, `status`) and flags map consistently to `OVERMIND_*` env vars.
- main.go lines 206-231: env loading is layered and explicit: `~/.overmind.env`, `./.overmind.env`, `./.env` unless `OVERMIND_SKIP_ENV`, plus comma-separated `OVERMIND_ENV` extras.
- start/command.go lines 41-115: each run creates a unique `overmind-<session>-<nanoid>` instance, isolated temp script directory, process list, command-center socket, and tmux client.
- start/command.go lines 118-165 and 225-263: shutdown is two-phase: wait for done/stop, send configured stop signal, wait timeout, then kill; temp scripts and output fan-in are cleaned up with defers.
- start/process.go lines 16-39 and 171-212: process lifecycle is an explicit state machine (`canDie`, `autoRestart`, `keepingAlive`, `dead`, `interrupted`, `restart`) with observe/respawn behavior.
- start/tmux.go lines 69-115, 125-163, 182-201: tmux `-C` control mode is used to map pane IDs/PIDs and stream output; unexpected tmux exit is treated as fatal and the session is killed.
- start/multi_output.go lines 20-77 and 101-148: output is centralized through one fan-in channel, with process-prefixed colored lines, optional timestamps, echo subscribers, buffer pooling, and explicit Stop drain.
- .github/workflows/build.yml and lint.yml: validation runs build/lint, but `go test ./...` locally reports no test files. This is a caution: copy operational patterns, not the test coverage gap.

## Multi-model conclusion

Three real planners were consulted: `claude-opus-4-7`, `gpt-5.5`, and `mimo-v2.5-pro`.

Consensus was deliberately conservative:
- Fan-out quorum was met, but discussion did not fully certify a code change.
- Claude and GPT both preferred a doc/governance artifact first because the evidence proves Overmind behavior, not an already-confirmed Hermes bug.
- MiMo proposed additional future skill/selfcheck work, but also identified the same core patterns: lifecycle state machine, layered env precedence, output fan-in, instance isolation, and graceful stop/kill semantics.

Decision: land this scoped private reference note now; defer code/skill changes until Hermes-internal evidence confirms a concrete gap.

## Transferable patterns for Hermes

### 1. Lifecycle state should be first-class, not inferred from logs

Overmind models each supervised process with durable booleans and transitions: running check, interrupt, kill, restart request, auto-restart, allowed-to-die, keeping-alive, dead, respawn.

Hermes mapping:
- Background processes, taskpool agents, gateway bridges, cron-launched scripts, and long-running external-control adapters should expose explicit lifecycle states.
- A future Hermes verifier should prefer a state object over ad-hoc log parsing: `started -> running -> stopping -> killed|exited|restarting|dead`, plus policy bits such as `can_die`, `auto_restart`, and `grace_timeout_s`.
- Do not claim healthy just because a process exists; verify the process state plus its command-center/API readiness signal.

### 2. Graceful shutdown requires an escalation ladder

Overmind stops by signal, waits for a configured timeout, then kills. It also cleans temporary scripts and drains output.

Hermes mapping:
- Any Hermes-managed daemon/bridge should have a documented stop ladder: polite stop, readiness drain, bounded wait, force kill, cleanup, and evidence record.
- This is especially relevant for gateway bridges, Rokid/Lingzhu SSE bridges, browser harness servers, long-running taskpool workers, and background watchdog scripts.
- Future code changes should add tests around timeout and cleanup, not just happy-path start.

### 3. Layered environment loading must be explicit and profile-aware

Overmind's env precedence is easy to audit because every layer and skip flag is visible.

Hermes mapping:
- Keep Hermes provider/profile env resolution centralized and documented. Avoid parallel config loaders that bypass `hermes_cli.config.load_config()` or profile `.env` normalization.
- For any future env feature, specify order, override semantics, skip/disable flag, and which layer is safe for secrets.
- Cron, gateway, child agents, and direct CLI probes must share the same resolution semantics unless a deliberate isolation boundary is documented.

### 4. Output fan-in should preserve identity and terminal semantics

Overmind avoids treating interactive processes as plain log files. It preserves colored output and prefixes each line with a process identity.

Hermes mapping:
- Multi-agent and background-process output should be identity-prefixed and drained through a bounded, single fan-in surface before summarization.
- Tool notifications should distinguish process identity, lifecycle event, stdout/stderr, and echo/subscriber output.
- Avoid losing ANSI/terminal semantics when the user is debugging TUI/browser/CLI behavior; raw evidence should remain available even if summaries are compact.

### 5. Instance isolation prevents cross-run cleanup hazards

Overmind names each run `overmind-<session>-<nanoid>` and puts scripts/sockets under that instance boundary.

Hermes mapping:
- Any generated runtime artifact should include a run/session/chain ID and live under a request-specific directory.
- Cleanup should remove only that instance boundary, never broad shared directories.
- This pattern already fits Hermes tick dirs and should be used consistently for reference-repo analyses, browser harness state, generated scripts, and multi-model artifacts.

### 6. Command center beats one-way process spawning

Overmind can restart/stop/status/connect through a command-center socket rather than relying only on the original foreground invocation.

Hermes mapping:
- Long-running Hermes subsystems should expose a small control surface: `status`, `stop`, `restart`, `logs/echo`, and `health`.
- Before adding new background automation, decide whether it needs an operator control plane rather than just `terminal(background=true)`.

## Prioritized Hermes follow-ups

P0, done in this turn:
- Capture this reference note under `docs/private/` and commit it as a scoped Hermes self-optimization artifact.

P1, evidence needed before implementation:
- Audit Hermes background process/taskpool/gateway lifecycle surfaces for missing explicit state transitions and stop/kill escalation tests.
- Audit env loading paths for any parallel loader that bypasses the canonical Hermes config/profile resolver.
- Audit output aggregation for background notifications and subagent/taskpool logs: confirm whether raw identity-prefixed evidence is recoverable after summarization.

P2, optional skill/doc if the audits confirm recurring need:
- Create or patch a Hermes skill for process-lifecycle control-plane patterns.
- Add a selfcheck section that asserts lifecycle control surfaces exist for critical local bridges.

## Guardrails

- Do not cargo-cult tmux. The transferable idea is process control-plane semantics, not tmux itself.
- Do not alter model routing, taskpool policy, env precedence, or gateway lifecycle based only on this external reference.
- Any future code change must be backed by Hermes-internal evidence and focused tests.
- Keep unrelated existing untracked files out of the scoped commit.

## Verification used for this artifact

- `git clone --depth 1 https://github.com/DarthSim/overmind ...`
- Read README, go.mod, main.go, start/command.go, start/process.go, start/tmux.go, start/multi_output.go, and GitHub workflow files.
- `go test ./...` in the cloned repo: passed, with no test files.
- `python3 ~/.hermes/scripts/consult_models.py run ... --tier T1 --quorum 3 --discussion --max-rounds 1 --keep --timeout 240`
- Local Hermes verification is recorded in the final response and commit metadata.

## Structured T1 improvement plan

This section is the immediate scoped artifact for the 2026-05-26 Overmind reference review. It is intentionally documentation/governance only: no Overmind/tmux integration, no runtime behavior change, and no edits to unrelated untracked private docs.

### Top transferable patterns, traceable to evidence

1. Explicit command surface for lifecycle operations.
   - Evidence: E-001 / README features and E-002 / main.go command surface list `start`, `restart`, `stop`, `connect`, `quit`, `kill`, `run`, `echo`, and `status`.
   - Hermes transfer: prefer named, inspectable lifecycle actions for background processes, gateway bridges, cron-launched jobs, and taskpool workers instead of relying only on ad-hoc process IDs or log tails.

2. Layered environment/config precedence with skip/extra controls.
   - Evidence: E-002 / main.go maps CLI flags to `OVERMIND_*` and loads `~/.overmind.env`, `./.overmind.env`, `./.env`, plus `OVERMIND_ENV` extras unless skipped.
   - Hermes transfer: any future Hermes supervisor/selfcheck should report which config/env sources were considered, which were skipped, and which profile/home path is active. This aligns with Hermes' profile-aware config expectations.

3. Instance isolation and cleanup as lifecycle invariants.
   - Evidence: E-003 / command.go creates unique instance IDs, per-process temp scripts, a command-center socket, and defers cleanup.
   - Hermes transfer: long-running Hermes subsystems should expose an instance/run ID and cleanup status so stale sockets, temp directories, and orphaned workers can be detected by selfchecks.

4. Two-phase graceful shutdown before kill.
   - Evidence: E-003 / command.go sends a configured stop signal, waits a timeout, then kills.
   - Hermes transfer: gateway/platform adapters, external-control bridges, and background workers should make graceful timeout policy explicit before hard termination.

5. Process lifecycle state machine with restart/can-die semantics.
   - Evidence: E-004 / process.go models `Running`, `Stop`, `Kill`, `Restart`, `autoRestart`, `canDie`, observe, and respawn.
   - Hermes transfer: selfchecks should distinguish allowed exits from unexpected deaths and should not infer health only from a process existing.

6. Central output fan-in with prefixes, subscribers, and drain behavior.
   - Evidence: E-006 / multi_output.go centralizes output through one channel with process prefixes/colors, optional timestamps, echo subscribers, and explicit stop/drain.
   - Hermes transfer: multi-agent/taskpool/gateway diagnostics should keep source-prefixed output boundaries, especially when several agents or processes are active.

7. Treat validation gaps as caution, not a pattern to copy.
   - Evidence: E-007 / CI build/lint exists while local `go test ./...` has no tests.
   - Hermes transfer: do not cargo-cult the coverage gap. Any runtime code change inspired by this review needs Hermes-native tests or selfcheck verification first.

### Hermes gaps identified from current evidence

The supplied state and local inspection prove the reference patterns and show that `/Users/charles/.hermes/scripts/agent_systems_engineering_control_plane_selfcheck.py` currently performs brain/control-plane file and search checks. They do not prove a live Hermes runtime defect.

Therefore these are gap hypotheses, not certified bugs:

- Hermes may need a small lifecycle-contract verifier for long-running local subsystems.
- Hermes may need better source-prefixed fan-in summaries for multi-process/multi-agent diagnostics.
- Hermes may need a stale-instance/temp/socket cleanup check for local control-plane scripts.
- Hermes may need explicit can-die/auto-restart policy fields for workers or gateway adapters.

No runtime patch should be made solely from these hypotheses. The next code-bearing step must first collect Hermes-side evidence for one specific gap.

### Immediate scoped artifact to land

Land this private documentation artifact only:

- `/Users/charles/.hermes/docs/private/overmind-reference-self-optimization-20260526.md`

Do not modify or stage unrelated files, including:

- `docs/private/graph-lite-provenance-manifest-schema-20260526.md`
- `docs/private/codegraph-v094-disposable-verification-20260526.md`
- pre-existing modified source files in `agent/`, `gateway/`, `run_agent.py`, or tests.

### Verification guidance

Minimum verification for this scoped doc/governance change:

```bash
python3 -m py_compile /Users/charles/.hermes/scripts/agent_systems_engineering_control_plane_selfcheck.py
git -C /Users/charles/.hermes/hermes-agent diff -- docs/private/overmind-reference-self-optimization-20260526.md
git -C /Users/charles/.hermes/hermes-agent status --short --branch
```

If a future implementation touches Hermes runtime or scripts, broaden verification according to impact:

- scripts: `python3 -m py_compile <changed-script>` and any matching script tests.
- Hermes source: focused pytest through the repo venv or `scripts/run_tests.sh`.
- taskpool/brain: `python3 ~/.hermes/scripts/brain_task_orchestrator.py selfcheck --json` and `~/.hermes/scripts/p10-health.sh`.

### Commit guidance

Commit only this artifact if it changed:

```bash
git -C /Users/charles/.hermes/hermes-agent add docs/private/overmind-reference-self-optimization-20260526.md
git -C /Users/charles/.hermes/hermes-agent commit -m "docs: capture overmind reference self-optimization plan"
```

Before committing, confirm the staged diff contains only the Overmind reference note. Do not push unless explicitly requested.

### Next evidence request before any runtime change

A future T1/T2 implementation proposal should first answer one narrow question with Hermes-side evidence, for example:

- Which Hermes local subsystems already expose lifecycle state, graceful stop/kill policy, run IDs, and cleanup status?
- Which existing selfcheck is the correct home for a lifecycle-contract check?
- Which logs or process registries are canonical for gateway, cron, taskpool, and background-process health?

Only after that evidence exists should a concrete `add_verifier` or runtime patch be proposed.

