# Self-evolution proposal boundary

Scope: use when absorbing an upstream self-evolving agent/runtime (memory extraction, skill distillation, sentinel/nudge, agent-case mining) into Hermes or another governed agent system.

Applicability:
- The upstream runtime has useful evidence/artifacts, but direct integration could mutate memory, skills, lifecycle state, schedulers, gateways, or external platforms.
- The user broadly authorizes progress and asks not to stop on generic human gates.
- You need a safe first runtime-facing slice that is more than a report but less than autonomous promotion.

Anti-conditions:
- Do not use this as authority to enable third-party runtime daemons, gateway/sentinel processes, cron jobs, external dispatch, direct memory writes, direct skill writes, credential reads, payment, push/deploy, or destructive actions.
- Do not claim full self-evolution from upstream integration tests or mock extractors. Classify evidence level explicitly.

## Boundary ladder

1. Isolated upstream proof
   - Run upstream benchmark in an isolated HOME/root/workspace.
   - Record exact evidence JSON/logs and artifact census.
   - Classify independently: user-memory roundtrip, agent-case extraction, skill artifact (`SKILL.md`) production, recall hit, no residual daemon.

2. Evidence projection, not runtime integration
   - Add a default-off local doctor/projection that reads only local evidence files.
   - Output a proposal packet with explicit booleans:
     - `runtime_mutation=false`
     - `external_dispatch=false`
     - `daemon_started=false`
     - `cron_created=false`
     - `credential_read=false`
     - `direct_memory_write=false`
     - `direct_skill_write=false`
     - `auto_promote=false`
   - Capability levels should be named conservatively, e.g. `memory_roundtrip_proven`, `memory_roundtrip_and_agent_case_proven`, `agent_skill_artifact_proven`.

3. Local proposal receipt
   - Optionally materialize a local receipt JSON under the project/AgentOS evidence ledger.
   - Receipt is a readback/proposal artifact only; it is not a lifecycle fact, memory write, or skill patch.

4. Candidate pack / dry-run diff
   - The next automation rung after a local proposal receipt is a candidate pack, not direct promotion.
   - Candidate pack shape should include an `experience_atom` (usually `status=promoted_candidate`, `landing_zone=skill` or `taskpool`) plus a dry-run diff preview.
   - The dry-run diff must keep `write_enabled=false` and include target skill/reference names, evidence refs, anti-conditions, falsifiers, and a preview only; it must not call `skill_manage`, memory writes, schedulers, or external adapters.

5. Fixture-only patch packet before real promotion
   - Convert a candidate pack into a patch packet with `mode=fixture_only`, `real_target_write_enabled=false`, and closed side-effect booleans.
   - Add a verifier that rejects deletes/replacements, unsupported operations, non-allowlisted target skills, `direct_skill_write=true`, `direct_memory_write=true`, and real-target write flags.
   - Apply the patch only to a temporary skill fixture/copy first. Record before/after hashes, `fixture_touched`, and `real_target_touched=false`.
   - Read back the real target skill to prove the generated addendum was not written there.

6. Exact promotion gate before real skill write
   - Convert a fixture-verified patch packet into `promotion_gate.v1` before any real skill write path exists.
   - The gate must bind exact target skill path, target hash, patch packet hash, fixture receipt path, rollback/backup requirement, and post-action readback requirement.
   - Real apply remains default-off and must require both gate authority (`execute_real_skill_write=true`) and a separate CLI/runtime execute flag. Missing either must produce a blocked receipt with `real_target_touched=false`.
   - Before touching any real target, prove the same harness against a temporary target directory and read back that the actual skill was not modified.

7. Promotion remains a separate gate
   - Convert proposal to experience-ratchet/taskpool only after a separate exact gate.
   - Direct memory/skill writes need their own authority packet, evaluator, diff preview, rollback, and readback.
   - If a governance/pre-commit hook blocks committing evidence receipts, do not use `--no-verify`; either satisfy the exact missing gate or leave the generated receipt/candidate pack/fixture receipt as an uncommitted local readback artifact and report that boundary clearly.

## TDD and verification checklist

- Write RED tests for: evidence-to-proposal conversion, missing evidence safe-off, doctor/CLI fast path, optional receipt materialization, candidate-pack generation, dry-run diff output, fixture-only patch-packet generation, unsafe operation rejection, and temporary fixture apply.
- Verify GREEN with targeted tests and py_compile.
- Smoke the real CLI using the current evidence file for receipt, candidate-pack, patch-packet, and fixture-apply outputs.
- Assert receipt/candidate/patch/fixture fields preserve all closed-side-effect booleans, assert any diff preview has `write_enabled=false`, and assert fixture receipts show `real_target_touched=false`.
- For patch packets, assert deletes/replacements are rejected and only allowlisted append operations can pass.
- Check no residual benchmark processes before claiming proof.
- If an outer governance/pre-commit hook blocks a ledger receipt commit, do not bypass it with `--no-verify`; leave the receipt as an uncommitted local artifact or add the missing canonical evidence required by the hook.

## Local OpenAI-compatible provider pitfall

When a local provider is exposed at `127.0.0.1` or `localhost` (for example Ollama OpenAI-compatible endpoints), Python OpenAI/httpx may inherit `HTTP_PROXY`, `HTTPS_PROXY`, or `ALL_PROXY` and route localhost traffic through a proxy. Before concluding the provider or upstream runtime is broken, run the proof with those proxy variables unset and `NO_PROXY=127.0.0.1,localhost` (plus lowercase `no_proxy`). Then verify chat and embedding probes separately before the full benchmark.
