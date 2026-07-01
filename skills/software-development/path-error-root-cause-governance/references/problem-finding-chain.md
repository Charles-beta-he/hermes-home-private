# Problem-Finding Chain

## Scope / Applicability / Anti-conditions

Scope: reusable debugging and incident-review method for software/product/runtime problems where the risk is choosing the wrong causal path before implementation.

Applicability: use for vague or cross-layer bug reports, visual/runtime anomalies, repeated failed fixes, user corrections such as “not this”, or any case where visible symptoms may be downstream of lifecycle, state, cache, deployment, platform, or control-flow mechanisms.

Anti-conditions: do not use for deterministic one-line fixes with a proven direct cause, pure implementation after root cause is already established, or task-progress storage. This reference is not project-specific and must not preserve repo names, PR numbers, branch names, local file paths, or temporary artifacts.

## Purpose

Before patching, convert a human report or artifact into a causal investigation path. This chain is independent of multi-model review. Models may supply candidate mechanisms, but evidence and falsifiers choose the path.

```text
user wording / artifact
→ intended outcome
→ time slice
→ surface owner
→ control boundary
→ candidate mechanisms
→ discriminating evidence
→ root-cause path
→ regression proof
```

## Stage Definitions

### 1. User wording / artifact

Capture the literal input: user words, screenshot, video, logs, issue text, monitoring alert, or test failure.

Do not paraphrase into a cause yet.

Ask:
- What did the user actually say is wrong?
- What artifact is being judged?
- Which details are observed facts vs interpretation?

### 2. Intended outcome

State the desired observable effect, not the suspected component.

Bad:
```text
Fix the visible widget height.
```

Good:
```text
During the reported lifecycle slice, the visible surface should occupy the intended area without a missing strip.
```

Ask:
- What should the user see, receive, or be able to do?
- What would count as fixed from the user's perspective?
- What is explicitly not part of this request?

### 3. Time slice

Many bugs look similar across different moments. Split the report into execution slices before reading code.

Common UI/runtime slices:
- T0 first paint / startup shell
- T1 loading / skeleton / transient overlay
- T2 hydrated steady state
- T3 transition / teardown
- T4 resume / back-forward / process restore
- T5 deploy / cache update / service-worker activation

Common backend/system slices:
- request entry
- validation/normalization
- persistence
- reconstruction/readback
- response projection
- async job / retry / callback
- deploy/config propagation

Ask:
- Which slice is the user judging?
- Which adjacent slice could be distracting but non-target?
- What contrast slice works correctly?

### 4. Surface owner

Identify who owns the surface/state at that slice.

Examples:
- OS shell, browser, WebView, viewport, keyboard, or system UI
- app shell, route, layout root, component, or animation layer
- store, cache, session marker, lifecycle flag, or service worker
- backend service, database, external provider, deployment, CDN, config, or runtime environment

Ask:
- Who decides the geometry/state before the suspected code runs?
- Which owner can make this exact symptom appear?
- Is the visible component causal or only downstream?

### 5. Control boundary

State what the suspected fix layer can and cannot control.

Examples:
- CSS cannot fill an area that the runtime surface never allocated.
- A component cannot show data that the API never projects.
- A frontend formatter cannot fix a backend state transition.
- A retry loop cannot fix missing auth/config propagation.

Ask:
- If this layer is patched, can it actually change the failing observation?
- What upstream decision may already have constrained the surface?
- What downstream symptoms would remain even if this patch works visually?

### 6. Candidate mechanisms

Keep at least two plausible mechanisms alive until evidence discriminates.

Template:
```text
H1: <mechanism at layer A>
If true: <specific observation>
If false: <specific counter-observation>
Minimal probe: <one command/test/screenshot/DOM readback>

H2: <mechanism at layer B>
If true: ...
If false: ...
Minimal probe: ...
```

Rules:
- Recent commits are leads, not proof.
- The most visible component is a lead, not proof.
- Model consensus is a lead, not proof.
- A hypothesis without a falsifier is not ready for patching.

### 7. Discriminating evidence

Gather evidence that separates mechanisms, not generic evidence that the bug exists.

For UI/runtime:
- time-stamped frames or screenshots per slice
- DOM existence and owner container
- computed style, visibility, opacity, position, z-index
- bounding boxes and viewport metrics
- root/app/shell height and scroll ownership
- state markers, storage, route, cache, service worker, and deployment identity

For backend/system:
- exact inbound payload
- normalized internal state
- persistence readback
- outbound projection
- config/env identity at each boundary
- current deployed artifact identity

Ask:
- Which single observation would eliminate one hypothesis?
- Does evidence cover both broken and contrast paths?
- Did the measurement hit the layer intended for patching?

### 8. Root-cause path

Patch only after the causal path is explicit:

```text
At <time slice>, <surface owner> applies <mechanism>, which constrains <control boundary>, producing <visible symptom>. The fix belongs at <owner/layer>, and regression must cover <failing path + contrast path>.
```

### 9. Regression proof

Regression should lock the problem path, not just the touched line.

Include:
- direct assertion for the failing slice/path
- contrast assertion for the neighboring non-target slice/path
- artifact readback when build/deploy transforms the source
- visual/runtime proof when the acceptance target is visual

## Stop Rules

Stop and rebuild the chain when:
- the user says “不是这个”, “你在修表现”, or corrects the target;
- the time slice cannot be named;
- the visible component appears correct but the symptom persists;
- the fix relies on platform/route/timing special cases without explaining owner/control boundary;
- no falsifier exists for the current path;
- tests pass but verify a different slice than the user target.

## Compact Working Note

```text
Problem chain
- Literal report/artifact:
- Intended outcome:
- Non-goals:
- Time slice under judgment:
- Contrast slice/path:
- Surface owner:
- Control boundary:
- H1 / prediction / falsifier / probe:
- H2 / prediction / falsifier / probe:
- Discriminating evidence:
- Root-cause path:
- Regression proof:
```

## Anti-Patterns

1. Component-first framing: “X component looks wrong, patch X.”
2. Commit-first framing: “recent commit touched Y, therefore Y is the target.”
3. Patchability bias: “I can change CSS/config, so that must be the fix layer.”
4. Time-slice drift: verifying steady state when the user reported startup/loading or transition.
5. Surface-owner blindness: patching downstream UI when platform/runtime/backend/deployment owns the failed state.
6. Consensus-as-truth: treating model agreement as evidence instead of hypothesis pressure.
