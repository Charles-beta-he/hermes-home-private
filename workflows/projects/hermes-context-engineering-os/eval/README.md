# Context Regression Eval

Purpose: detect context assembly regressions before runtime integration.

Current standalone fixtures are intentionally local-only and dependency-free:

- `fixtures/pass/local-foundation.json` must pass.
- `fixtures/fail/unknown-evidence-id.json` must fail source/evidence mapping.
- `fixtures/fail/missing-do-not-save.json` must fail memory landing-zone guard.
- `fixtures/fail/missing-readback.json` must fail authority readback guard.

Run:

```bash
python3 scripts/context_regression_eval.py
```

No external dispatch, scheduler, model call, taskpool lifecycle mutation, credential, deploy, or destructive action is performed.
