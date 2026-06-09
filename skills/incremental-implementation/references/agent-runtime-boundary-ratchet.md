# Agent runtime boundary ratchet reference

Session class: evolving Hermes-style agent/control-plane architecture from report-only contracts into real external-agent runtime execution without losing ledger/policy/evidence control.

## Boundary ladder used

1. Contract/projection only
   - Coverage matrix in code.
   - Worker result, fork/join graph, certification packet, artifact pointer, and workflow metadata validators.
   - No dispatch, lifecycle mutation, adapter write-through, persistent learning, outbound messages, or automatic done.

2. Ledger-only runtime start
   - Append durable JSONL run row with deterministic run id/request digest.
   - `run_status=started`, `runtime_boundary=started_ledger_only`.
   - Idempotent replay for same request digest.
   - Reject authority-smuggling keys before writing.

3. Governed builtin read-only executor
   - Consume a started run.
   - Allow only explicit builtin executor/action pairs.
   - Append completed result to ledger.
   - Keep `external_executor_invoked=false`, lifecycle unchanged, adapter write-through disabled.

4. External process probe
   - Executor-type allowlist maps to binary basename, e.g. `claude_code -> claude`, `codex -> codex`, `opencode -> opencode`.
   - Invoke only fixed `--version`; reject arbitrary command/basename drift.
   - Append receipt; keep `task_prompt_sent=false`.

5. External prompt dry-run
   - Require started run, allowlisted executor, prompt, artifact path, and evidence refs.
   - Use constrained mode where available: for Claude Code, `claude -p <prompt> --permission-mode plan --tools "" --no-session-persistence --output-format json`.
   - Capture full stdout/stderr into artifact JSON.
   - Ledger stores only pointer/hash/size/bounded summary/evidence refs.
   - Keep tools/write/lifecycle/adapter/persistent-learning disabled.

6. External readonly context packet
   - Require started run, allowlisted executor, instruction, `context_artifact_uri`, `context_sha256`, output artifact path, and evidence refs.
   - Allow only context artifact pointers/hashes in the hot path; reject `inline_context` so large evidence stays outside the run ledger and prompt request.
   - Recompute the context artifact SHA-256 before invocation and fail closed on mismatch or missing artifact.
   - Build the prompt internally from instruction + run id + task ref + context URI/hash + no-tool/no-write rules.
   - Use the same constrained agent argv as dry-run (`--permission-mode plan`, empty tools, no session persistence, structured output when supported).
   - Store full stdout/stderr in an output artifact and append only context pointer/hash plus output artifact pointer/hash/size/bounded summary/evidence refs to the ledger.

## Verification bundle

For each rung:
- Add RED tests proving the function/CLI does not exist or rejects unsafe inputs.
- Add positive test for the new allowed boundary.
- Add negative tests for authority smuggling and target drift.
- Run `py_compile` on touched modules.
- Run focused tests for the control-plane module.
- Run CLI smoke against a temporary ledger/artifact directory and read back ledger rows/artifacts.
- For real external-agent smoke, use a tiny no-tool/no-write prompt that returns a sentinel string and report any model cost observed in the tool output.
- Run `git diff --check`.
- Make a scoped commit containing only that rung and its SSOT doc update.

## Hot-path evidence rule

Never put full model transcripts, inline context blobs, or command output into the task/run hot ledger. Store large input/output as artifacts and put only:
- artifact URI
- SHA-256
- byte size for output artifacts
- bounded summary for output artifacts
- evidence refs

## Still-closed boundaries after readonly context packet

Do not open these without a separate, narrower slice:
- external agent tools
- direct workspace file reads outside the supplied artifact packet
- file edits
- shell execution
- task lifecycle mutation
- external adapter write-through
- rollback/reopen
- automatic done/closeout

## Pitfalls

- Treating "agent process invoked" as a single boundary. Split version probe, prompt dry-run, readonly context packet, readonly tools, write tools, lifecycle proposal, and adapter write-through.
- Letting command_path become arbitrary shell execution. Compare executor type to expected basename and construct argv internally.
- Passing inline context to the runtime request. Use artifact URI + SHA-256 and reject inline context before invoking the agent.
- Reporting dry-run or readonly-context success from stdout only. Persist an artifact and append its digest/pointer to the ledger.
- Letting model consensus or worker result become fact. Worker/model output remains evidence/proposal until the policy/human gate promotes it.
