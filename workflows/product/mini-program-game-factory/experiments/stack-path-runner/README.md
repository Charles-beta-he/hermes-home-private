# 叠桥冲刺 (Stack Path Runner)

Original candidate-only two-level browser vertical slice for the `mini-program-game-factory` reference-ad experiment lane. Zero dependencies; pure ESM.

Promise: 第一关只是热身，第二关才是真本事。

## Boundaries

- Clean-room original design. No source-video art, audio, geometry, colors, copy or values are used; the reference MP4/frames stay in `../../evidence/ad-tests/` as evidence only.
- Local browser candidate only. This is **not** Cocos Creator, Douyin runtime, DevTools, device, submission or publish evidence, and it cannot satisfy the `verified-current-hot` market-to-kernel gate.

## Layout

- `src/kernel.js` — deterministic gameplay kernel: automatic forward motion, horizontal steering in [-1, 1], +1 stack pickups (once each), once-only obstacle penalties, atomic gap spending, nonnegative stack, win/loss. Level 1 (`warm-up`) wins with no input while centered; Level 2 (`skill-gate`) has split left/right pickup lanes, a centered obstacle and two gap budgets — no-input play must lose. `LEVEL2_WINNING_TRACE` is a deterministic winning steering trace.
- `tests/kernel.test.js` — `node --test` suite covering all rules above plus determinism and clamping.
- `index.html` / `styles.css` / `src/app.js` — mobile-first 9:16 Canvas presentation (navy/teal/amber), pointer drag + arrow-key steering, stack/progress/level HUD, restart, Level 1 → Level 2 progression, result overlay, accessible buttons and `aria-live` status, `prefers-reduced-motion` respected.

## Run

```bash
export PATH="$HOME/.nvm/versions/node/v24.14.0/bin:$PATH"
node --test            # kernel tests (or: npm test)
python3 -m http.server 8123   # then open http://localhost:8123/
```

## Browser test API

`window.__STACK_PATH_RUNNER__` exposes fixed verbs only (no eval, no arbitrary commands):

- `startLevel(levelNumber)` — start level 1 or 2.
- `setSteer(value)` — steering input, clamped to [-1, 1].
- `advance(seconds, optionalStep)` — deterministically drive the simulation (works while stopped).
- `getState()` — `{screen, paused, levelNumber, status, stack, progress, ...}` readback.
- `restart()` — restart the current level.
- `stop()` / `resume()` — pause/resume the animation loop for deterministic driving.

Example acceptance drive:

```js
const api = window.__STACK_PATH_RUNNER__;
api.stop();
api.startLevel(1);
api.advance(8);            // level 1 wins with no input
api.startLevel(2);
api.advance(14);           // level 2 loses with no input
```
