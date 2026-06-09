# Local code-graph advisory evaluation

Use this reference when evaluating a third-party local code graph / semantic indexer as a tool-call reduction layer for Hermes or another repo.

## Boundary

Treat code-graph tools as advisory retrieval layers, not truth gates. They can reduce discovery calls for symbol entry points and dependency neighborhoods, but final claims still need direct source reads and project verification (`read_file`, targeted searches, tests/builds, or runtime probes).

## Evaluation pattern

1. Pin and record the exact source.
   - Verify the canonical repository URL.
   - Clone or inspect the repo and record commit / package version.
   - Read repository-local instructions before building.
2. Use an isolated cache/index directory.
   - Avoid leaving large generated index folders in the target repo.
   - Clean the index after the spike unless the user explicitly wants it persisted.
3. Check runtime compatibility before indexing.
   - For JS/WASM-heavy CLIs, prefer a known-good stable Node line for the spike and record it in the report.
   - If a newer runtime crashes or leaks, capture the working pin as a spike-local prerequisite; do not turn it into a permanent global ban unless separately ratified.
4. Index the target and record objective metrics.
   - Files indexed, node/edge count, index size, backend used, wall-clock time, and any degraded/fallback backend label.
5. Compare against the existing baseline.
   - Use 2–4 fixed retrieval cases that represent real future work.
   - For each case, compare code-graph output against `search_files` / direct reads: entry-point coverage, false positives, missing roots, latency, and tool-call count saved.
6. Make an adoption decision with a default-off bias.
   - Require multi-root support when important code lives outside the repo root (for Hermes this often includes `~/.hermes/scripts` alongside the checkout).
   - Require cache freshness/staleness policy, ignore rules, degraded-backend labeling, and cleanup policy before mainline integration.

## Reporting shape

Write a concise private report with:
- Source: repo URL, commit/version, build/runtime pin.
- Index run: command, target path, metrics, backend, index size.
- Retrieval cases: query, expected truth surface, code-graph result, baseline result, miss/benefit.
- Decision: integrate now / keep advisory / reject.
- Follow-ups: multi-root, cache, staleness, cleanup, truth-gate requirements.

## Pitfalls

- Do not call an indexer “integrated” after only building or indexing it.
- Do not rely on repo-root indexing when the real control plane spans external scripts, generated artifacts, or user-profile overlays.
- Do not preserve large generated indexes in a source checkout without an explicit cache policy.
- Do not replace source reads/tests with graph output; graph output is a locator, not evidence by itself.
