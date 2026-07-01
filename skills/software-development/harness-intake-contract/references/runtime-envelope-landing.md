# Runtime envelope landing pattern

Use this reference when moving `harness-intake-contract` from skill/process guidance into an actual task pipeline or envelope executor.

## Layered landing order

1. **Skill/contract layer**
   - Define the intake schema: map, goal, acceptance, division, evidence, gates.
   - Add a reusable template and trigger/counter-trigger evals.
   - Verify by reading the skill and template back.

2. **Executor prompt + proof gate layer**
   - Teach the executor to read contract fields from the envelope payload, commonly:
     - `harness_contract`, `intake_contract`, `contract`, `confirm_plan.contract`;
     - `acceptance_criteria`, `acceptance_evidence`.
   - Inject a compact `HARNESS INTAKE CONTRACT` section into the worker prompt.
   - Require final `PROOF_JSON.acceptance_criteria_covered[]` with criterion, status, deterministic evidence, and blocker.
   - Fail closed when declared acceptance exists but proof does not cover it.

3. **Pipeline payload preservation layer**
   - When converting taskpool/brain/Lark/GitHub tasks into envelopes, preserve:
     - `acceptance_criteria`, `evidence_refs`, `acceptance_evidence`, `non_goals`, `red_lines`, `workflow_contract`.
   - Build a derived `harness_contract` in the envelope payload so the executor does not lose the task's proof requirements.

4. **Live execution boundary**
   - Stop before running real `pipeline_tick` or `executor run` if it can create/consume real envelopes, wake workers, mutate task state, edit repos, or send external notifications.
   - Continue only with explicit authority for the live run.

## Verification bundle

For local reversible landing, verify with:

- syntax/compile checks for changed scripts;
- unit tests that assert the worker prompt contains the harness section;
- unit tests that declared acceptance without `acceptance_criteria_covered` fails closed;
- unit tests that task-to-envelope conversion preserves acceptance/proof fields;
- read-only stats commands are OK; live tick/run is a separate authority gate.

## Pitfalls

1. **Contract evaporation:** task records may contain acceptance, but envelope creation can drop it. Preserve contract fields at the producer boundary.
2. **Prompt-only enforcement:** telling the worker to follow acceptance is not enough; the executor must reject done proof that does not cover acceptance.
3. **Final-proof omission:** real workers may explain that an inline contract is sufficient but still omit the required final `PROOF_JSON:` line. Harden the prompt with a dedicated `FINAL OUTPUT CONTRACT`, tell proof-only smoke tasks to return PROOF_JSON immediately, and require no explanatory text after the final marker.
4. **Live-run creep:** after tests pass, do not silently run the real scheduler/executor. That crosses from local verification into control-plane side effects.
5. **Synthetic failure accounting:** controlled runtime-smoke envelopes can intentionally or accidentally create terminal FAILED records. After root-causing and fixing a synthetic failure, read back trace/proof and move the human-escape acknowledgement watermark with an explicit smoke-review reason; do not delete audit history.
6. **Broad legacy blocking:** adding fail-closed proof checks can affect old envelopes; keep changes scoped to declared acceptance fields and test the no-acceptance path for backward compatibility.
