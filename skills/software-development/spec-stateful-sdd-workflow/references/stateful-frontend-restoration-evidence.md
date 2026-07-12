# Stateful frontend restoration evidence pattern

Use for local UI preferences whose state must survive reloads without corrupting an orthogonal domain choice.

## State model

Represent distinct meanings independently. Example:

```text
lastRealPeriod = min30       # durable domain preference
activeView = depth | absent  # transient presentation mode
```

Do not store `depth` in the period key if entering depth must preserve the last real period. On leaving depth for a real period, clear the view key and update the period key.

## RED/GREEN transition matrix

| Step | Expected state |
|---|---|
| Seed real preference | period=`min30`, view absent |
| Click transient view | transient control selected; period still `min30`; view=`depth` |
| Reload | transient control still selected; period still `min30` |
| Click real period | real control selected; period=`min30`; view absent |
| Reload again | real control still selected; view absent |

RED should fail at the first missing transition and must include at least one reload. GREEN must verify the forward and reverse transitions.

## Browser-harness safeguards

- Clear cache storage and service workers for the test origin before navigation; stale bundles can create false RED/GREEN results.
- Disable network cache for the harness.
- Set the exact mobile viewport before navigation.
- Assert semantic state (`aria-pressed`, selected role/state) and storage separately.
- When the selected control sits in a horizontal scroller, call `scrollIntoView({block: 'nearest', inline: 'end'})` before screenshot capture so the visual evidence actually displays the selected affordance.
- Keep runtime harness files and screenshots in scoped project evidence, not the product repository, unless the repo explicitly owns them.

## Evidence boundary

Restoration and data completeness are different claims. A selected mode plus a visible empty grid proves that UI state restored; it does not prove data loaded or rendered. Report missing curves, rows, or values as a separate evidence gap. Do not weaken restoration assertions, synthesize data, or invent a fallback to make the screenshot look complete.

## Capability-probe stop rule

When a reference client exposes a state but the target client's read-only API rejects every candidate value while a control request succeeds:

1. record exact candidate/control responses;
2. stop implementation;
3. do not infer a hidden enum from library rendering support;
4. request an authoritative API value, valid test data, or explicit product fallback decision.

This keeps visual-library capability from being mistaken for business-contract authority.
