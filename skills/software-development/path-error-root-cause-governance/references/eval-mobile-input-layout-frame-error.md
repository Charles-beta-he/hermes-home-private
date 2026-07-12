# Eval case: repeated mobile input-layout fixes should trigger frame-error gate

Scope: class-level regression/eval fixture for `single-model-frame-error-prevention.md`; applies to mobile Web/PWA/WebView input-layout incidents across projects.

Applicability:
- A soft-keyboard or input-focus layout symptom has received multiple distinct fixes.
- The patch set contains more than one layer attempting to control viewport, scroll, input visibility, or bottom action positioning.
- Tests mostly prove implementation markers/classes/tokens rather than the real input-focus user path.

Anti-conditions:
- Do not use this eval for a single deterministic layout bug with one observed owner and one failing assertion.
- Do not use this eval to store task progress, project names, branch names, PR numbers, or repository-specific component names.

## Input signal

A codebase has a mobile soft-keyboard/input-layout issue where visible symptoms include bottom action movement, header movement, input scroll snapping, typing jitter, or route-return viewport residue.

Historical evidence shows repeated fixes such as:
- stop keyboard auto-scroll;
- opt a page out of a pinned reset;
- stop manual scroll snapping to input;
- stabilize repeated typing;
- rollback/restore after the fixes.

Current patch contains multiple mechanisms for the same state variable:
- a component-level keyboard shell applied to many pages;
- route-level scroll locks;
- global/root body scroll locks;
- viewport runtime listeners and viewport-height tokens;
- keyboard inset tokens that are calculated but not clearly consumed;
- page-specific keyboard markers or escape hatches;
- input/pointer `preventDefault`, manual scroll restoration, timeout settling, or global focus/pointer listeners;
- tests that assert CSS tokens/class names/markers more than user-path behavior.

## Expected gate result

`single-model-frame-error-prevention` must return:

```text
BLOCK_IMPLEMENTATION_AND_RUN_OWNERSHIP_CONTRACT
```

It must not proceed to another local patch, because at least these stop triggers are active:
- same symptom received multiple distinct fixes and rollback;
- fixing one symptom traded into another symptom;
- route/platform/page/input special cases are growing;
- multiple controllers appear to write the same variables: viewport, document scroll, route scroll, input visibility, bottom action position;
- implementation-trace tests risk certifying patch structure rather than the keyboard user path.

## Required R-B-H-F-E-O-S output

### Representation

The problem must be rewritten as a state/path/mechanism issue:

```text
During a mobile input-focus path, browser viewport changes, document/body scroll, app shell layout, route scroller, page shell, focused input visibility, and bottom action positioning compete for ownership. The visible header/action/input symptom is downstream of missing layout-control ownership.
```

A component-only representation such as `keyboard shell bug` or `bottom action bug` fails the eval.

### Boundary

The boundary must include at least:
- browser/WebView visual viewport;
- document/body/root scroll ownership;
- app shell and route scroller;
- page keyboard shell and inner content scroller;
- footer/bottom action positioning;
- page-specific input handlers;
- tests and visual/user-path evidence.

### Hypotheses

At least three hypotheses must remain alive before solution:
1. visible component/layout bug;
2. route/app-shell ownership bug;
3. browser/document/visualViewport ownership bug;
4. multiple-controller conflict;
5. verification-path bug.

### Falsifiers

Each major hypothesis needs a falsifier. Examples:
- If component shell is root cause, disabling global viewport listeners should still leave the component scroller as the only moving scroll owner.
- If document scroll is root cause, input focus should change document/window scroll while the component scroller remains stable.
- If tests are wrong, class/token assertions should pass while screenshot/bounding-box/user-path evidence still fails.

### Evidence

Required evidence classes:
- before/focus/type/blur/route-return viewport metrics;
- window/document scroll, route scroller, page content scroller;
- activeElement and focused input bounding box;
- header and bottom action bounding boxes;
- screenshot or browser interaction evidence for at least one broken path and one contrast path.

### Ownership

Must output an owner table:

```text
Variable | Current controllers | Correct owner | Forbidden writers | Migration/removal
viewport height | browser/runtime + app/component tokens | runtime read-only state or shell contract | page components | narrow or delete extra writes
route scroll | app route scroller + global reset + page reset | route scroller | page input handlers | remove page/global resets
input visibility | browser native + shell focus helper + page preventDefault | keyboard shell inner content scroller | document/body/global listeners | keep one shell-local helper
bottom action position | action block + keyboard shell + safe-area/token hacks | page shell contract | viewport runtime | choose one shell mode
```

### Solution boundary

The only acceptable next solution is a consolidation plan that reduces controllers first:
- define one keyboard-layout ownership contract;
- remove or narrow global root/body locks, route locks, page-specific markers, and global pointer/focus preventDefault unless evidence proves they are the single owner;
- keep keyboard behavior in a shell-local contract;
- verify through user-path/browser evidence.

## Failing outputs

The eval fails if the agent:
- proposes another CSS padding/fixed/footer tweak before ownership mapping;
- treats multi-model or self-confidence as evidence;
- uses tests that only assert markers/tokens/classes as completion proof;
- adds a third escape hatch or page-specific flag;
- cannot name what observation would falsify the chosen fix.
