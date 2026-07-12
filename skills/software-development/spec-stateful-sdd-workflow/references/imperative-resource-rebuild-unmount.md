# Imperative UI Resource Rebuild and Unmount Verification

Use this pattern when a React component owns a third-party chart/editor/map/media instance and exposes an imperative method that can destroy and recreate it.

## Ownership invariant

An effect cleanup that closes over the instance created during effect setup is insufficient when an imperative method can replace that instance later:

```ts
useEffect(() => {
  const initial = initializeResource();
  return () => dispose(initial); // leaks a later imperative replacement
}, []);
```

The component owns the **current** resource, not only the setup-time resource. Cleanup must dispose the current ref and clear ownership:

```ts
useEffect(() => {
  const initial = initializeResource();
  if (!initial) return;
  return () => {
    const current = resourceRef.current;
    if (current) dispose(current);
    resourceRef.current = null;
  };
}, [initializeResource]);
```

Applicability: an imperative API (`setTheme`, `reload`, `replaceSource`, renderer swap) can recreate the underlying resource without remounting the React component.

Anti-condition: do not use this mechanically when multiple owners intentionally share one resource or when the library's disposal contract is container-based rather than instance-based. Define ownership first.

## Required regression path

Test the exact transition that leaked:

1. Mount the real component.
2. Obtain its real imperative handle.
3. Invoke the rebuild method.
4. Verify the rebuilt resource is active.
5. Unmount or switch to the alternate view.
6. Verify the current resource is disposed and its ref/DOM ownership is gone.
7. Assert no unexpected runtime exception.

A source-string check is useful as a guard but is not sufficient evidence for lifecycle behavior.

## Browser-only harness technique

When the product has no unit-test renderer and adding a debug API would pollute production code, a local CDP harness can inspect the React fiber attached to the component DOM node, walk hook state to locate the forwarded imperative ref, and call the real method. For cleanup evidence, temporarily instrument `EventTarget.prototype.removeEventListener`, scoped to the resource container/window/document, then restore the original function immediately after unmount.

Record bounded evidence such as:

- imperative handle found;
- canvases/nodes present after rebuild;
- component DOM absent after unmount;
- listener-removal count and event types;
- unexpected exception list.

This proves that the real rebuild→unmount path exercised cleanup. It does not prove absence of every possible library-internal leak; retain that boundary in the verdict.

## Verification checklist

- [ ] Rebuild restores current domain state/data/indicators.
- [ ] Cleanup disposes `resourceRef.current`, not a stale closure value.
- [ ] Cleanup clears the ref.
- [ ] Rebuild→unmount has executable runtime evidence.
- [ ] Static guard is supplementary, not the sole proof.
- [ ] Focused lint findings are attributed with blame so historical baseline errors are not misreported as regressions.
- [ ] Independent review receives the exact target commits and a clean-worktree expectation.
