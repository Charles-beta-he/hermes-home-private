# Cascade Cleanup: Removing a Function/Component

When deleting a function, component, or type, **never remove just the definition**.
Cascade through all dependents in one pass before building.

## Checklist

After removing a function/component/type, immediately scan for:

1. **Imports that only it used** — `grep` for the removed symbol's imports and check each one's other usages. If an import has zero remaining consumers, delete it.
2. **Helper functions it called** — if a helper (like `statusTone()`) was only used by the removed code, delete it.
3. **Literal values it referenced** — if the removed code compared against enum values that don't exist in the actual type (e.g., `tx.status === "expired"` when `TxStatus` has no `"expired"`), those comparisons are now dead code. Remove them.
4. **Test files** — update or remove tests that only tested the removed function.
5. **Re-export barrels** — check `index.ts` barrel files for re-exports of the removed symbol.

## Technique

```
# 1. Find all references to the removed symbol
grep -rn "SymbolName" src/

# 2. For each file, check if the reference is still needed
#    - Is it an import with no other usage? → remove
#    - Is it a helper called only by removed code? → remove
#    - Is it a comparison against a value not in the type? → remove

# 3. Build to verify
pnpm run build  # or tsc -b

# 4. Fix any remaining TS6133 (unused) or TS2367 (type mismatch) errors
```

## Common Error Patterns

| Error | Meaning | Fix |
|-------|---------|-----|
| `TS6133: 'X' is declared but its value is never read` | Unused import/variable/function | Remove the declaration |
| `TS2367: types have no overlap` | Comparing against a value not in the union type | Remove the dead comparison branch |
| `TS2304: Cannot find name 'X'` | You removed a symbol but still reference it | Remove the reference |

## Example (this session)

Removed `StatusPill` component → cascading cleanup:
- `HourglassSpinner` import (only used by StatusPill) → removed
- `statusTone()` helper (only used by StatusPill) → removed
- `tx.status === "expired"` comparisons (not in TxStatus union) → removed

All three were caught by `pnpm run build` errors after the initial removal.

## Anti-pattern

**Don't** fix build errors one at a time in a loop. Scan the full cascade first,
fix all at once, then build once. This avoids N build cycles for N related errors.
