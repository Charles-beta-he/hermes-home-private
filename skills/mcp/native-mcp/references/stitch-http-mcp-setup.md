# Stitch HTTP MCP setup notes

Use when a user wants to connect Google Stitch MCP to Hermes Agent from a Stitch “Setup MCP” panel.

## Applicability

- Stitch shows a remote HTTP MCP endpoint such as `https://stitch.googleapis.com/mcp`.
- The setup UI may display client-specific TOML for Codex, VS Code, Claude Code, etc.
- Hermes native MCP is the target client.

## Hermes config shape

Hermes uses YAML under `~/.hermes/config.yaml`, and remote MCP headers go under `headers`:

```yaml
mcp_servers:
  stitch:
    url: "https://stitch.googleapis.com/mcp"
    headers:
      X-Goog-Api-Key: "<fresh Stitch API key>"
    timeout: 180
    connect_timeout: 60
    sampling:
      enabled: false
```

Do not copy Codex TOML literally into Hermes config:

```toml
[mcp_servers.stitch]
url = "https://stitch.googleapis.com/mcp"

[mcp_servers.stitch.http_headers]
"X-Goog-Api-Key" = "..."
```

For Hermes, `http_headers` is not the documented field; use `headers`.

## Credential boundary

If the API key appears in chat, screenshots, terminal logs, or other model-visible context, treat it as exposed. Do not persist it into `config.yaml`, env files, shell history, scripts, or reference docs. Ask the user to rotate/regenerate the key, or have them write it locally themselves if they accept the risk.

When documenting the setup, redact the key and store only the endpoint/config shape.

## Verification

After config change and Hermes restart/reload:

1. Confirm `mcp_servers.stitch` exists in config without printing the key.
2. Reload/restart Hermes.
3. Check the tool list for names prefixed like `mcp_stitch_*`.
4. If only old servers appear, the current session did not load Stitch; verify startup logs/status before changing unrelated config.

## Anti-conditions

- Do not conclude “Stitch MCP does not work” just because the current session lacks `mcp_stitch_*`; startup/reload timing and config shape are separate.
- Do not encode a leaked key into durable config for convenience.
