# Social Distribution Adapter — local dry-run layer

## Location

`~/.hermes/scripts/social_distribution_adapter.py`

Tests: `~/.hermes/scripts/test_social_distribution_adapter.py`

## What it does

Reads a platform-neutral `publish-package.json`, validates it against a JSON Schema, maps fields to per-platform payloads, checks adapter availability (MatrixMedia for Chinese platforms, Postiz for international), and emits an evidence JSON bundle — **without** logging in or publishing.

## Supported platforms

### MatrixMedia (GPL-2.0 — CLI boundary only)
抖音(dy) · 头条(tt) · 快手(ks) · B站(blbl) · 百家号(bjh) · 视频号(sph) · 小红书(xhs)

### Postiz (AGPL-3.0 — CLI boundary only)
X/Twitter · LinkedIn · YouTube · TikTok · Instagram · Facebook · Reddit

## Red lines (enforced)

| Rule | Enforcement |
|------|-------------|
| `--mode publish` without `--human-approval-token` | Rejected with error |
| dry-run always sets `will_publish=false` | Guaranteed |
| AGPL/GPL projects behind CLI boundaries only | No source copying |
| Missing binary → `unknown_binary_missing` | Reported, not faked |
| No password/cookie/credential entry | Script design guarantee |

## Usage

```bash
# Dry-run against sample package
python3 ~/.hermes/scripts/social_distribution_adapter.py \
  ~/.hermes/runs/social-distribution-dry-run-2026-06-11/publish-package.sample.json \
  --mode dry-run \
  --platforms dy,xhs,x \
  --out evidence.json

# Publish mode (requires human approval token)
python3 ~/.hermes/scripts/social_distribution_adapter.py \
  package.json \
  --mode publish \
  --human-approval-token "abc123" \
  --platforms dy \
  --out evidence.json
```

## PublishPackage schema

Schema file: `~/.hermes/runs/social-distribution-dry-run-2026-06-11/publish-package.schema.json`

Required: `title`, `media` (non-empty array with `type` + `path`).
Optional: `body`, `tags`, `platformOverrides`, `scheduleAt`, `human_approval_token`.

## Adapter detection

- Global CLI via `which matrixmedia` / `which postiz`
- Repo-local fallback: checks cloned checkouts under `~/.hermes/runs/social-distribution-oss-verify-2026-06-10/`
- When neither is available: `available=false`, `login_status=unknown_binary_missing`

## Evidence output

```json
{
  "generated_at": "ISO 8601",
  "package_valid": true,
  "mode": "dry-run",
  "matrixmedia": { "available": true, "login_status": "..." },
  "postiz": { "available": false, "login_status": "unknown_binary_missing" },
  "platform_previews": [
    {
      "platform": "dy",
      "platform_name": "抖音",
      "adapter": "matrixmedia",
      "command_preview": "matrixmedia cli publish -p dy ... # DRY-RUN ONLY",
      "will_publish": false,
      "available": true
    }
  ],
  "red_lines_held": ["package_validated", "cli_boundary_preserved", ...],
  "errors": []
}
```

## Next step: unlock publishing

To go from dry-run to actual publishing:

1. Install MatrixMedia GUI → `cli login` per platform
2. Or deploy Postiz instance → `postiz auth:login`
3. Pass `--human-approval-token` for explicit single-publish approval

The adapter stays at dry-run until these steps are complete.
