# Hermes Project Scaffold Matrix v0

日期: 2026-06-22
任务: t_1ad1d3d1
来源评估: `/Users/charles/.hermes/docs/private/create-better-t-stack-hermes-scaffold-eval-20260622.md`

## 0. 边界

本 v0 只落在 docs + skill + stdlib Python validator + fixtures，不改 Hermes core，不引入 Better-T-Stack 依赖，不写真实用户项目目录。

目标是把 Hermes 项目脚手架从“临场口头 checklist”提升为可组合、可校验、可回放、可证明的能力矩阵。后续只有在多个项目验证稳定后，才考虑进入 `hermes project init`、taskpool hook 或 GUI/TUI Stack Builder。

## 1. Matrix contract

输入为一个 JSON object。v0 推荐字段如下:

```json
{
  "project_name": "portfolio-pwa",
  "target": "greenfield | existing_project | migration",
  "surfaces": ["web_frontend", "mobile_pwa", "backend_api"],
  "frontend": {
    "framework": "react | vue | next | nuxt | svelte | astro | none",
    "language": "typescript | javascript",
    "task_runner": "vite | turborepo | nx | pnpm | npm | bun",
    "pwa": true
  },
  "backend": {
    "kind": "api | fullstack | none",
    "framework": "hono | express | fastapi | spring | none",
    "runtime": "node | bun | deno | workers | workerd",
    "api": "rest | trpc | graphql | orpc | rpc"
  },
  "cloudflare": {
    "pages": true,
    "workers": true
  },
  "addons": ["mcp", "skills", "browser_harness"],
  "mcp": {"servers": ["filesystem"]},
  "skills": {"names": ["baseline-ui"]},
  "browser_harness": {"viewports": ["desktop_1280", "mobile_375"]},
  "proof_gate": {
    "required": true,
    "commands": ["npm run build"],
    "evidence": ["validator_json", "build_log", "browser_smoke"],
    "review_required": true
  }
}
```

v0 validator deliberately keeps the schema permissive in places where Hermes projects differ, but fail-closes on rules that protect real delivery: incompatible task runners, Cloudflare Workers backend/runtime constraints, missing addon prerequisites, and missing proof evidence.

## 2. Capability matrix

| Capability | JSON surface / object | v0 meaning | Required proof |
|---|---|---|---|
| Web frontend | `surfaces: ["web_frontend"]`, `frontend` | Browser-delivered UI, admin UI, landing page, dashboard, or SPA/SSR app | static validation, package/build command, browser smoke when UI is generated |
| Mobile/PWA | `surfaces: ["mobile_pwa"]`, `frontend.pwa=true` | Web app must include mobile viewport and installability/offline-sensitive checks | mobile 375 viewport proof, PWA manifest/service-worker proof when generated |
| Backend/API | `surfaces: ["backend_api"]`, `backend` | API/server layer, including serverless-compatible APIs | compile/test command, API smoke command, contract evidence |
| Cloudflare Pages | `cloudflare.pages=true` or `cloudflare_pages` | Frontend deploy target on Pages | frontend object required, browser smoke recommended/required for Pages stacks |
| Cloudflare Workers | `cloudflare.workers=true`, `backend.runtime=workers` | Edge server target on Workers/workerd | Hono/no custom backend in v0, workers smoke evidence required/recommended |
| MCP | `addons` contains `mcp`, plus `mcp.servers` | Scaffold includes MCP server/client integration contracts | server list and follow-up MCP smoke plan |
| Skills | `addons` contains `skills`, plus `skills.names` | Scaffold includes Hermes skill references or generated skill skeletons | skill names and reload/read verification plan |
| Browser harness | `addons` contains `browser_harness`, plus `browser_harness.viewports` | Scaffold must be accepted through real browser automation | desktop_1280 and/or mobile_375 viewport evidence |
| Evidence/proof gate | `proof_gate.required=true` | Generation is not done until evidence exists | commands and evidence arrays are mandatory |

## 3. Constraint rules in validator v0

Implemented in `/Users/charles/.hermes/scripts/project_scaffold_matrix_validator.py`:

| Rule id | Failure condition | Reason |
|---|---|---|
| `schema.project_name.required` | missing/empty `project_name` | proof and ledgers need a stable spec name |
| `schema.surfaces.required` | missing/empty `surfaces` | no capability target means no meaningful proof plan |
| `surface.web_frontend.frontend_required` | web surface without `frontend` | prevents UI task with no UI contract |
| `surface.mobile_pwa.pwa_required` | mobile/PWA surface without `frontend.pwa=true` | avoids treating ordinary desktop web as mobile/PWA-ready |
| `surface.backend_api.backend_required` | backend surface without `backend` | prevents API tasks without API contract |
| `frontend.task_runner.mutual_exclusion` | more than one of `vite`, `turborepo`, `nx` | mirrors Better-T-Stack-style task runner conflict protection |
| `cloudflare.workers.backend_runtime` | Workers stack with backend framework other than Hono/none | v0 supports only Hono/no custom backend on Workers |
| `cloudflare.workers.runtime` | Workers stack with non-workers backend runtime | keeps Workers target explicit |
| `cloudflare.pages.frontend_required` | Pages target without frontend | Pages deploy requires web output |
| `addon.mcp.servers_required` | `mcp` addon without `mcp.servers` | addon cannot be verified without server contract |
| `addon.skills.names_required` | `skills` addon without `skills.names` | generated/attached skills must be named |
| `addon.browser_harness.viewports_required` | browser harness addon without viewports | browser proof must state target viewports |
| `proof_gate.required` | proof gate not explicitly required | scaffold must fail closed by default |
| `proof_gate.commands.required` | proof gate has no commands | no runnable verification path |
| `proof_gate.evidence.required` | proof gate has no evidence artifacts | prevents “command ran but proof not consumable” |

Warnings keep v0 flexible while nudging better evidence:

- `schema.surfaces.unknown`: unknown surfaces are advisory until the matrix stabilizes.
- `frontend.task_runner.unknown`: unknown runners are allowed but flagged.
- `addon.browser_harness.viewport_coverage`: recommend Hermes canonical desktop/mobile viewports.
- `proof_gate.validator_json.recommended`: structured validator output should be captured for taskpool/kanban.
- `proof_gate.workers_smoke.recommended`: Workers stacks should prove edge/serverless behavior.
- `proof_gate.browser_smoke.recommended`: Pages/web stacks should prove browser behavior.

## 4. Proof plan levels

The validator outputs `{valid, errors, warnings, proof_plan}` for every spec.

Tier 0:
- `schema_and_matrix_validation`: run this validator and capture JSON.
- `dry_run_manifest_review`: review intended file manifest and reproducible spec before writing to a real project.

Tier 1:
- `declared_verification_commands`: run project-specific build/test/typecheck commands.
- `browser_harness_smoke`: required for Pages, useful for all web/PWA stacks.
- `cloudflare_workers_smoke`: required for Workers stacks.

Tier 2:
- `human_review_gate`: enabled by default because scaffolded code often needs human review before merge/write.
- `evidence_bundle`: collect declared proof artifacts into a durable task/kanban handoff.

## 5. Fixtures

Fixture root: `/Users/charles/.hermes/fixtures/project_scaffold_matrix`.

Valid:
- `valid/fullstack-cloudflare-pages.json`: covers web frontend, mobile/PWA, backend/API, Cloudflare Pages/Workers, MCP, skills, browser-harness, and proof gate.

Invalid:
- `invalid/task-runner-mutual-exclusion.json`: rejects mutually exclusive task runners.
- `invalid/workers-runtime-backend.json`: rejects Express on Cloudflare Workers runtime.
- `invalid/addon-prerequisites.json`: rejects MCP/skills/browser-harness addons without their prerequisite config.
- `invalid/proof-gate-required-fields.json`: rejects empty proof commands/evidence.

## 6. Validator usage

Single spec:

```bash
python3 /Users/charles/.hermes/scripts/project_scaffold_matrix_validator.py \
  /Users/charles/.hermes/fixtures/project_scaffold_matrix/valid/fullstack-cloudflare-pages.json \
  --pretty
```

Fixture suite:

```bash
python3 /Users/charles/.hermes/scripts/project_scaffold_matrix_validator.py \
  --check-fixtures /Users/charles/.hermes/fixtures/project_scaffold_matrix \
  --pretty
```

The script exits 0 for valid specs and fixture suites that match expected validity; it exits 1 for invalid specs or fixture mismatches. Invalid spec output still includes a proof plan so downstream tools can show what would be needed after the user fixes the errors.

## 7. Promotion path

Do not wire this into Hermes core yet. Recommended next steps after v0 has been used on 2-3 real project specs:

1. Add JSON schema generation or stricter schema docs if the permissive v0 shape causes ambiguity.
2. Add a dry-run scaffold manifest generator that produces file plans without writing real project directories.
3. Add taskpool intake conversion from a validated spec to ordered tasks/DAG.
4. Add addon registry entries for MCP, skills, PWA, Cloudflare, browser-harness, and proof harness.
5. Only then consider a formal `hermes project init` or `hermes project validate` CLI surface.
