# Web Workbench Runtime Verification — 2026-07-02

Status: local runtime smoke verified; multi-model safety review degraded/advisory, not full certification.

## Multi-model safety gate

Artifacts:
- State: `/Users/charles/.hermes/runs/hewos-web-workbench-runtime-safety-20260702/state.json`
- Tick dir: `/Users/charles/.hermes/tick-20260702-113152-346711-p86418-def31985-8cd50527`
- Discussion: `/Users/charles/.hermes/tick-20260702-113152-346711-p86418-def31985-8cd50527/discussion_result.json`
- Manifest: `/Users/charles/.hermes/tick-20260702-113152-346711-p86418-def31985-8cd50527/final/certification_manifest.json`

Result:
- status: `degraded_not_certified`
- participants attempted/consulted: claude-opus-4-8, mimo-v2.5-pro, gemini-3.1-pro-preview
- usable substantive reviewers: Claude + MiMo
- Gemini route failed: unknown provider `google-gemini-cli`
- no full certification claimed

Actionable amendments absorbed:
- module docstring declares projection-only boundary;
- endpoint contract tests added;
- `/execute` and side-effect-like routes return 404;
- POST/simulation disabled for this slice;
- projection responses are JSON snapshots;
- runtime has host/port flags to avoid local port conflicts.

## Runtime smoke evidence

Server command used during smoke:

```bash
PYTHONPATH=/Users/charles/.hermes/workflows/projects/hermes-embodied-workflow-os/implementation \
python3 - <<'PY'
from hewos_core.workbench_runtime import serve
serve(port=8799)
PY
```

Curl/urllib smoke:
- `/` => 200 text/html
- `/healthz` => 200 application/json, `execution_enabled: false`
- `/projection/dashboard` => 200 application/json
- `/projection/capabilities` => 200 application/json
- `/projection/action-intents` => 200 application/json
- `/projection/evidence-ledger` => 200 application/json
- `/execute` => 404

Browser smoke:
- URL: `http://127.0.0.1:8799/`
- title: `HEWOS Workbench Static Fixture`
- visible sections: Dashboard, ActionIntent Review, EvidenceLedger
- ActionIntent risk: `physical_action`
- ActionIntent status: `blocked`
- browser console: 0 JS messages, 0 JS errors

Server process was killed after smoke.

## Automated tests

Latest command:

```bash
python3 -m unittest discover -s workflows/projects/hermes-embodied-workflow-os/implementation/tests -v
```

Result: 27 tests OK.

## Boundaries preserved

- no taskpool write
- no external dispatch
- no deploy/push
- no auth/credential path
- no hardware/robot execution
- no `/execute` endpoint
- no UI A+/uIMax claim
