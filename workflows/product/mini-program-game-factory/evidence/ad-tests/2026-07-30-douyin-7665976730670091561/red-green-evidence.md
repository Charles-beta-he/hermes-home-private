# RED → GREEN evidence — reference-ad lane + Stack Path Runner

Tests were written and executed before any implementation existed. RED output below is verbatim (tails).

## RED 1 — reference-ad validator tests before implementation

Command:

```bash
cd workflows/product/mini-program-game-factory/07-build
python3 -m unittest -v test_reference_ad_experiment.py
```

Output (tail):

```text
test_reference_ad_experiment (unittest.loader._FailedTest) ... ERROR

======================================================================
ERROR: test_reference_ad_experiment (unittest.loader._FailedTest)
----------------------------------------------------------------------
ImportError: Failed to import test module: test_reference_ad_experiment
Traceback (most recent call last):
  File ".../unittest/loader.py", line 154, in loadTestsFromName
    module = __import__(module_name)
  File ".../07-build/test_reference_ad_experiment.py", line 14, in <module>
    from reference_ad_experiment import (
ModuleNotFoundError: No module named 'reference_ad_experiment'

----------------------------------------------------------------------
Ran 1 test in 0.000s

FAILED (errors=1)
```

## RED 2 — Stack Path Runner kernel tests before implementation

Command:

```bash
export PATH="$HOME/.nvm/versions/node/v24.14.0/bin:$PATH"
cd workflows/product/mini-program-game-factory/experiments/stack-path-runner
node --test tests/
```

Output (tail):

```text
  code: 'MODULE_NOT_FOUND',
  requireStack: []
}

Node.js v24.14.0
✖ tests (37.380625ms)
ℹ tests 1
ℹ suites 0
ℹ pass 0
ℹ fail 1
ℹ cancelled 0
ℹ skipped 0
ℹ todo 0
ℹ duration_ms 45.807416

✖ failing tests:

test at tests:1:1
✖ tests (37.380625ms)
  'test failed'
```

(`../src/kernel.js` did not exist yet — MODULE_NOT_FOUND.)

## GREEN 1 — reference-ad validator tests after implementation

Command:

```bash
cd workflows/product/mini-program-game-factory/07-build
python3 -m unittest -v test_reference_ad_experiment.py
```

Output (tail):

```text
Ran 35 tests in 0.029s

OK
```

35/35: 30 validator tests (digest binding, symlink/missing media, exact `source_type`, exact-whitelist market status, contradictory/unknown rank-hot claims, non-empty market boundary, visible-facts/inferences/unknowns, clean-room boundary, warm-up+skill-gate levels, exact-whitelist fully closed authority, determinism, non-mutation, real evidence bundle) + 5 workflow boundary tests (capability graph node/gates/cannot_satisfy, market-to-kernel gate unchanged, README/spec-packet/workflow-state boundaries).

`python3 -m py_compile reference_ad_experiment.py test_reference_ad_experiment.py` → OK.

## Independent-review remediation

The first independent Codex review rejected staged tree `d65c54eedf9e4e143dfc07ea908efb674a58fea6`: executable counterexamples showed `may_compile_work_package=true`, `may_claim_verified_current_hot=true`, `current_hot=true`, and `chart_position=1` were accepted and normalized away. Six focused tests were added first and all six failed RED. The validator now uses exact allowed-key contracts: every recognized authority field must be declared; all non-candidate fields must be exactly false; unknown authority and market-status keys fail closed; `market_status.boundary` is required and non-empty. The six focused tests then passed GREEN. The review's non-blocking `innerHTML` suggestion was also removed in favor of DOM nodes plus `textContent`; visual copy is unchanged. A fresh successor review is required after these byte changes.

## GREEN 2 — Stack Path Runner kernel tests after implementation

Command:

```bash
export PATH="$HOME/.nvm/versions/node/v24.14.0/bin:$PATH"
cd workflows/product/mini-program-game-factory/experiments/stack-path-runner
npm test   # = node --test
```

Output (tail):

```text
ℹ tests 15
ℹ suites 0
ℹ pass 15
ℹ fail 0
ℹ cancelled 0
ℹ skipped 0
ℹ todo 0
ℹ duration_ms 57.510792
```

Covers: Level 1 centered no-input win (+ surplus stack 3), Level 2 no-input loss, left-only and right-only steering losses at gap 1 with atomic (unchanged) stack, once-only obstacle penalty, insufficient-stack obstacle loss, deterministic winning trace using both steer directions across two gap checks, nonnegative-stack invariant at every observed point, fixed-trace determinism, chunked-vs-whole advance equality, steer clamping, frozen post-win state, public-state shape. `node --check` passed on `src/kernel.js`, `src/app.js`, `tests/kernel.test.js`.

Note: `node --test tests/` (explicit dir argument) misresolves under Node 24.14.0 in this layout; default discovery `node --test` is the supported invocation and is what `npm test` runs.

## Deterministic receipt readback

Command:

```bash
python3 reference_ad_experiment.py \
  --observation ../evidence/ad-tests/2026-07-30-douyin-7665976730670091561/reference-ad-observation.json \
  --mechanic-card ../evidence/ad-tests/2026-07-30-douyin-7665976730670091561/mechanic-card.json \
  --output ../evidence/ad-tests/2026-07-30-douyin-7665976730670091561/reference-ad-experiment-receipt.json
```

Result: exit 0; receipt `closure_state=reference_ad_experiment_candidate`, media sha256 `0e4c03d6049f29b559e57acf544220803b52ccf15b146b424201cf9f5e64a44d` verified against `source/ad.mp4` (regular non-symlink file), authority fully closed, `cannot_satisfy_gates` includes `verified-current-hot` and `market-to-kernel-gate`.

## Regression + hygiene runs (2026-07-30)

- Installed the lockfile-pinned runtime dependency in this isolated worktree with `npm ci --ignore-scripts --no-audit --no-fund` (1 package, exit 0), then reran the canonical regressions: the nine pre-existing 07-build suites passed 103/103 and `runtime/cocos/runtime-core` passed 17/17. No Cocos Creator GUI, platform DevTools, upload, submission, or publish action was performed.
- JSON syntax checks OK: `capability-graph.json`, `reference-ad-observation.json`, `mechanic-card.json`, `reference-ad-experiment-receipt.json`, `experiments/stack-path-runner/package.json`.
- `git diff --check` clean.
- Browser acceptance (local HTTP server, 2026-07-30): title `叠桥冲刺` loaded with zero console/JavaScript errors. Deterministic readback through the fixed `window.__STACK_PATH_RUNNER__` API proved (a) Level 1 centered/no-input -> `won`, 6 pickups, 1 gap paid, stack 3; (b) Level 2 no-input -> `lost` at the centered obstacle, stack 0; (c) the authored left+right trace -> Level 2 `won`, 13 pickups, 2 gaps paid, stack 0. Start and Level-2-win overlays were visually inspected at the rendered 9:16 stage: text and primary actions were readable and unobstructed. This is local-browser evidence only; no Cocos Creator, Douyin runtime, DevTools, device, upload or publish evidence exists.
