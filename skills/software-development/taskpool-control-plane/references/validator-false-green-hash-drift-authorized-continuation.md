# Validator false-green, canonical hash drift, and authorized blocked-task continuation

Applicability: Local Brain/taskpool governance loops that combine Markdown frontmatter parsing, lifecycle validation, generated projections, semantic search hashes, and user-authorized continuation of blocked historical tasks.

Anti-conditions:
- Do not infer business completion, renew expiry, or mutate external source status from parser repairs.
- A general “execute blocked tasks” grant does not authorize credentials, external sends, production writes, deploy/push, destructive actions, or invented source artifacts.

## 1. Detect parser/scope false greens

A canonical task may accidentally place a YAML key before its opening delimiter:

```md
conflict_group: conflict:x
---
type: task
layer: L3
status: pending
```

If parsing returns empty metadata and L3 scope accepts only parsed canonical types, the task disappears from governance. A sudden `59 -> 0` result may therefore hide malformed active tasks.

Procedure:

1. Inspect representative first lines from every excluded bucket before accepting a zero-debt result.
2. Add a RED test that expects a dedicated `malformed_frontmatter` violation for a YAML key before `---`.
3. Detect malformed framing before metadata-based scope classification.
4. Repair framing mechanically by moving the stray key inside the delimiters; do not alter lifecycle/evidence fields.
5. Re-run validation. Newly revealed `expired_l3` items are real OPEN debt until current source evidence resolves them.
6. Refresh dashboard, inventory, and audit claims; stale green projections must be amended rather than preserved.

Valid exclusions still include explicit non-L3 notes, fixtures, archives, and inactive storage, but malformed canonical tasks must never become invisible.

## 2. Canonical hash verifier must reuse canonical indexing

Do not mirror block-splitting/hash logic in the task orchestrator. Call the indexer’s canonical `blocks_from_file()` so heading/range rules, secret filtering, and skipped counts cannot drift.

Negative tests:

- forged/stale hash;
- malformed line range types;
- vault traversal and outside-vault symlink;
- secret-containing blocks excluded by the canonical indexer;
- missing file/block.

### Strict line-range typing pitfall

Do not normalize untrusted search-hit ranges with `int(value)`. In Python, `bool` is a subclass of `int`, and `int(1.2)` silently truncates; both can make malformed hits match canonical blocks. Validate before comparison:

- `type(line_start) is int` and `type(line_end) is int` (or explicitly reject `bool` before `isinstance(..., int)`);
- `line_start >= 1`;
- `line_end >= line_start`;
- compare the validated integers exactly with the canonical block.

The RED/negative matrix must cover both start and end with `True`, `False`, float, `None`, numeric/non-numeric strings, zero, negative values, and `end < start`, plus one canonical positive control. Keep forged hash, traversal/outside-vault, secret-block, missing-file, and missing-block cases in the same regression slice so a narrow type fix cannot weaken neighboring fail-closed boundaries.

macOS pitfall: `/var/...` can resolve to `/private/var/...`. Resolve both candidate path and vault root before `relative_to()` and before calling the canonical block function.

## 3. Independent verifier snapshot freshness

A reviewer’s verdict is valid only for the exact code/data snapshot it read. A pre-repair `AMEND` or violation count remains useful as root-cause evidence but cannot certify a later state. After every material repair:

1. run the same positive and negative gates;
2. refresh generated projections;
3. re-dispatch a read-only verifier against the current bytes;
4. bind closure claims to that fresh result.

## 4. Blocked-task authorization and concurrent resolver readback

After the user authorizes blocked historical tasks, the taskpool’s resolver/event hook may already transition `blocked -> retry -> pending`. Before issuing a manual transition:

1. read the exact task frontmatter and lifecycle log;
2. run exact task/status readback;
3. treat `pending -> pending` as evidence that another controller already advanced it, not as permission to force;
4. use accepted evidence prefixes (`command:`, `file:`, `artifact:`, `proof:`, `url:`) for any lifecycle mutation;
5. execute only the local, reversible slice supported by available inputs.

If an image-analysis task has no recoverable original image, verify the runtime and fail-soft path, then keep the feature-specific acceptance OPEN with `source image unavailable`; never substitute a fixture as the user’s image receipt.

For staged architecture tasks, record P0/P1 evidence while leaving P2/P3 OPEN. Passing compile/unit tests does not justify `done` when planner-selection changes, outcome feedback, post-update regression, or independent certification remain unproven.
