# Structured Semantic Authority Continuation — Read-Only Certification Pattern

## Applicability

Use when certifying that structured semantic authority survives task-producer continuation paths such as inbox ingestion, wrapper commands, or repair-child creation.

Anti-conditions:

- Do not write to the live task root merely to test rejection.
- Do not infer semantic authority from titles, body text, truth/evidence prose, or legacy metadata.
- Do not treat a green evaluator test as proof that every producer propagates the envelope.

## Certification procedure

1. Pin the exact source bytes with SHA-256 and state whether the worktree is uncommitted. Bind the verdict to bytes, not an assumed commit.
2. Read the evaluator, capability registry, orchestrator producer paths, and focused tests.
3. AST-enumerate every internal call to the canonical task-creation sink (for example `command_add`). Report enclosing producer, call line, argument expression, and the source of `semantic_intent_json`.
4. Distinguish the direct CLI dispatch call from wrapper producers: the direct call may receive the parser namespace rather than construct a new keyword.
5. Verify inbox continuation:
   - only the explicit CLI envelope is forwarded;
   - semantic-looking body/title text is ignored;
   - missing, malformed, invalid, and legacy-conflicting envelopes fail closed on a strict root.
6. Verify repair-child continuation:
   - inherit only when the parent marker is exactly validated and the envelope is structured;
   - revalidate the inherited envelope at the canonical sink;
   - missing, unvalidated, or invalid parents fail closed;
   - compare inherited envelope equality and assert no expansion of lane, task class, brain profile, side-effect class, learning, or multimodel authority.
7. Probe multimodel precedence independently:
   - `truth_gate` alone and `evidence_bundle` alone must not activate ordinary tasks;
   - explicit `requires_multimodel`, reason, or participants remain explicit signals;
   - structured `mode=forbidden` must dominate runtime/legacy triggers;
   - forbidden plus explicit legacy activation fields must conflict rather than silently merge.
8. Run focused deterministic tests plus tempfile probes. Mock live hooks and task writes; keep all writable paths under `TemporaryDirectory`.
9. Produce a claim-linked verdict with blockers, material issues, command evidence, hashes, and explicit boundaries.

## Important pitfalls

- **Requested test-count drift:** report the actual discovered/run count. A request saying “22 tests” may describe the previous slice while the current suite contains 23 after an added negative test. Count drift is not itself failure when all intended tests are identified and pass.
- **Marker-only trust:** a `validated` marker is insufficient by itself. The child path must send the envelope through the canonical evaluator again.
- **Legacy-field shadow authority:** copying parent lane/project/priority is not automatically an authority expansion, but lane must be checked against semantic routing and all authority-bearing fields must remain envelope-controlled.
- **AST false gap:** a `main -> command_add(args)` call has no local `semantic_intent_json=` keyword; verify that its parser namespace defines the option before flagging it.
- **Dirty-worktree ambiguity:** a successful review of current files does not certify a commit or staged artifact. Record hashes and scope the vote to current bytes.

## Minimal evidence schema

```text
vote: approve|amend|reject
blocking_issues: []
material_issues: []
producer_inventory: [{producer, call_line, semantic_path}]
negative_probes: [{case, expected, observed}]
tests: {command, actual_count, result}
hashes: {path: sha256}
boundaries: [no live taskpool writes, no external operations, verdict bound to current bytes]
```
