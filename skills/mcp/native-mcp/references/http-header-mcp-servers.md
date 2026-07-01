# HTTP-header MCP servers in Hermes native MCP

Use this when a web product shows a Codex/Claude-style MCP snippet for an HTTP server that authenticates with custom headers, and you need to translate it into Hermes native MCP configuration.

## Applicability

- Remote MCP server over HTTP/SSE/streamable HTTP.
- Auth is a static HTTP header such as `X-Goog-Api-Key` or `Authorization`.
- The upstream docs show TOML-like blocks such as `[mcp_servers.name.http_headers]`.

Anti-conditions:

- Do not store already-exposed API keys in durable config unless the user explicitly accepts the security boundary; prefer a newly issued key.
- Do not record concrete keys in logs, reports, skills, summaries, or references.
- Do not describe the client as “pretending to be Codex”; the important contract is URL + headers + transport, not identity spoofing.

## Hermes config shape

Codex/TOML examples often use `http_headers`. Hermes native MCP config is YAML and uses `headers`:

```yaml
mcp_servers:
  stitch:
    url: "https://stitch.googleapis.com/mcp"
    headers:
      X-Goog-Api-Key: "<redacted>"
    timeout: 180
    connect_timeout: 60
    sampling:
      enabled: false
```

## Verification workflow

1. Back up config before writing:

```bash
cp ~/.hermes/config.yaml ~/.hermes/config.yaml.bak-<server>-$(date +%Y%m%d%H%M%S)
```

2. Insert/update the server config without printing secrets.
3. Verify using Hermes CLI with secret redaction in shell output:

```bash
hermes mcp list
hermes mcp test <server>
hermes mcp doctor <server>
```

Expected success signals:

- `hermes mcp list` shows the server enabled.
- `hermes mcp test <server>` reports `Connected` and a non-zero tool count.
- `hermes mcp doctor <server>` reports auth configured and probe OK.

4. If the CLI can see the server but the current agent turn does not expose `mcp_<server>_*` tools, the current session was started before the MCP toolset was injected. Reload/restart Hermes, then do a read-only tool call first.

## First read-only probe pattern

After reload, call the least invasive read-only MCP method first, for example:

- `get_project`
- `list_projects`
- `list_screens`
- `get_screen`

Only after that should generation/edit tools be used.
