# UUMit A2A/MCP convergence evidence repair — 2026-06-14

Scope: parent task `2026-06-06-uumit-a2a-mcp-只读观察-adapter-spike禁止凭证-写操作-ut-消费` and the regenerated 2026-06-14 convergence children created after `auto-split-non-convergence` encountered a pruned historical discussion artifact.

Boundary:
- Read-only evidence repair only.
- No credentials, no writes to UUMit, no UT spend, no MCP tool execution.
- Parent objective remains frozen: UUMit A2A/MCP read-only adapter spike.
- This repair supplements convergence evidence; it does not claim production adapter runtime rollout.

## Source evidence used

Existing completed child notes and parent proof log already contain deterministic read-only evidence:
- Public probe script: `/Users/charles/.hermes/scripts/uumit_readonly_probe.py`
- Latest probe output: `/tmp/uumit_readonly_probe_latest.json`
- Durable probe evidence: `/Users/charles/.hermes/docs/private/evidence/uumit-readonly-probe-20260606.json`
- Parent proof: OpenAPI 164 paths / 286 schemas, Agent Card `UUAgent Platform`, public stats, MCP SSE HTTP 200 endpoint event, A2A unauth guard HTTP 401.
- Existing convergence children from 2026-06-12 cover `quota_observability`, `fallback_threshold`, `patch_normalization`, `framing`, and `relay_ordering` as advisory/deterministic narrowed briefs.

## Axis repair decisions

### quota_observability

Decision: quota/usage observability for this adapter must be local and fail-closed.

Evidence contract:
- Treat public read-only probes as zero-credential, zero-spend capability checks.
- Any future authenticated MCP/A2A action, UT spend, query-param key, or direct global MCP install is outside this task and requires a separate human gate.
- If quota/usage state is unavailable or stale, the adapter remains observe-only and must not auto-apply/review/deliver.

Closeout criterion for child: narrowed brief records quota source, confidence, unknown handling, and file-backed evidence locations.

### fallback_threshold

Decision: noop is the default when budget/quota/safety state is unknown; change is allowed only when the requested action is read-only and the deterministic evidence bundle is fresh.

Thresholds:
- `read_only_public_probe`: allowed when no credentials, no writes, no spend, and timeout-bounded.
- `mcp_sse_handshake`: allowed only as HTTP event-stream handshake, not tool execution.
- `a2a_unauth_guard`: allowed only to confirm expected 401/unauth response.
- `authenticated_action`, `UT_spend`, `write_operation`, `auto_apply`, `global_mcp_install`: blocked until a separate authority gate exists.

Noop-vs-change rule:
- Choose noop if quota is unknown, probe evidence is missing/stale, or a call would cross auth/write/spend boundary.
- Choose bounded change only for local task note/evidence repair and read-only probe artifacts.

Closeout criterion for child: narrowed brief covers trigger thresholds, allowed fallback actions, and explicit noop-vs-change criteria.

### framing

Decision: frame UUMit as a read-only observation/intake adapter candidate, not as an execution or spend integration.

Acceptance frame:
- The current deliverable is evidence-backed capability mapping and safety boundary definition.
- Implementation-class work must be a later task with separate adapter contract, tests, and execution-flow gate.
- Parent ratification should judge whether the read-only adapter spike is sufficiently evidenced, not whether a production integration exists.

Closeout criterion for child: narrowed brief preserves parent objective, separates advisory/intake evidence from runtime implementation, and records residual boundary.

## Residual parent boundary

The parent may still require parent-level multimodel certification refresh. If the gate remains `FAIL/CONTINUE_LOOP`, the safe states are:
- keep parent blocked while children finish and certification is unavailable; or
- archive the parent as terminal advisory/intake evidence if no safe certifying path remains.

Do not mark the parent `done` unless lifecycle/multimodel gates pass with structured evidence.
