# Personal AI OS read-only control-room progression

Applicability: use after a broad Agent OS / Personal AI OS projection packet already exists and the user authorizes continued safe progress, especially with wording like “继续推进 / 不以阶段或人工接入为中止借口 / 直至方案落地”. This applies only while the next slice is local, reversible, read-only, and authority-safe.

Anti-conditions: do not use this pattern to open capability execution, scheduler/taskpool lifecycle writes, external dispatch, credential/secret handling, payment/legal authority, production mutation, clipboard/file export, or physical-device effects. If the next useful step crosses one of those boundaries, produce a boundary artifact and stop at exact target/rollback/readback requirements.

## Continuation rule

After each safe slice lands and passes verification, do not immediately produce a final “next step” summary. First read the current backlog/doctor/status and ask: “Is there another local, reversible, read-only slice on the ladder that preserves all hard gates?” If yes, continue implementing it in the same turn. Stop only when the remaining items are completed/local-equivalent or require a concrete authority boundary (credentials, external dispatch, lifecycle mutation, payment/legal/device effects, destructive change, or missing evidence). This rule exists because `继续推进 / 不以推进阶段与人工接入为中止借口 / 直至方案全部落地` is an execution contract, not permission to report one completed phase and pause.

## Safe progression ladder

1. Native readback surface
   - Expose the projection through a local CLI/API readback surface.
   - Keep the implementation side-effect-free and make `side_effects_executed=false` explicit in the output.
   - Tests should assert neighboring authority gates remain closed.

2. Authenticated dashboard control-room
   - Add a dashboard page or panel that consumes the read-only endpoint.
   - Show boundary flags (execution, external dispatch, runtime mutation, payment/credential action, physical-device effect) as first-class UI, not buried in raw JSON.
   - Browser-verify that the page is non-blank, the relevant panels are present, and console has zero JS errors.

3. Operator filters and deep links
   - Add local-only filters for evidence, authority records, proposal inbox, device/service nodes, and external dependency inbox.
   - Hydrate filters from URL query params and sync changes with `history.replaceState` so control-room state is reproducible without backend writes.
   - Use browser readback to prove a query URL hydrates inputs and filters visible records.

4. Receipt packet
   - Build a compact read-only receipt object from the same projection state: schema, project/packet id, counts, boundary flags, open external dependencies, findings, and `side_effects_executed=false`.
   - Expose it via CLI/API/UI if those are already safe native surfaces.
   - Do not export files or send the receipt externally unless a separate authority gate exists.

5. Operator handoff summary
   - Combine current deep-link URL, active filters, receipt counts, boundary flags, open dependencies, and side-effect flag into a copyable/read-only summary block.
   - Prefer a read-only textarea or pre block; do not auto-copy to clipboard.

6. Local integrity stamp
   - Compute a browser-local SHA-256 over the handoff summary with WebCrypto (or equivalent local hashing).
   - Display the hash as an integrity stamp and clear stale summary/hash when filter state changes.
   - Verify by recomputing the hash over the rendered summary and comparing to the displayed value.

7. Local hash verification surface
   - Add a browser-local verifier that accepts generated-or-pasted handoff text plus an expected SHA-256 hash, recomputes the hash locally, and displays `match` / `mismatch` / `error` state.
   - Prefill verifier inputs from the generated handoff summary/hash, but allow pasted text so the surface verifies handoffs without backend writes.
   - Reset stale verification status and computed hash whenever the verifier text, expected hash, or upstream filter state changes.
   - Keep the verifier display-only: no clipboard write, file export/download, network send, capability execution, lifecycle mutation, external dispatch, payment/credential/legal action, or device effect.

## Verification checklist

- Deterministic tests cover CLI/API receipt/readback behavior and assert closed gates.
- For UI-only verifier surfaces, add a source/static contract or component test that names the verifier labels/status and asserts no clipboard/download/window-open/export hooks were introduced.
- Web build/typecheck passes.
- Browser readback covers at least one filtered URL and one user interaction.
- Browser readback for a verifier must click/build the handoff, click/verify the hash, assert `verification_status: match`, independently recompute the hash over the exact textarea value, and inspect console errors.
- Browser console has zero JS errors after interaction.
- A receipt/handoff/hash claim is backed by actual output, not just implementation.
- The progress ledger/backlog records the slice as read-only and names the preserved boundaries.

## Pitfalls

- “Human handoff” wording can accidentally become a stop reason. In this pattern, handoff is a read-only artifact, not a permission boundary, so keep progressing through local reversible surfaces.
- Auto-copy/export feels convenient but silently crosses a user-boundary. Keep clipboard/file/network export separate from building and displaying local text.
- A hash is only meaningful if it is computed over the exact rendered handoff text and stale hashes are cleared when the source state changes.
- A verifier that only displays a generated hash is not enough; exercise the independent verify action and check both match and stale-state reset behavior when practical.
- Do not claim a dashboard feature from DOM-only presence. Exercise the actual button/filter and inspect console errors.