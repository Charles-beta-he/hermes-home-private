# External Brain Semantic Lifecycle — Convergence Evidence

Date: 2026-07-11
Verdict: SCOPED CERTIFIED — base structured semantic authority plus continuation producer-propagation and persistence slice. No external side effect exercised.

## Acceptance mapping

- AC1/AC2/AC3: `test_external_brain_semantic_contract.py` proves surface-text invariance and different envelopes overriding identical words.
- AC4: malformed, low-confidence, unknown capability, unsafe route-without-execute-authority, and high-side-effect cases fail closed. Strict configured roots require both `decision=route` and `policy.may_execute=true` before executable lifecycle states; `--force` cannot bypass this gate.
- AC5: `decide` routes to decision synthesis; durable reusable learning requires `repeated_evidence` and `writeback_classifier` and is not written automatically.
- AC6/AC7: idle taskpool is neutral for priority preemption; explicit `no_dispatchable_task` is accepted as safe idle while error-shaped denials fail.
- AC8: focused tests 23/23; brainctl tests 29/29; full orchestrator suite 118/118; py_compile PASS; live readiness semantic architecture/runtime/live-queue checks PASS.
- AC9: isolated real CLI lifecycle `add → claim → running → review → certified → done → list` passed. The first `done` was correctly rejected without project-verification evidence; it passed only after proof hash plus pytest evidence were supplied.
- AC10: only local source/config/spec/test files changed. No external send/deploy/push/destructive action occurred.

## Fresh command evidence

- `python3 -m unittest discover -s .../scripts -p 'test_external_brain*.py' -v` → 23 tests, OK.
- `python3 -m pytest -q .../scripts/test_brain_task_orchestrator.py` → 118 passed.
- `python3 -m pytest -q .../scripts/test_brainctl.py` → 29 passed.
- `python3 -m py_compile ...` → exit 0.
- `brain_task_orchestrator.py autonomy-readiness --json` → PASS, architecture_complete=true, full_runtime_activation_ready=true, no blockers; semantic architecture capability/runtime config/live queue all PASS; active=0, missing=[], invalid=[].
- Isolated CLI lifecycle → add/claim/running/review/certified all exit 0; first done exit 1 on missing project verification; second done and list exit 0 after proof hash + pytest evidence.
- `brain_task_orchestrator.py selfcheck --json` → PASS.
- `brain_task_orchestrator.py proof-check --json` → PASS.
- `brainctl.py --json memory-replay-gate` → PASS, gate_effective=true.
- `brainctl.py --json brains validate` → passed=true, 13 subbrains, default_entry=main.
- scoped `git diff --check` → exit 0.
- code/config review patch `/tmp/external-brain-code.patch` → SHA-256 `c9e8b47e2f6f1bfb9c291c1a76b402e873ea6bc104419e4c18ffe7dd588cff62`, 1898 lines; tracked diffs plus full additions for untracked semantic contract/tests/registry, with reverse-apply check PASS (evidence docs excluded).
- independent verifier `/Users/charles/.hermes/cache/delegation/subagent-summary-0-20260711_113523_968348.txt` → `vote=approve`, `blocking_issues=[]`, `material_issues=[]`; independent route-vs-execute/force/registry-corruption probes all passed.
- continuation verifier `/Users/charles/.hermes/cache/delegation/subagent-summary-0-20260711_121654_152751.txt` → `vote=approve`, `blocking_issues=[]`, `material_issues=[]`; independent tempfile probes covered inbox missing/invalid/conflicting semantics, review-child validated inheritance/no authority expansion, all six AST `command_add` call sites, and multimodel-forbidden precedence.
- continuation slice: all internal task-intake producers now have an explicit structured semantic propagation path. `add-repo-capability-absorption` and `add-work-closeout-pair` forward `--semantic-intent-json`; `ingest-inbox --write` accepts one explicit envelope and applies it to each draft without inspecting draft prose; review-gap repair children inherit only a parent `semantic_intent` marked `semantic_contract_status=validated`. `semantic_intent` dictionaries now round-trip through frontmatter as compact JSON; closeout E2E reloads both files and proves object equality plus `decision=route`. Missing/invalid/conflicting semantics still converge on canonical `command_add` fail-closed validation.

## Boundary and residual compatibility

- Legacy lexical classification remains only as `warn_only` compatibility output for tasks without `semantic_intent`; it is not promoted to semantic authority by this slice.
- Structured tasks use `fail_closed_structured_semantics` and `structured_envelope_only` authority.
- Runtime activation remains governed by existing env flags, allowlists, proof/multimodel gates, and kill switch.
- Operational-venv `post-update-check.py --fix` completed with exit 0 and no `FIX_FAILED`; canonical `brainctl ... brains validate` also passed with no errors or warnings.
- No commit was created because `scripts/brain_task_orchestrator.py` already contained unrelated concurrent unstaged changes and the repository already had unrelated staged Lark changes. Committing the whole file would violate scoped-commit isolation.

## 2026-07-11 automatic semantic knowledge recall continuation

### Scope

- AC12–AC14 automatic local-brain recall at canonical validated intake.
- Receipt persistence, worker-visible hash refs, strict lifecycle integrity/source verification, and authority-neutral grounding.
- No external dispatch, production write, real taskpool mutation, commit, push, deploy, Memory mutation, or Skill mutation.

### Final implementation evidence

- Recall queries are deterministically recomputed from the validated `TaskSemanticEnvelope`; title/body are excluded from query planning.
- Receipt binds to `sha256(canonical semantic envelope JSON)` through `semantic_envelope_hash`.
- Persisted hits accept only the bounded allowlisted schema and 64-hex content hashes; excerpts are not persisted.
- Strict executable lifecycle validates envelope digest, exact queries, hit/ref/evidence consistency, and current local-brain source membership.
- Missing, malformed, stale, unavailable, or internally consistent but forged source refs fail closed.
- Knowledge context remains `context_only_no_authority`; semantic route/execute/side-effect/multimodel/learning policy is unchanged by recall.

### Fresh verification on final implementation bytes

- `/Users/charles/.local/bin/python3.11 -m unittest scripts.test_external_brain_task_integration scripts.test_external_brain_semantic_contract`
  - `Ran 28 tests in 1.344s`; `OK`.
- `/Users/charles/.hermes/hermes-agent/venv/bin/python -m pytest -q scripts/test_brain_task_orchestrator.py`
  - `118 passed in 38.68s`.
- `/Users/charles/.hermes/hermes-agent/venv/bin/python -m pytest -q scripts/test_brainctl.py`
  - `29 passed, 8 subtests passed in 0.15s`.
- Python 3.11 `py_compile`: PASS; scoped `git diff --check`: PASS.
- `autonomy-readiness --json`: `status=PASS`, `architecture_complete=true`, `full_runtime_activation_ready=true`.
- `CHK-SEMANTIC-KNOWLEDGE-RECALL`: PASS with `bounded=true`, `deduplicated=true`, `excerpt_excluded=true`, `authority_neutral=true`, `sources_verified=true`, `validation_failures=[]`.
- Isolated actual-search lifecycle probe in `TemporaryDirectory`: six current hash-bound hits, no excerpt persisted, valid lifecycle failures `[]`, and internally consistent forged source rejected with `semantic_knowledge_recall_sources_unverified`; no real taskpool write.
- `post-update-check.py --fix`: exit 0, `FIX_FAILED=0`; existing environment/productization observations remain (`yaml` absent for hook registry selfcheck and conductor runtime disabled) and are outside this scoped recall implementation.
- Live read-only closure gates: orchestrator `selfcheck --json` PASS with zero failures; `proof-check --json` PASS with zero failures (terminal historical hash debt remains warning-only); `brainctl.py --json memory-replay-gate` PASS with `gate_effective=true` and all six fixture classes passing.

### Final implementation byte hashes before evidence-file update

- `scripts/brain_task_orchestrator.py`: `d422fda1b47274f0073508fe82d6c4b035bbeb8ff393a3f9d44d578112f9f986`
- `scripts/test_external_brain_task_integration.py`: `06a05a331571fd2965bd8c1913ad97004d302b72d47b9a57bd8b5f2787e302b6`
- `brains/semantic-capabilities.json`: `3aea9d95389cdbe8bcb7d76f486160b2fe928f605c7d06c322df6e5beb2d9abe`
- `00-spec.md`: `1c580774932b61fcde2524cfc995e60c4a3652bb750bc17019badd5b497ed48a`

### Independent review history

- Initial recall-slice verifier: REJECT because a fully forged shallow-consistent receipt could pass lifecycle.
- Remediation added canonical-envelope binding, strict receipt/ref/evidence validation, and current-source verification; the prior forged-receipt probe now fails closed.
- Final independent verifier `/Users/charles/.hermes/cache/delegation/subagent-summary-0-20260711_143627_703394.txt`: **APPROVE**, no blockers or material AC12–AC14 issues. Independent probes returned valid `[]`, forged `semantic_knowledge_recall_sources_unverified`, offline `semantic_knowledge_recall_source_verification_failed`, and bad hash `semantic_knowledge_recall_hits_invalid`; verifier hashes exactly matched the implementation hashes recorded above.

### Scoped verdict and continuation exit

**SCOPED CERTIFIED — automatic semantic knowledge recall continuation (AC12–AC14).**

The continuation exit gate is satisfied for this local reversible slice: spec mapped to current code, focused/full regressions and readiness pass, actual isolated lifecycle and negative tamper/offline/hash probes pass, source/memory/proof gates pass, final independent verifier approves the exact implementation bytes, and convergence evidence is persisted. Runtime authority boundaries remain unchanged. No commit/push/deploy/external send/real taskpool mutation was performed; repository-wide cleanliness and unrelated environment/productization observations are not promoted into this scoped verdict.
