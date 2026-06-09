# Text-assertion mismatch: fixing `assert "X" in CONSTANT` failures

## Common patterns

### 1. Singular/plural substring trap

Python `in` is **exact substring**, not word-boundary:

```python
>>> "dependency" in "dependencies"
False   # "dependency" (9 chars) ≠ any contiguous 9-char slice of "dependencies"

>>> "status" in "statuses"  
False   # same pattern: -y/-ies, -s/-es mismatches
```

**Fix:** Rephrase the source so the expected substring appears literally:
- `"Resolve dependencies first"` → `"Resolve each dependency first"` ✓
- `"Check statuses"` → `"Check each status"` ✓

Suffix pairs that bite: `-y/-ies`, `-tion/-tions`, `-ment/-ments`, `-ness/-nesses`, `-ty/-ties`

### 2. Synonym / paraphrase mismatch

Test expects `"relevant"` but source says `"pertinent"`. The fix is to match the test's
vocabulary — tests are the spec when they assert on string content.

### 3. Casing mismatch

Test asserts `"describe"` in `.lower()` but source has `"DESCRIBE"`. Always apply
`.lower()` to both sides or neither.

### 4. Whitespace / punctuation drift

`"cross-session"` vs `"cross session"` — hyphens, em-dashes, and Unicode arrows (→)
are easy to miss. Use the exact byte sequence the test expects.

## Debugging workflow

1. Run the failing test with `--tb=long -o "addopts="` to see actual vs expected
2. `repr()` the constant to see hidden chars (Unicode arrows, non-breaking spaces)
3. Fix the source constant, not the test (tests are the spec)
4. Run targeted test, then full file to catch cascading substring issues
