# Social-signal advisory drain runbook

Use when the user asks to continue/progress a taskpool backlog that consists of public social/media signals, research/product claims, screenshots, or tutorial articles already captured as taskpool advisory items.

Applicability:
- Public X/Twitter/Douyin/blog/video/screenshot signals were already saved as evidence and converted to taskpool cards.
- The next safe action is advisory analysis, source-boundary clarification, decision matrix, or closeout of a pending advisory card.
- The user says “继续”, “协助推进”, “全盘推进” but no exact authority exists for runtime, scheduler, external dispatch, deploy, destructive operations, or credential entry.

Anti-conditions:
- Do not use this as permission to implement a runtime feature, create cron jobs, spawn workers, publish/deploy, send external messages, or mutate credentials.
- Do not certify social-source claims, benchmark claims, repo stars, price/performance claims, or product capability claims without primary-source readback and verifier evidence.
- Do not store session progress in memory/skills; only durable procedure belongs here.

## Objective model

Success for this class of work is not “make the task disappear”; it is:

1. preserve source/access boundary;
2. separate observed text/image claims from verified facts;
3. compare against existing Hermes/taskpool/skill coverage;
4. produce a concise artifact with decision matrix;
5. move the task through lifecycle only with artifact/proof evidence;
6. keep certification/implementation gates closed unless independently proven.

## Safe bounded loop

1. Snapshot live state.
   - `brain_task_orchestrator.py next --json`
   - `brain_task_orchestrator.py list --json`
   - `brain_task_orchestrator.py selfcheck --json`

2. Pick the next advisory task only if no higher-risk exact-authority task is active.
   - Prefer pending advisory/evolution tasks whose evidence is already local.
   - If a task is in `review`, first inspect auto-close/readback before dispatching more work.

3. Read evidence and source boundaries.
   - Use local captured `.txt`/`.json`/media notes, not memory summaries.
   - If image/video evidence matters, run a fresh visual readback or use an existing artifact.
   - Redact any tokens/secrets that appeared in prior capture commands.

4. Search overlap before recommending work.
   - Search relevant skills/references and task files for the concept.
   - Mark items as `already covered`, `recertify`, `adopt as advisory vocabulary`, `child-task`, `blocked`, or `reject`.

5. Write one artifact per advisory card or coherent cluster.
   Suggested sections:
   - Source/access boundary
   - Extracted visible claims / architecture / taxonomy
   - Fresh external probes, if any
   - Hermes existing coverage
   - Decision matrix
   - Recommendation
   - Red-line confirmation

6. Bind artifact to lifecycle.
   - Compute `sha256` of the artifact.
   - Transition with structured evidence:
     - `claimed` with `artifact:<path>`
     - `running` with `artifact:<path>; proof:sha256:<hash>`
     - `review` with artifact, hash, and command/source readback notes
     - `done` only if the task is evidence/advisory and acceptance is fully satisfied

7. Verify after each tranche.
   - Run `selfcheck --json`.
   - Run `list --json` and summarize `active_total`, `by_status`, `dispatchable`.
   - State remaining active tasks and any warnings.

## Lifecycle-hook pitfall

After `transition --to review`, event hooks or auto-close logic may already move an advisory task to `done`. A later explicit `done` command can return a no-op such as `done -> done`.

Do not force the lifecycle for dashboard cleanliness. Instead:
- read back `list --json` / task status;
- confirm active count decreased or terminal status is present;
- run `selfcheck --json`;
- report the hook behavior as readback evidence if needed.

## Bounded source-grounded fixture spikes

When an advisory card asks to verify an extraction/library/source-grounding capability, do not stop at reading a social post if the task acceptance allows a local fixture. Use a scratch-only spike:

1. Verify canonical source first: repo/API/README/package metadata, license, archive status, default branch or version, and source claim boundaries.
2. Install only into an isolated scratch venv/temp directory; never into active Hermes runtime from an advisory task.
3. Prefer local/no-cloud providers when available; record if credentials, paid APIs, or unsupported Python/runtime versions block the fixture.
4. Run the smallest deterministic fixture and save raw output under the evidence directory.
5. Preserve hashes for the note and fixture outputs, then bind them to lifecycle transitions with `artifact:` and `proof:sha256:` refs.
6. Decide narrowly: `adopt as bounded fixture pattern`, `future child task`, `reject marketing claim`, or `no runtime integration`.

Example anti-patterns:
- Copying a social marketing benchmark into docs without primary-source verification.
- Installing a library into the active agent/runtime to satisfy an advisory card.
- Treating a successful local fixture as permission for default-on pipeline integration.

## Decision matrix defaults

| Source type | Default decision |
|---|---|
| Tutorial/opinion article with good vocabulary | Adopt vocabulary / recertify existing gates; no implementation. |
| Architecture diagram from credible org but no paper/code readback | Advisory note only; require official source before implementation. |
| Benchmark/performance claim from social post | Reject/blocked until primary source + comparator. |
| Loop/self-improvement claim | Require fixed evaluator, inner/outer role split, bounded meta-loop inputs, no-authority-expansion, and comparator before any runtime work. |
| Product UX workflow pattern | Consider template/reference only; do not build runtime without concrete user workflow and acceptance evidence. |

## Example red-line language

- “No runtime/worker/cron/scheduler change was made.”
- “No social-source claim was certified.”
- “This is advisory closeout, not implementation delivery.”
- “A future child task is required before any code/runtime change.”

## Verification checklist

- [ ] Live taskpool state was read, not inferred from prior context.
- [ ] Evidence artifact path and hash were attached to lifecycle transitions.
- [ ] Source facts, unverified claims, and recommendations are separated.
- [ ] Existing Hermes coverage was searched before proposing net-new work.
- [ ] `selfcheck` has fresh PASS/FAIL readback.
- [ ] Remaining warnings are classified as blocking vs advisory/soft.
