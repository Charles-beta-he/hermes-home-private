# Stitch/Figma/HTML design-to-product MCP pipeline

Use when a user wants to use Stitch/Gemini-quality design, Figma node export, or HTML generated from a design tool as input for product implementation.

## Core principle

```text
Stitch/Gemini = visual ideation
Figma = design SSOT / node evidence
MCP = evidence transport
HTML = translation artifact
Application code = product logic SSOT
```

Never let generated HTML or a design MCP server directly overwrite runtime product logic. Pull design evidence, derive tokens/screen maps, then implement owned components against existing state machines and side-effect gates.

## Safe workflow

1. User logs into Stitch/Figma and handles credentials.
2. Generate design in Stitch/Gemini using product constraints and UI copy red lines.
3. Export/send selected design to Figma.
4. User provides a Figma frame link, not credentials.
5. User stores token locally, e.g. `~/.hermes/secrets/figma-mcp.env`; the agent must not ask them to paste secrets in chat.
6. Connect read-only Figma MCP.
7. Fetch the exact frame/node and save raw evidence under a scoped project `references/` directory.
8. Derive:
   - `token-map.json` for colors, typography, spacing, radius, shadows;
   - `screen-map.json` for frame/component hierarchy and coordinates;
   - image assets only when needed.
9. Implement application components from the derived maps while preserving existing product logic, ledger, permissions, and confirmation gates.
10. Verify with tests/lint/build plus screenshot diff against the Figma/Stitch reference.

## Hermes native MCP pattern

For a local stdio Figma Context MCP server:

```yaml
mcp_servers:
  figma_context:
    command: "bash"
    args:
      - "-lc"
      - "cd '<verified-Figma-Context-MCP-repo>' && set -a && source ~/.hermes/secrets/figma-mcp.env && set +a && NODE_ENV=cli pnpm start:cli -- --json --skip-image-downloads"
    timeout: 180
    connect_timeout: 60
    sampling:
      enabled: false
```

For a remote/Cloudflare design MCP server, prefer only when the user accepts that the design/token path traverses the remote service:

```yaml
mcp_servers:
  figma_context_remote:
    url: "https://<verified-worker-or-service>/mcp"
    timeout: 180
    connect_timeout: 60
    sampling:
      enabled: false
```

## Figma handoff packet

Ask the user for:

```text
1. Figma frame link
2. Confirmation that token file is ready
```

Expected link shapes:

```text
https://www.figma.com/design/<FILE_KEY>/<NAME>?node-id=<NODE_ID>
https://www.figma.com/file/<FILE_KEY>/<NAME>?node-id=<NODE_ID>
```

Extract `fileKey` and `nodeId`; fetch only that node unless the task requires file-level context.

## 1:1 implementation rules

- Treat Figma/Stitch as source for visual tokens and geometry only.
- Treat project code/profile/SSOT as source for product logic.
- Preserve state machines, side-effect gates, ledgers, readback semantics, and permission boundaries.
- Generated HTML belongs in `references/.../raw/` until reviewed.
- Apply patches to app code manually/through reviewed diffs, never by wholesale generated overwrite.
- Screenshot diff is mandatory for the user’s 1:1 design expectation.

## Stop gates

Stop before:

- typing Google/Figma credentials;
- storing tokens in chat or plaintext shared config;
- deploying a Worker containing personal tokens without explicit user approval;
- enabling MCP sampling for untrusted design servers;
- letting a design server mutate code;
- publishing/pushing/deploying generated design output.

## Verification checklist

- MCP connects and lists expected read-only tools.
- Raw Figma/Stitch/HTML evidence is saved.
- Derived token/screen maps validate as JSON.
- Product code uses existing state and gates.
- Tests/lint/build pass.
- Screenshot diff or visual inspection compares final app to the design reference.
