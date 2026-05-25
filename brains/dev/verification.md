# Dev Verification v0.2.0

Minimum closure evidence:
- changed file list
- test/build command output
- associated-surface map for project/code/product/document queries, or explicit unchecked surfaces
- producer/transformer/consumer/entry/permission/KPI/test classification for nontrivial query hits
- known residual risks
- rollback/restore note when stateful

Agent-facing automation contract evidence:
- For structured CLI/script/tool output: command invocation, schemaVersion or contract version, required-field assertions, failure-case shape, deterministic fixture/replay input, and no ANSI/control noise in machine output.
- For tool-specific workflows: exact binary path/version and proof that workflow/help/schema/diagnostics were loaded from that same binary when available.
- For repair/fix flows: diagnostic id, repair id/summary, safety label, plan-first output, explicit apply approval when edits are made, and retest result.
- For provenance or coverage claims: owner/surface-to-fixture matrix and proof the fixtures are actually run by the relevant test command.
- For optimization/resource/readiness claims: budget artifact, size/memory/performance report, readiness report, or before/after metric; otherwise label the claim as advisory only.
- For experimental or untrusted tools: disposable/sandbox workspace path, host side-effect review, private-access/private-input exclusion, and cleanup/artifact boundary.
