# HTTP MCP servers with header auth in Hermes (Stitch/Codex-style setup)

Scope: Connecting an HTTP MCP server that provides a Codex/Claude/Cursor-style config snippet, especially when the snippet uses TOML and header auth.

Applicability:
- The server endpoint is an HTTP MCP URL such as `https://.../mcp`.
- The external UI shows a client selector like Codex and a TOML block with `[mcp_servers.<name>]` and `[mcp_servers.<name>.http_headers]`.
- Hermes native MCP is the actual client being configured.

Anti-conditions:
- Do not treat this as permission to impersonate another client or bypass auth; the client selector often just changes config syntax.
- Do not persist exposed secrets unless the user explicitly grants use of that value in the current security context. Prefer redacted logs and backup-before-edit.
- Do not claim the live chat has gained new MCP tools until the Hermes session/tool registry has actually reloaded.

## Config translation

Codex-style TOML commonly looks like:

```toml
[mcp_servers.stitch]
url = "https://stitch.googleapis.com/mcp"

[mcp_servers.stitch.http_headers]
"X-Goog-Api-Key" = "..."
```

Hermes native config is YAML and uses `headers`, not `http_headers`:

```yaml
mcp_servers:
  stitch:
    url: "https://stitch.googleapis.com/mcp"
    headers:
      X-Goog-Api-Key: "..."
    timeout: 180
    connect_timeout: 60
    sampling:
      enabled: false
```

For HTTP MCP servers, `hermes mcp list`, `hermes mcp test <name>`, and `hermes mcp doctor <name>` are the fastest verification path.

## Safe setup workflow

1. Backup config first:

```bash
cp ~/.hermes/config.yaml ~/.hermes/config.yaml.bak-<server>-mcp-$(date +%Y%m%d%H%M%S)
```

2. Add the YAML server block under `mcp_servers`.
3. Redact secrets in every verification command output:

```bash
hermes mcp test stitch 2>&1 \
  | sed -E 's/AQ\.[A-Za-z0-9._-]+/<redacted>/g; s/(X-Goog-Api-Key[=:] ?)[A-Za-z0-9._-]+/\1<redacted>/g'
```

Adjust the regex for the provider's key prefix.

4. Verify:

```bash
hermes mcp list
hermes mcp test <name>
hermes mcp doctor <name>
```

Expected success evidence:

- `list` shows the server enabled.
- `test` shows `Connected` and `Tools discovered: N`.
- `doctor` shows `auth.status: configured`, `config.present: true`, `probe.ok: true`, and the expected `tool_count`.

5. Restart/reload Hermes if the current chat does not expose the newly configured tools. CLI-level MCP connection success does not retroactively add tools to an already-started agent tool registry.

## mcporter caveat

`mcporter list --http-url ... --header ... --json` can fail on schema reference resolution for some MCP servers, for example `can't resolve reference #/$defs/...`, even when Hermes native MCP connects and discovers tools successfully. Treat that as an mcporter/schema-compatibility caveat, not as proof that the MCP server is unusable. Prefer `hermes mcp test/doctor` for Hermes-native readiness.

## Pitfalls

- Copying TOML syntax directly into Hermes YAML config.
- Using `http_headers` in Hermes config instead of `headers`.
- Printing full API keys while running setup probes.
- Equating an external UI's "Codex" selector with a need to spoof Codex identity. Usually it only means "show Codex config format".
- Reporting completion after config write only; always prove connection and tool discovery.
