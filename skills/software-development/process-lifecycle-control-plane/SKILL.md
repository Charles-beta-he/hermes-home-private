---
name: process-lifecycle-control-plane
description: Use when designing, auditing, or changing Hermes-managed long-running processes, background tasks, gateways, cron workers, adapters, or any start/stop/restart/status/log control surface.
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [processes, lifecycle, control-plane, hermes, operations]
    related_skills: [hermes-agent, systematic-debugging, test-driven-development, requesting-code-review]
---

# Process Lifecycle Control Plane

## Overview

Use this skill to turn external process-manager lessons (notably Overmind-style Procfile supervision) into Hermes-safe implementation and audit steps.

The transferable pattern is not tmux. The durable pattern is an operator control plane: explicit lifecycle state, bounded shutdown escalation, identity-preserving output, scoped runtime artifacts, profile-aware environment resolution, and verifiable status/log surfaces.

## When to Use

- Changing `terminal(background=true)`, `process(...)`, taskpool workers, gateway bridges, cron workers, browser harness servers, SSE/local-device adapters, or similar long-lived processes.
- Auditing whether a daemon/worker can be safely stopped, restarted, observed, and recovered after Hermes/gateway restart.
- Adding notification, fan-in logging, PID/session recovery, profile/env propagation, or generated runtime artifact cleanup.
- Don't use for: one-shot foreground commands with no lifecycle, pure UI changes, or ordinary business logic where no process boundary is involved.

## Required Audit Order

1. Identify the instance boundary.
   - Every generated runtime artifact must include a run/session/process ID.
   - Cleanup must delete only that instance boundary, never a broad shared directory.

2. Make lifecycle state explicit.
   - Prefer state fields over log inference: `starting`, `running`, `stopping`, `exited`, `killed`, `failed`, `detached`, `recovered`.
   - Include policy bits when relevant: `can_die`, `auto_restart`, `notify_on_complete`, `watch_patterns`, `grace_timeout_s`.

3. Implement shutdown as a ladder.
   - Polite stop/TERM first.
   - Bounded wait.
   - Force kill for survivors.
   - Cleanup and checkpoint update.
   - Return the observed exit state, not a guessed success code.

4. Preserve identity in output fan-in.
   - Prefix or structure output by `session_id`, process name, command, event type, and exit code.
   - Keep raw/paginated logs available even when summaries are compact.

5. Use canonical env/profile resolution.
   - Prefer Hermes config/profile helpers over parallel env loaders.
   - For cron/profile jobs, snapshot/restore process-global env and serialize jobs that mutate global runtime state.

6. Verify command-center semantics.
   - At minimum: `status`, `stop/kill`, `logs`, and `wait/poll` should behave consistently.
   - For real daemons: add readiness/health proof, not just PID existence.

## TDD Requirements

Before production code changes:

1. Add a failing test for the lifecycle transition or control-plane contract.
2. Verify RED with the smallest targeted pytest command.
3. Implement the narrowest code change.
4. Verify GREEN with the targeted test and nearby suite.
5. Run static/syntax checks and scoped diff review before commit.

Good test targets:
- TERM-ignoring child escalates to kill after the grace timeout.
- `poll`/`wait` reconcile real process exit before reporting status.
- `kill` returns the observed exit code or a documented unavailable state.
- Notification output includes process identity and event type.
- Checkpoint recovery distinguishes host PIDs from sandbox PIDs.
- Profile/workdir env is restored after the process/job finishes.

## Common Pitfalls

1. Claiming success after sending TERM without waiting for the process to exit.
2. Treating PID existence as health; readiness must be a separate signal.
3. Dropping process identity when fan-in output is summarized.
4. Using shell-level `nohup`/`&` hacks instead of the managed background registry when Hermes needs to track lifecycle.
5. Letting cleanup operate on shared temp/cache directories instead of an instance-specific path.
6. Copying Overmind's tmux dependency or test-coverage gap instead of the process-control semantics.
7. Mutating process-global env in parallel jobs without snapshot/restore and serialization.

## Verification Checklist

- [ ] Instance/session/run ID is visible in state, logs, and artifacts.
- [ ] Stop path is TERM -> bounded wait -> KILL for survivors.
- [ ] Status is based on actual process state plus readiness when applicable.
- [ ] Output fan-in preserves process identity and raw log access.
- [ ] Env/profile resolution uses canonical Hermes helpers or documents deliberate isolation.
- [ ] Tests cover timeout/escalation and not only happy-path exit.
- [ ] Scoped diff excludes unrelated runtime/cache/doc churn.
