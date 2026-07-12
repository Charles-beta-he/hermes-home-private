# Imperative Frontend Resource-Replacement Lifecycle

Use this when a React/Vue/UI owner can recreate a chart, editor, map, WebSocket, worker, observer, media stream, or third-party SDK instance from both declarative lifecycle code and an imperative API.

## Applicability and anti-conditions

Apply when a live resource is held in a ref/field, replacement can occur through multiple paths, and unmount/shutdown must release the latest resource. Do not apply to immutable values or resources whose ownership is explicitly transferred to another owner.

## Ownership invariant

At every point there is one authoritative current instance. Every replaced instance is released, and terminal cleanup releases **the current instance**, not merely the instance captured by an earlier effect.

Common defect:

```ts
useEffect(() => {
  const instance = initialize();
  return () => dispose(instance); // stale after imperative replacement
}, []);

useImperativeHandle(ref, () => ({
  rebuild() {
    current.current = initialize();
  }
}));
```

After `rebuild()`, unmount disposes the old captured instance while the replacement survives.

Safer designs:

- terminal cleanup reads, disposes, and clears the authoritative current ref;
- one owner atomically disposes old, installs new, and records ownership;
- imperative requests update declarative state so the normal effect owns replacement;
- a generation/token prevents stale cleanup from disposing or clearing a newer instance.

## Review procedure

1. Identify the authoritative owner (`ref`, field, registry entry).
2. Enumerate creation paths: mount, prop change, retry, theme change, imperative ref, reconnect, hot reload.
3. Enumerate release paths: replacement, unmount, error rollback, route change, cancellation.
4. Build transitions: `create A → replace with B → replace with C → unmount`.
5. Prove A and B are released during replacement and C during unmount.
6. Check stale cleanup cannot clear/dispose a newer instance.
7. Check auxiliary state is restored consistently: data, panes/plugins, subscriptions, callbacks, styles, loading state.
8. Check replacement failures leave either the prior valid instance or a clean empty state—not a half-owned resource.

## Executable evidence

Static string checks can prove API shape but not lifecycle ownership. Add a behavior test that records instance identities and disposal calls:

- mount creates A;
- imperative/declarative rebuild releases A and creates B;
- optional second rebuild releases B and creates C;
- unmount releases the latest instance;
- no created instance remains live;
- stale cleanup does not release the current instance early.

For visual resources, pair identity/disposal assertions with a runtime smoke proving user-visible state survives rebuild. DOM attributes or pane counts alone do not prove terminal cleanup.

## Review severity

When a change explicitly claims lifecycle hardening, a replacement instance surviving owner unmount is a blocking lifecycle/resource-leak finding. Cite the exact replacement path, stale cleanup closure, and missing transition test rather than reporting only a speculative “memory leak.”
