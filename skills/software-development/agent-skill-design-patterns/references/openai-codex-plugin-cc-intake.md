# OpenAI Codex Plugin for Claude Code — Skill/Runtime Intake

Scope: reusable lessons from `openai/codex-plugin-cc` for designing agent skills, model bridges, review gates, and background-job runtimes. This is not an installation endorsement and does not treat upstream popularity or tests as proof of production safety.

## Source snapshot

- Canonical repo: `https://github.com/openai/codex-plugin-cc`
- Inspected commit: `db52e28f4d9ded852ab3942cea316258ae4ef346` (`v1.0.6`)
- License: Apache-2.0
- Inspected surfaces: README, three internal skills, rescue agent, eight commands, hook manifest/prompt, JSON review schema, JavaScript runtime, tests, release metadata, and open-issue sample.
- Local verification at this commit: `npm test` passed 91/91; `node --check` passed for all runtime `.mjs` files.

## What the project actually contains

The reusable design is larger than its three `SKILL.md` files:

1. `codex-cli-runtime` — strict internal Wrapper contract for one Codex task invocation.
2. `codex-result-handling` — result-preservation and no-auto-fix guardrail.
3. `gpt-5-4-prompting` — prompt-contract Generator with progressive references.
4. `codex-rescue` agent — proactive but intentionally thin delegation wrapper.
5. Deterministic slash commands — setup, review, adversarial review, rescue, transfer, status, result, cancel.
6. Runtime control plane — shared app-server broker, session-scoped jobs, persisted state/logs, resume/cancel/status/result, and process cleanup.
7. Stop hook — optional review gate over the immediately preceding edit-producing turn.

The effective capability is therefore:

```text
route/command -> thin agent or deterministic command -> runtime adapter -> shared Codex app-server
              -> tracked job/evidence -> structured renderer -> review/stop gate
```

## Reusable skill-design lessons

### 1. Keep the model-facing skill thin; move determinism into code

The rescue agent may shape a prompt, but it must make exactly one runtime call and return stdout unchanged. Repository inspection, job control, git target selection, state persistence, and protocol handling live in JavaScript.

Adopt when an external model/tool bridge needs stable semantics. A skill should define routing, authority, and output behavior; scripts should own parsing, process control, persistence, and retries.

### 2. Separate commands, skills, agents, and runtime adapters

- Commands are user-facing deterministic entrypoints.
- Skills are internal behavioral contracts.
- The agent is a narrowly authorized wrapper.
- Runtime code owns orchestration and lifecycle.

Do not collapse these into a monolithic “delegate to model” skill. This separation prevents recursive skill invocation and limits accidental independent work by the forwarding agent.

### 3. Use capability-specific authority defaults

- Native and adversarial review are read-only.
- Rescue implementation defaults to write-capable unless the user asks for diagnosis/research/read-only.
- Review results may not trigger automatic fixes; a fresh user choice is required.
- Setup may offer installation but asks before global npm mutation.

Generalize as an authority matrix per route, not one global model permission.

### 4. Make output an artifact contract

The review schema requires verdict, summary, severity-ordered findings, exact file/line ranges, confidence, recommendation, and next steps. Result handling preserves uncertainty and refuses to invent substitute output after failed invocation.

For reviewer skills, pair prompt instructions with machine validation and graceful rendering of malformed output. Do not let a renderer turn incomplete data into a false success.

### 5. Treat prompting as composable contracts

The prompting skill uses selective XML blocks:

- task
- structured/compact output contract
- default follow-through policy
- completeness and verification loops
- missing-context and grounding rules
- action safety
- research mode
- deeper-review nudge

The key lesson is not “always use XML”; it is to select the smallest stable contract blocks needed by the route. Tighten task/output/evidence contracts before raising reasoning effort.

### 6. Background delegation needs a real lifecycle

The project models jobs with IDs, phases, logs, stored results, session scoping, resume, cancellation, and SessionEnd cleanup. A background call without status/result/cancel/readback is not a complete agent capability.

Required reusable nodes:

```yaml
- dispatch
- durable_job_record
- progress_log
- status_readback
- result_readback
- cancellation
- stale_job_reconciliation
- session_cleanup
- timeout_or_watchdog
```

The last two cannot be inferred from “background supported”; they need tests and runtime evidence.

### 7. Review gates must bind to the exact change slice

The stop prompt reviews only direct edits from the immediately previous Claude turn, verifies edits from repository state, and allows status/setup/report-only turns. This avoids blocking on stale changes.

Generalize completion gates as:

```text
current claim -> exact action slice -> repository/tool evidence -> allow/block
```

Never let an aggregate prior-session condition prove the current task.

### 8. Shared runtimes require semantic health, not socket existence

A shared app-server broker saves startup cost, but open upstream reports identify races, stale/wedged brokers, unbounded handshakes, concurrent state writers, and inherited unrelated MCP configuration. Reuse must be conditional on a bounded semantic round trip and scoped capability profile.

Recommended bridge contract:

- generation/runtime ID
- connect and initialize deadlines
- health-check evidence
- fallback or restart path
- single-writer/atomic state updates
- PID/liveness reconciliation
- explicit tool/MCP allowlist for headless runs

### 9. Parsing and shell boundaries are part of the skill contract

The v1.0.6 release removed shell expansion for git commands. Open reports still flag unknown-option swallowing and prompt re-tokenization where prose resembling flags can alter routing.

Use structured argv parsing, `--` separators where supported, literal subprocess argument arrays, strict option allowlists, and tests where quoted prose contains `--model`, backslashes, or shell metacharacters. Never interpolate task text into a shell command.

### 10. Session transfer is a privacy and provenance boundary

The transfer route restricts sources to `~/.claude/projects`, uses the native importer, and returns a resumable Codex thread ID. A transferable transcript is not “just context”: validate source containment, preserve provenance, avoid secret expansion, and state which local/external runtime receives the history.

## Pattern classification

| Surface | Primary pattern | Secondary mode |
|---|---|---|
| codex-cli-runtime | Wrapper | Guardrail |
| codex-result-handling | Reviewer | Guardrail |
| gpt-5-4-prompting | Generator | Inversion |
| codex-rescue agent | Router/Wrapper | Pipeline entry |
| review commands | Reviewer | Deterministic adapter |
| stop review hook | Gate | Reviewer |
| app-server/job runtime | Pipeline | Control plane |

## Gaps and caution signals at the inspected snapshot

These do not negate the design value, but block a production-ready claim:

- Open reports describe completed write jobs with no trustworthy workspace-write/result evidence.
- Background workers reportedly lack comprehensive stall/watchdog behavior and can remain stale after host termination.
- Workspace-keyed state can become undiscoverable after cwd/worktree drift.
- Shared broker concurrency/health and state-writer races remain active risk areas.
- Windows-specific hook, transfer, environment-file, and process-tree issues are reported.
- A predictable temporary state directory and unvalidated broker metadata were reported as a local multi-user IPC risk.
- The stop gate is deliberately fail-open when Codex is unavailable; that is an availability choice, not strict certification.

Treat GitHub issue reports as risk leads until reproduced or fixed/read back at a later commit.

## Hermes adaptation rule

Absorb the architecture, not the plugin wholesale:

1. Reuse thin-wrapper + deterministic-runtime separation.
2. Reuse route-specific authority and no-auto-fix review boundaries.
3. Reuse structured output/evidence contracts.
4. Require job lifecycle, stale reconciliation, bounded handshakes, and readback before claiming reliable background delegation.
5. Keep provider/model names as adapters; the stable core should be provider-neutral.
6. Do not import upstream prompts, hooks, or runtime defaults globally without route evals and isolated verification.

## Verification checklist for a derived implementation

- [ ] User-facing routes map to exact capabilities and authority.
- [ ] Forwarding agents cannot inspect/modify outside their wrapper contract.
- [ ] Task text never enters shell interpolation.
- [ ] Reviews cannot silently mutate code.
- [ ] Structured outputs are schema-validated and preserve uncertainty.
- [ ] Every background job has status/result/cancel plus stale/liveness reconciliation.
- [ ] Shared runtimes have bounded semantic health checks and fallback.
- [ ] Completion/review gates bind to the exact current edit slice.
- [ ] Session transfer validates source containment and provenance.
- [ ] Cross-platform and concurrent-state tests exist.
