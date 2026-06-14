# Control Console live session/readback verification

Use this when verifying Hermes-style local control consoles whose UI state is a projection of both a static dashboard snapshot and a live local API.

## Durable lesson

A local UI can show stale authorization state even when the backend is already armed if the frontend only reads `public/hermes-dashboard.json`. For writable controls, browser acceptance must prove the full chain:

1. Start the console through the same production/local supervisor path the user will use, not a mismatched manual API process plus a separate dev server.
2. Verify both surfaces are live:
   - UI server responds on the expected frontend port.
   - Local API `/api/console/health` responds and reports the expected capability/session state.
3. In the frontend, merge or otherwise consume live health/session state before deciding whether action buttons are authorized. A stale generated snapshot must not be the only source for short-lived capability state.
4. Click the actual button in the browser, not only a direct API call.
5. Read back all three evidence layers:
   - UI receipt text and button pressed/disabled state.
   - Local ledger row showing the write/override/idempotent result.
   - Regenerated dashboard snapshot showing `latestByTarget` or equivalent projection.
6. Check browser console errors after the interaction.
7. Commit only source/tests; keep generated runtime snapshots out of the scoped commit unless the project explicitly tracks them as fixtures.

## Pitfall: health probes that time out by not consuming the response

For Python `http.server`-style local APIs, a readiness probe that opens a response but does not fully consume/close it can produce `BrokenPipeError`/`ConnectionResetError` server noise or false startup failure under some runtimes. Prefer a deterministic probe that reads and closes the response, for example with `http.client.HTTPConnection`:

```python
connection = http.client.HTTPConnection("127.0.0.1", port, timeout=0.6)
try:
    connection.request("GET", "/api/console/health")
    response = connection.getresponse()
    response.read()
    return response.status == 200
finally:
    connection.close()
```

This is especially important when a supervisor refuses to start the frontend unless the local API health check passes.

## Anti-patterns

- Declaring the UI fixed because buttons are no longer `disabled` without proving the write/readback chain.
- Manually arming an API process with a different token/session than the browser/dev-server path and then treating UI failures as frontend bugs.
- Letting stale generated snapshots govern short-lived capability/session state.
- Committing generated dashboard snapshots from a real verification run as part of a source-code fix.
