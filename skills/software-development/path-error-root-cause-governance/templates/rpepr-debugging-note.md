# RPEPR Path-Error Debugging Note

Use this as a working note before applying a third patch or when the user challenges the frame.

## 1. Representation

Surface:

Path that fails:

Contrast path that works:

State/path/mechanism sentence:

## 2. Proof Matrix

| Layer | Broken path evidence | Contrast path evidence | Interpretation |
|---|---|---|---|
| DOM/render | | | |
| CSS/computed | | | |
| Geometry/rect | | | |
| Root/shell ownership | | | |
| State markers/storage | | | |
| Lifecycle/timers/effects | | | |
| Cache/deploy/version | | | |
| Auth/route/API | | | |

## 3. Competing Hypotheses

### H1

Mechanism:

Prediction if true:

Falsifier:

Minimal test:

### H2

Mechanism:

Prediction if true:

Falsifier:

Minimal test:

### H3

Mechanism:

Prediction if true:

Falsifier:

Minimal test:

## 4. Entry Gate

Chosen path:

Why this explains broken path:

Why this explains contrast path:

What would make this path wrong:

Why lower-level visible-component patches are rejected/deferred:

## 5. Fix and Regression

Smallest root-cause fix:

Regression test path:

Contrast test path:

Build/type/lint gate:

## 6. Landing Zone

What is one-off session evidence:

What is project-specific fact:

What is reusable procedure/pitfall:

What needs ADR/runtime gate/taskpool follow-up:
