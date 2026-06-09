When diagnosing Hermes provider/version mismatch or `agent.codex_circuit_breaker` issues, verify the runtime source before blaming package versions.

Checklist
1. Resolve the actual CLI entrypoint:
   - `which hermes`
   - inspect the shebang in the launcher script
2. Confirm the Python runtime used by Hermes, not the system Python.
   - In this environment the launcher points at `~/.hermes/hermes-agent/venv/bin/python3`.
3. Confirm whether Hermes is running editable source.
   - import `run_agent` from the Hermes venv and print `run_agent.__file__`
   - inspect `sys.path`
4. Compare versions from three places separately:
   - `pyproject.toml`
   - lockfile (`uv.lock`)
   - installed packages inside the Hermes venv
5. Compare local source against upstream before concluding the bug is remote.
   - `git status --short --branch`
   - `git fetch origin`
   - `git diff origin/main -- run_agent.py ...`
   - grep upstream for the suspect symbol

Observed durable pattern
- A `CodexCircuitOpen` error can be caused by local source drift plus transport failures, even when runtime `openai`/`httpx` versions match `pyproject.toml`.
- If `agent/codex_circuit_breaker.py` is local-only or `run_agent.py` references it only in the working tree, the behavior is not upstream-consistent.
- Distinguish runtime-package mismatch from source-drift mismatch.

Interpretation rules
- If the Hermes venv has the pinned `openai`/`httpx` versions, do not blame system `python3` package versions.
- If `pyproject.toml` and `uv.lock` disagree but upstream has the same disagreement, record it as repository dependency-governance drift, not a local install bug.
- If logs show `APIConnectionError` before/inside `CodexCircuitOpen`, treat network/provider transport as a direct trigger and the breaker as a secondary guardrail.
- Historical log wording/cooldown values may differ from the current source; use that mismatch as evidence of local patch evolution rather than assuming the running behavior matches upstream.

Useful probes
- `which hermes`
- `head -n 1 ~/.local/bin/hermes`
- `~/.hermes/hermes-agent/venv/bin/python - <<'PY' ... import importlib.metadata ... PY`
- `git -C ~/.hermes/hermes-agent grep -n "codex_circuit_breaker" origin/main -- run_agent.py agent/codex_circuit_breaker.py`
- inspect `~/.hermes/config.yaml` for `model.provider`, `model.base_url`, and active model routing.
