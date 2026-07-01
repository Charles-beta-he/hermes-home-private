# Agent runtime executor ratchet after ledger-only start

Extracted from `/Users/charles/.hermes/skills/incremental-implementation/SKILL.md` on 2026-07-01T08:55:33.664327+00:00 by generic core-body debt remediation. Root SKILL.md keeps a progressive-loading pointer; content is preserved here.

## Agent runtime executor ratchet after ledger-only start

When an agent/control-plane architecture has already landed contract validations and a ledger-only runtime start, promote runtime capability one authority boundary at a time. Each step must have RED tests, focused smoke, hot-path bounded evidence, and a scoped commit before the next boundary opens.

1. First consume a started run with a governed builtin read-only executor.
   - Re-read the run ledger and require a matching `run_status="started"` row.
   - Allow only named builtin executor/action pairs; reject unknown executors without appending ledger rows.
   - Append a completed run result with `external_executor_invoked=false`, lifecycle mutation disabled, adapter write-through disabled, and evidence refs preserved.

2. Then probe external agent binaries without task prompts.
   - Maintain an executor-type to binary-basename allowlist (for example `claude_code -> claude`, `codex -> codex`, `opencode -> opencode`).
   - Invoke only a fixed benign command such as `--version`; never accept arbitrary command strings.
   - Append a probe receipt to the ledger, but keep `task_prompt_sent=false`, tools disabled, lifecycle unchanged, and adapter write-through disabled.

3. Then allow no-tool/no-write external prompt dry-runs.
   - Require a previously started run, executor allowlist match, non-empty prompt, artifact path, and evidence refs.
   - Force the external agent into constrained/no-write mode (`--permission-mode plan`, empty tools list, no session persistence, structured output where available).
   - Reject prompt requests that smuggle authority fields such as lifecycle status, mark-done, external writes, memory/skill writes, outbound messages, provider config, or tools/write mode flags.
   - Capture full stdout/stderr into an external artifact; the hot ledger stores only `artifact_uri`, sha256, size, bounded summary, and evidence refs.

4. Then allow readonly context artifact packets.
   - Require a previously started run, executor allowlist match, non-empty instruction, `context_artifact_uri`, `context_sha256`, output artifact path, and evidence refs.
   - Pass only the context artifact URI/hash into the agent prompt; reject inline context so large evidence never enters the hot ledger or prompt builder by accident.
   - Recompute and verify the context artifact SHA-256 before invoking the agent.
   - Keep the same no-tool/no-write invocation constraints as prompt dry-run; capture stdout/stderr into an output artifact and append only context/output pointers, hashes, bounded summary, and evidence refs to the ledger.
   - Reject tool/write flags and authority-smuggling keys before process invocation.

5. Then accept external proposal artifacts, not facts.
   - Require a previously started run and a proposal artifact URI/hash; recompute SHA-256 before appending.
   - Accept only review proposals (`proposal_type="worker_review_proposal"`, `lifecycle_target="review_proposed"`) with non-empty summary, failure classification, top-level evidence refs, and claim-level evidence refs.
   - Reject `done`, lifecycle status, mark-done flags, external writes, memory/skill writes, outbound messages, provider/config changes, and any tool/write authority smuggling.
   - Append only proposal artifact pointer/hash/summary/counts to the ledger; preserve `allowed_to_mark_done=false`, lifecycle mutation disabled, adapter write-through disabled, and persistent learning disabled.

6. Then accept multi-model certification promotion packets, still not done.
   - Require a started run plus an already recorded proposal artifact.
   - Require certification artifact URI/hash and verify it binds to the recorded proposal artifact URI/SHA-256.
   - Require at least two reviewers, `quorum >= 2`, `quorum <= reviewer_count`, `truth_gate=true`, reviewer evidence refs, and claim evidence refs.
   - Allow only `lifecycle_target="certification_passed_for_review"`; preserve `model_consensus_is_fact=false`, `allowed_to_mark_done=false`, and lifecycle mutation disabled.
   - Append only certification pointer/hash/summary/reviewer_count/quorum/truth_gate/claim_count to the hot ledger.

7. Keep the next unopened boundary explicit.
   - After certification promotion, the still-closed boundary is human/elevated policy done authorization, lifecycle mutation, external tools, workspace file reads/edits, shell execution, adapter write-through, rollback/reopen, and automatic done.
   - Do not open readonly tools, writes, rollback/reopen, or automatic done in the same slice as proposal or certification promotion.

See also: `references/agent-runtime-boundary-ratchet.md` for the Claude Code/Codex/OpenCode runtime progression and smoke-verification bundle that motivated this pattern.
See also: `references/agent-runtime-proposal-certification-ratchet.md` for proposal artifact intake and multi-model certification promotion packet requirements.
