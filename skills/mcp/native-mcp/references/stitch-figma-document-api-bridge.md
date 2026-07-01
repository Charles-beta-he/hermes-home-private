# Stitch → Figma → MCP / Document API bridge

Use when a task needs to turn a Stitch/Gemini-generated design into implementable app code through Figma and Hermes.

## Applicability

- The user wants Stitch/Gemini visual quality, then 1:1 implementation in RN/PWA/HTML.
- The design can be exported or linked through Figma.
- Hermes needs to ingest design evidence, not let the design tool mutate runtime code directly.

## Anti-conditions

- Do not use this as a reason to store or paste design-tool tokens in chat.
- Do not treat Stitch/Figma as the product-logic SSOT; runtime state, permissions, ledger, and safety gates remain in the app code/project profile.
- Do not hardcode a one-session Stitch project URL, Figma file key, node id, or leaked token into a skill.

## Preferred workflow

1. Use Stitch/Gemini for design generation and visual exploration.
2. Export or send the selected design to Figma.
3. Ask the user for a Figma frame link, not a token.
4. Ingest the frame by either:
   - Figma MCP (`get_figma_data`, `download_figma_images`) for long-lived workflow; or
   - direct Figma REST Document API for a fast one-off bridge.
5. Save raw Figma evidence under a project-scoped `references/.../raw/` directory.
6. Derive `token-map.json`, `screen-map.json`, and assets.
7. Rebuild the UI in the target app using existing product logic/state machines.
8. Verify with tests/lint/build plus screenshot comparison against the Figma/Stitch reference.

## Token safety

If the user pastes a Figma Personal Access Token in chat or screenshot, treat it as leaked:

1. Do not use it.
2. Instruct the user to revoke/delete it.
3. Ask them to create a new read-only token and put it only in a local secret file, for example:

```bash
mkdir -p ~/.hermes/secrets
chmod 700 ~/.hermes/secrets
cat > ~/.hermes/secrets/figma-mcp.env <<'EOF'
FIGMA_API_KEY=NEW_TOKEN_HERE
EOF
chmod 600 ~/.hermes/secrets/figma-mcp.env
```

Then ask the user to say only `figma token file ready`.

## Direct Figma REST fallback

MCP is useful but not mandatory. For a copied frame link:

```text
https://www.figma.com/design/<FILE_KEY>/<NAME>?node-id=<NODE_ID>
```

Parse:

```text
fileKey = <FILE_KEY>
nodeId = <NODE_ID> with hyphen converted to colon for API `ids`
```

Call:

```text
GET https://api.figma.com/v1/files/<FILE_KEY>/nodes?ids=<NODE_ID>
```

Auth headers:

```text
X-Figma-Token: <PAT>
# or
Authorization: Bearer <OAuth token>
```

Use this path when Hermes has not been restarted to load a newly-added MCP server, or when one frame needs to be fetched quickly.

## Hermes native MCP configuration pattern

For a local Figma Context MCP server, prefer sourcing a secret file from an absolute path. Avoid `~` in MCP args because the MCP launcher does not expand it reliably.

Example shape:

```yaml
mcp_servers:
  figma_context:
    command: bash
    args:
      - -lc
      - cd '<Figma-Context-MCP repo>' && set -a && source /Users/<user>/.hermes/secrets/figma-mcp.env && set +a && NODE_ENV=cli pnpm start:cli -- --json --skip-image-downloads
    timeout: 180
    connect_timeout: 60
    sampling:
      enabled: false
```

After editing config, restart Hermes so the generated MCP tools become available.

## Config pitfall

`hermes config set mcp_servers.<name> '<json>'` may serialize the JSON as a string depending on config tooling/version. Verify the resulting YAML type. If it becomes a quoted JSON string instead of a mapping, rewrite it as a real YAML mapping and keep a backup.

Verification snippet:

```python
import yaml
cfg = yaml.safe_load(open('/Users/<user>/.hermes/config.yaml'))
assert isinstance(cfg['mcp_servers']['figma_context'], dict)
```

## Browser-control pitfall

The automation browser session may not share the user’s logged-in Google/Figma state. If the user authorizes direct browser operation on their own Chrome/Safari, use macOS background `computer_use` with screen captures and avoid typing secrets. Stop on login/password/payment/permission prompts unless explicitly authorized.
