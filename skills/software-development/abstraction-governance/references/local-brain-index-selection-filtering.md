# Local Brain Index Selection Filtering

Scope: local brain / evidence-memory retrieval paths where `brainctl search` or similar FTS/keyword indexes choose which knowledge blocks enter prompt context.

Applicability:
- Search results can mix current knowledge-base notes, project experience, reviews, and stale task/project notes.
- Older project experience repeats the query terms more often than the current SSOT/knowledge note.
- Chinese text or dense Markdown causes FTS tokenization gaps, so current knowledge is present but not surfaced.

Anti-conditions:
- Do not use this as a reason to delete project experience; stale project notes may still be useful as historical evidence.
- Do not promote external memory-system claims without benchmark/schema/rollback evidence.
- Do not store session progress in memory or skills; use taskpool proof/session history instead.

Pattern:
1. Keep the raw FTS/BM25 query as candidate discovery, not final truth.
2. Expand the candidate pool before final `limit` so noisy/stale high-BM25 hits can be demoted after governance filtering.
3. Add a deterministic fallback for Chinese/dense text: search `blocks` by `LIKE` on the first query term, then require all query terms in `path + heading + body` before adding fallback candidates.
4. Classify each candidate by source class, e.g. `knowledge_base`, `project_experience`, `governance_review`, `derived_dashboard`, `general_note`.
5. Parse frontmatter/status and body markers:
   - stale markers: `status: stale`, `archived`, `deprecated`, `completed without tests`, `旧结论`, `过期`, `废弃`, `归档`.
   - current markers: `current`, `active`, `canonical`, `SSOT`, `current source`, `证据边界`, `当前准则`.
6. Return visible selection metadata, not silent magic:
   - `selection_status`: `accepted` or `filtered`.
   - `filter_reasons`: e.g. `stale_temporal_state`, `weak_or_missing_evidence`.
   - `source_class`, `base_score`, `rank_adjustment`, adjusted `score`.
7. Sort accepted/current/evidence-backed candidates above filtered/stale candidates even when stale notes have more raw keyword hits.
8. Preserve line/hash evidence fields so final answers can cite the selected block and operators can audit why a stale block was filtered.

Regression test shape:
- Fixture A: old project experience with repeated query terms and `status: stale` / weak-proof marker.
- Fixture B: current knowledge-base note with the same query terms and `status: current` / `Current source` / `证据边界` marker.
- Assert the current note ranks first and the old project note remains visible but `selection_status == filtered` with `stale_temporal_state`.

Verification commands used in the originating session:
- `python3 -m py_compile ~/.hermes/scripts/brainctl.py ~/.hermes/scripts/test_brainctl.py`
- `python3 ~/.hermes/scripts/test_brainctl.py`
- `python3 ~/.hermes/scripts/brainctl.py --json brains validate`
- `python3 ~/.hermes/scripts/brainctl.py --json memory-replay-gate`
