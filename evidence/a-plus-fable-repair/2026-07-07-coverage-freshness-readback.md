# A+ coverage freshness readback — route/cost/UI

Timestamp: 2026-07-07T01:50:00+08:00 local

Scope: fresh local readback for Fable 5 A+ weak dimensions. No secrets printed; provider snapshot redacted by key shape.

## Route/provider freshness
- Redacted route/config snapshot captured in `/tmp/a_plus_coverage_freshness_readback.txt`.
- No token/key/password/secret values are included; suspicious key names were replaced with `[REDACTED]`.
- Fable 5 availability remains established by prior real Claude Code receipts with `modelUsage.claude-fable-5`.
- Multi-brain wrapper direct command exits 0 and records `timeout_recorded` as bounded degradation, not hard failure.

## Cost/usage freshness
- Usage wrapper readback captured in `/tmp/a_plus_coverage_freshness_readback.txt`.
- Multi-brain wrapper usage section reported `score=93.75`, `grade=A`, canonical usage score path present.
- Fable high-context audits remain explicitly cost-sensitive; coverage registry should mark high-cost model audits as budgeted/intentional.

## Portfolio freshness
- `portfolio_os_verify.py --json` returned `ok=true`, `error=0`, `warning=0` after registry/profile repair.

## HEWOS implementation freshness
- `python3 -m unittest discover -s implementation/tests -v` under HEWOS ran successfully; latest suite includes 27 tests OK in the current project codebase.

## UI/browser freshness
- Served HEWOS static workbench locally at `http://127.0.0.1:8799/workbench-static-fixture.html` from artifacts directory.
- Browser title: `HEWOS Workbench Static Fixture`.
- H1: `Workbench for evidence-led operations.`
- Regions read back: Dashboard, ActionIntent Review, EvidenceLedger, Gate ladder.
- Console readback: `console_messages=[]`, `js_errors=[]`, `total_errors=0`.
- Server was terminated after smoke; no external network, no deploy, no side effect.

## Boundary
- This proves current local UI artifact freshness only. It does not claim production UI, mobile device install, external adapter execution, or deploy readiness.
