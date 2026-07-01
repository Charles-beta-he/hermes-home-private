# Design-tool MCP integration safety pattern

Scope: configuring or evaluating MCP servers that connect design tools such as Figma, Stitch-like generators, or HTML/code-export services to Hermes.

Applicability: use when the user wants MCP to fetch design files, layers, tokens, generated HTML, or assets. Anti-conditions: do not treat this as an endorsement of any specific package/endpoint without verification; do not inline tokens; do not trust MCP output as executable code.

## Safe architecture

```text
design tool / generator
→ MCP fetch/export
→ raw evidence file
→ derived token-map/screen-map
→ reviewed implementation patch
→ tests/build/screenshot verification
```

MCP is the evidence transport layer, not the authority layer.

## Configuration pattern

For Figma-like stdio servers:

```yaml
mcp_servers:
  figma:
    command: "npx"
    args: ["-y", "<verified-figma-mcp-package>"]
    env:
      FIGMA_TOKEN: "${FIGMA_TOKEN}"
    timeout: 180
    connect_timeout: 60
```

For remote HTTP design services:

```yaml
mcp_servers:
  design_service:
    url: "https://example.com/mcp"
    headers:
      Authorization: "Bearer ${DESIGN_SERVICE_TOKEN}"
    timeout: 180
    connect_timeout: 60
```

Do not use placeholders as final config. First verify the official package/endpoint and auth model.

## Security checklist

- Tokens must come from env/secrets, never plaintext config.
- Disable or restrict sampling for untrusted design MCP servers.
- Redact raw exports before sharing; design files may include private user/project data.
- Keep generated code/HTML quarantined under `references/raw/` or equivalent until reviewed.
- Never let an MCP server mutate project code unless that server is explicitly trusted and the change is reviewed.

## Direct document API fallback

For Figma-like design sources, MCP is convenient but not always necessary. When a user provides a Figma frame link and a read token via a local secret file, a direct REST pull can be the fastest safe path for one-off implementation:

```text
Figma frame link
→ parse fileKey + nodeId
→ GET /v1/files/{fileKey}/nodes?ids={nodeId}
→ save raw JSON evidence
→ derive token-map/screen-map
→ implement owned UI/components
```

Use this fallback when MCP setup would require a restart, when a remote design MCP endpoint is unverified, or when the work is a single design import. Keep the token outside chat and config; prefer a local env file such as `~/.hermes/secrets/<design-tool>.env` with mode 600. Do not print the token during smoke tests.

## Verification checklist

1. MCP server connects and lists tools, or direct REST auth succeeds with a non-secret readback.
2. Tool list or REST endpoint matches expected read-only fetch/export operations.
3. Fetch/export output is saved as raw evidence.
4. Derived token/screen maps validate as JSON.
5. Product implementation uses owned state and components.
6. Tests/lint/build/screenshot verification pass.
7. If a token appeared in chat, screenshots, logs, or a browser capture, treat it as leaked and require rotation before use.

## Pitfalls

- **Package-name hallucination**: many MCP examples use plausible package names. Always verify the package/endpoint exists before adding config.
- **Design-file authority trap**: Figma/Stitch can be design SSOT, not product-logic SSOT. State machines, side-effect gates, ledgers, and permissions remain in code/project SSOT.
- **Credential boundary**: browser login pages and token generation are human gates; stop and request the user to authorize rather than typing secrets. If the user pastes a personal access token into chat or an attached screenshot, do not use it; tell them to revoke it and provide a rotated token through a local secret file.
- **Browser-session mismatch**: the agent's browser session may not share the user's logged-in Stitch/Figma session. If the agent still sees a login page, have the user generate/export the design in their browser, then hand over the Figma frame link or exported artifact.
