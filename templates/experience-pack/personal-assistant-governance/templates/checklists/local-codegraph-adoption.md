# Local Codegraph / Knowledge-Graph Adoption Gate

Use this before enabling a local codebase-memory-style MCP server for a new Hermes user or project.

## Objective

Give agents structural code understanding with low context cost while keeping code and graph artifacts local.

## Default stance

Install the template automatically, but do not auto-index arbitrary projects and do not auto-merge MCP config until the binary and project root are verified.

## Activation checklist

1. Binary trust
   - Prefer a pinned release or locally built binary.
   - Verify checksum/signature when using release artifacts.
   - Run `codebase-memory-mcp --version`.

2. Local cache boundary
   - Set `CBM_CACHE_DIR=$HERMES_HOME/cache/codebase-memory-mcp`.
   - Do not commit generated SQLite/cache files.
   - Treat graph output as advisory evidence, not canonical truth.

3. First-project smoke test
   - Start with a small/medium repo.
   - Run `index_repository` with `mode=fast`.
   - Verify `list_projects` returns the indexed project.
   - Verify `search_graph` finds a known function/class.
   - Verify `trace_path` returns a known caller/callee edge.

4. Agent usage rules
   - Use graph queries before broad file reads for architecture, call chain, impact analysis, dead-code candidates, and route/service tracing.
   - Still read source files before editing or making final claims.
   - Detect pagination/truncation (`has_more`, `total`, limit) before concluding absence.

5. Promotion to default-on
   - Only after successful smoke test on at least one real repo.
   - Record version, cache path, indexed project, query outputs, and fallback plan.
   - Keep standard search/read tools available as rollback.

## Red lines

- Do not run `curl | bash` silently for a new user.
- Do not auto-edit agent configs without a dry-run/readback.
- Do not enable UI/network surface beyond localhost.
- Do not commit `.codebase-memory/graph.db.zst` unless the repo explicitly wants shared graph artifacts.
- Do not treat indexed graph results as proof when source readback disagrees.
