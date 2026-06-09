# Local overlay drift and ratchet example

Concrete findings from a Hermes local-vs-upstream audit.

## Runtime identity

- CLI executable: ~/.local/bin/hermes
- Shebang pointed to: ~/.hermes/hermes-agent/venv/bin/python3
- Runtime imports came from editable source checkout: ~/.hermes/hermes-agent

Lesson: compare versions inside the Hermes venv first; system python3 package versions can differ without affecting CLI behavior.

## Dependency vs overlay drift

Observed split:
- Hermes venv matched pyproject for openai==2.24.0 and httpx==0.28.1.
- System python3 had openai 2.30.0, which was irrelevant to CLI runtime.
- pyproject.toml and uv.lock were themselves inconsistent on hermes-agent versioning; treat that as repo-governance debt.

Lesson: package mismatch and source drift are separate failure classes.

## Local-only Codex circuit breaker behavior

Observed pattern:
- Local run_agent.py imported agent/codex_circuit_breaker.py.
- agent/codex_circuit_breaker.py was a local untracked file.
- origin/main did not contain the file or import.
- Therefore CodexCircuitOpen behavior was local-overlay drift, not upstream behavior.

Lesson: grep origin/main for the suspect symbol before attributing blame to providers or dependencies.

## Partial OpenClaw landing pattern

Observed pattern:
- agent/openclaw_control_plane.py existed and implemented helpers such as activation hints, scoped policy rendering, memory write gate, and benchmark helpers.
- agent/task_router.py did invoke activation_hints_for_text behind default-off config.
- Config keys existed in ~/.hermes/config.yaml under openclaw_control_plane.
- But prompt-builder and memory-tool mainline integration were not yet proven from the audit; helper existence alone was insufficient evidence of full landing.

Lesson: classify enhancements as helper-landed vs mainline-integrated vs certified.

## Hygiene gate reminder

Running ~/.hermes/scripts/hermes-pre-update-verify.sh failed immediately on git diff --check due to trailing whitespace in tools/mcp_tool.py.

Lesson: treat git diff --check as a hard pre-update gate. Do not start an upstream sync on a dirty tree.
