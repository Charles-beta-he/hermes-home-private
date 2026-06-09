# Approval-after-analysis taskpool handoff

Use when a user gives short approval after you already analyzed an external source or proposed a governed task, e.g. “认可”.

## Rule

Treat short approval as authorization to execute the immediately proposed safe next step, usually taskpool creation or local-brain note capture. Do not ask again unless the next operation crosses a red line: install software, log in, grant permissions, migrate existing structures, publish/send externally, delete/overwrite, or mutate authority-layer state beyond the proposed task/note.

## Taskpool pattern

1. Preserve existing analysis evidence.
2. If the source is short-video/social-platform content, write or reference a concise evidence note with source URL, resolved URL, visible title/author/date/metrics, extracted mechanism keywords, candidate upstreams, and uncertainty.
3. Search for duplicates by source, repo, and mechanism class.
4. Create a governed task with at least:
   - `priority_layer`
   - `dependency_order`
   - `multimodel_triage_result`
   - `architecture_target`
   - `capability_delta`
   - `anti_drift_check`
   - `acceptance_evidence`
   - evidence refs
5. Refresh dashboard and read back frontmatter to verify status, evidence refs, boundaries, and structured fields.

## Local-brain / LLM Wiki boundary

For tasks about local-brain wiki, Obsidian, LLM Wiki, or knowledge compilers:

- wiki notes are knowledge projection / compiled knowledge, not taskpool/ledger authority;
- Qdrant/vector DB is recall-only and must回链 evidence/wiki files;
- taskpool/ledger/API remain authority for lifecycle state;
- promotion to memory/skill/taskpool/ADR requires explicit gate;
- do not install plugins or migrate vault structure without separate authorization.

## Pitfall

Do not turn “认可” into a fresh broad planning round. Execute the already-proposed bounded step and report the concrete artifact paths/IDs.