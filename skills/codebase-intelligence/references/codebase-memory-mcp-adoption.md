# codebase-memory-mcp adoption notes

Use this reference when evaluating or wiring DeusData/codebase-memory-mcp, or a similar local MCP code knowledge graph, into Hermes/codebase-intelligence workflows.

## Source-verified snapshot

- Canonical repo: `https://github.com/DeusData/codebase-memory-mcp`
- Session-pinned commit inspected: `e599df1d563c1e9b0b2fc8c6b12ee85934ade1c5`
- Shape: C-based stdio MCP server + CLI, SQLite graph store, vendored tree-sitter grammars, hybrid LSP-style resolver passes, optional localhost graph UI.
- Advertised MCP tools observed in source/help: `index_repository`, `search_graph`, `query_graph`, `trace_path`, `get_code_snippet`, `get_graph_schema`, `get_architecture`, `search_code`, `list_projects`, `delete_project`, `index_status`, `detect_changes`, `manage_adr`, `ingest_traces`.
- Cache default in source: `~/.cache/codebase-memory-mcp`; `CBM_CACHE_DIR` overrides it.

## Smoke-test ladder

Use an isolated cache; never index a real project first without an explicit target root.

```bash
export CBM_CACHE_DIR="$HERMES_HOME/cache/codebase-memory-mcp"
codebase-memory-mcp --version
codebase-memory-mcp cli index_repository '{"repo_path":"/path/to/small/repo","mode":"fast"}'
codebase-memory-mcp cli list_projects '{}'
codebase-memory-mcp cli search_graph '{"project":"<project>","query":"known symbol","limit":5}'
codebase-memory-mcp cli trace_path '{"project":"<project>","function_name":"known_function","direction":"inbound","depth":3}'
```

Acceptance: index returns a project id, list shows the project, search finds a known symbol, trace returns a known caller/callee edge. If search/trace fail, do not enable it as default-on; keep it advisory and inspect source/tool config.

## Hermes integration model

Prefer a default-off MCP template plus explicit activation, not silent one-line install:

```yaml
mcp_servers:
  codebase_memory:
    command: codebase-memory-mcp
    args: []
    timeout: 30
    env:
      CBM_CACHE_DIR: $HERMES_HOME/cache/codebase-memory-mcp
```

Hermes CLI landing pattern after adoption:

- `hermes codegraph list` — read configured snippet/activation/cache/merge state without side effects.
- `hermes codegraph install --dry-run` — resolve latest release, platform asset, and checksum manifest without downloading or writing the binary.
- `hermes codegraph install` — download the selected release asset, verify SHA-256 from `checksums.txt`, safe-extract, install to `$HERMES_HOME/bin/codebase-memory-mcp`, then verify `--version`.
- `hermes codegraph doctor` — binary/version/cache/config readiness.
- `hermes codegraph enable --dry-run` — preview Hermes-scoped activation writes.
- `hermes codegraph enable` — write `$HERMES_HOME/config/codegraph-mcp.yaml`, `$HERMES_HOME/state/codegraph-activation.json`, and `$HERMES_HOME/cache/codebase-memory-mcp/` only; do **not** mutate main `config.yaml`.
- `hermes codegraph enable --merge-config` — explicitly merge `mcp_servers.codebase_memory` into `$HERMES_HOME/config.yaml` with backup.
- `hermes codegraph smoke --repo /path --query "known symbol" --function-name known_function` — run the smoke ladder and read back outputs against an explicitly authorized repo root.

When registering this class of capability as a formal Hermes CLI subcommand, prefer a thin `hermes_cli/subcommands/<name>.py` parser plus a lazy dispatcher in `hermes_cli/main.py`; add the new command to `_BUILTIN_SUBCOMMANDS` so plugin discovery is not needlessly triggered. Keep the implementation callable both as a standalone manager script and through the CLI dispatcher where practical.

## Open-box automation requirement

Do not stop at a report, inventory, or sanitizer when the user asks for “开箱即用”, “全自动化效果”, or “全盘推进至企业生产级”. A usable landing must include an installer/activator path that performs safe defaults automatically: doctor, fail-closed sanitization, no-overwrite copy/merge, disabled side-effect flags, receipt/readback, and smoke-test evidence. For Hermes feature adoption, push past a loose script into a formal CLI surface plus tests when the user explicitly asks for production-grade landing. Human gates remain for binary trust, config mutation, project indexing authority, UI/network exposure, and committing shared graph artifacts.

## Release installer pattern

For production-grade adoption of a local external binary, prefer a verified release installer rather than a shell pipe:

1. Query the upstream release metadata (latest by default, explicit `--tag` when pinning).
2. Detect OS/architecture to select the exact asset; on Linux prefer portable bundles when the upstream provides them to reduce host ABI drift.
3. Download `checksums.txt` first and fail closed if the selected asset is absent.
4. In `--dry-run`, stop after metadata + checksum-manifest verification; do not download the archive or write files.
5. In real install, download archive, compute SHA-256, compare with `checksums.txt`, safe-extract with path-traversal checks, copy only the expected binary into `$HERMES_HOME/bin`, make it executable, and run `--version`.
6. Keep install separate from `enable`: installing a binary must not mutate MCP config; enabling config must not silently download code.
7. Test with both fake binary/unit paths and one real temp-home install against a release asset before claiming production readiness.

## Safety and trust boundaries

- Do not run `curl | bash` silently for a new user. Prefer an already installed binary, a pinned package manager path, or a release download with checksum/signature verification.
- Do not auto-edit agent config without dry-run and readback.
- Keep graph UI disabled unless requested; if enabled, bind localhost only.
- Put generated DB/cache under `$HERMES_HOME/cache/codebase-memory-mcp` or another explicit cache path; do not commit it.
- Do not commit `.codebase-memory/graph.db.zst` unless the repository explicitly chooses team-shared graph artifacts.
- Treat graph results as advisory navigation. Before editing or final claims, read the source and run the relevant tests/build/runtime checks.
- Watch for stale indexes: call `index_status`, `detect_changes`, or re-index before relying on impact/call-chain output.

## Verification checklist for production-grade Hermes landing

- Parser: `hermes codegraph --help` lists `list`, `install`, `doctor`, `enable`, and `smoke`.
- Read-only commands: `list`, `doctor`, and `install --dry-run` do not create config/cache/state/binary files.
- Verified installer: real temp-home `install` resolves a release asset, validates checksum, installs `$HERMES_HOME/bin/codebase-memory-mcp`, and `--version` runs.
- Safe enable: `enable` writes only Hermes-scoped snippet, activation receipt, and cache directory; it does not write `config.yaml` unless `--merge-config` is explicit.
- Merge readback: `--merge-config` creates/updates `mcp_servers.codebase_memory` and backs up an existing `config.yaml`.
- Real smoke: run against a small explicit repo and verify `index_repository`, `list_projects`, `search_graph`, and `trace_path` results.
- Test coverage: add parser tests plus fake-binary command tests; run targeted CLI tests and any experience-pack sanitizer/installer tests that ship the manager.
- Commit hygiene: commit only the CLI implementation, parser, tests, docs, and pack artifacts in scoped commits; do not mix runtime caches, docs/private receipts, or unrelated dirty files. If a root repo tracks a submodule pointer, do not commit that pointer until the submodule commits are pushed or otherwise reachable.

## Build pitfall observed

A source build on macOS with Homebrew libgit2 1.9.2 may auto-detect libgit2 and fail around `git_allocator`. For a local spike, forcing the fallback path by clearing libgit2 flags can build the production binary:

```bash
make -f Makefile.cbm cbm -j4 LIBGIT2_LIBS= LIBGIT2_CFLAGS= LIBGIT2_FLAGS=
```

Do not encode this as a permanent global rule; it is a local compatibility workaround. Prefer verified release binaries for normal users unless source-build validation is part of the task.
