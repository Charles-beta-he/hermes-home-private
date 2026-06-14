# Better-T-Stack intake: workflow / Agent Builder relevance

Captured: 2026-06-14

## Source

- Site: https://www.better-t-stack.dev/
- Docs: https://www.better-t-stack.dev/docs
- Agent workflows: https://www.better-t-stack.dev/docs/cli/agent-workflows
- Programmatic API: https://www.better-t-stack.dev/docs/cli/programmatic-api
- Project structure: https://www.better-t-stack.dev/docs/project-structure
- Config: https://www.better-t-stack.dev/docs/bts-config
- Compatibility: https://www.better-t-stack.dev/docs/cli/compatibility
- GitHub: https://github.com/AmanVarshney01/create-better-t-stack
- npm: https://registry.npmjs.org/create-better-t-stack/latest

## Canonical facts

Website description:
- `A modern CLI tool for scaffolding end-to-end type-safe TypeScript projects with best practices and customizable configurations`

GitHub API:
- repo: `AmanVarshney01/create-better-t-stack`
- language: TypeScript
- license: MIT
- stars at capture: 5459
- forks at capture: 303
- open issues: 144
- created: 2025-02-10
- pushed: 2026-06-13
- topics include: better-auth, bun, cli, drizzle-orm, expo, fumadocs, hono, prisma, shadcn-ui, tanstack-router, turborepo, typescript

npm latest:
- package: `create-better-t-stack`
- version: 3.33.0
- bin: `create-better-t-stack: dist/cli.mjs`
- license: MIT
- latest published: 2026-06-13

## Surface summary

Better-T-Stack scaffolds end-to-end type-safe TypeScript projects. It supports:
- frontend: TanStack Router, React Router, TanStack Start, Next, Nuxt, Svelte, Solid, Astro, React Native, none
- backend: Hono, Express, Fastify, Elysia, Convex, self, none
- runtime: Bun, Node, Cloudflare Workers, none
- database: SQLite, Postgres, MySQL, MongoDB, none
- ORM: Drizzle, Prisma, Mongoose, none
- API: tRPC, oRPC, none
- auth: Better Auth, Clerk, none
- payments: Polar, none
- addons: Turborepo, Nx, PWA, Tauri, Electrobun, Biome, Lefthook, Husky, Starlight, Fumadocs, Ultracite, Oxlint, MCP, OpenTUI, WXT, Skills, Evlog, etc.
- examples: todo, ai, none
- deployment surfaces: Cloudflare Workers / infra via Alchemy docs

## Agent/workflow-specific value

The most relevant page is `/docs/cli/agent-workflows`. It provides a JSON-first, schema-driven automation path:

- `create-json`: create project from a single JSON payload.
- `add-json`: add addons to an existing project from JSON.
- `schema --name ...`: runtime schema introspection for CLI/createInput/addInput/addonOptions/dbSetupOptions.
- `mcp`: local stdio MCP server exposing:
  - `bts_get_stack_guidance`
  - `bts_get_schema`
  - `bts_plan_project`
  - `bts_create_project`
  - `bts_plan_addons`
  - `bts_add_addons`
- `--dry-run`: safe planning without file writes.
- Programmatic API: `create()` / `add()` from TypeScript/JavaScript, silent by default, returns Result rather than exiting process.

Important field discipline from docs:
- MCP tools expect a full explicit config, not a partial payload.
- Explicitly set frontend/backend/runtime/database/orm/api/auth/payments/addons/examples/dbSetup/webDeploy/serverDeploy/git/packageManager/install.
- `addons` and `examples` should be explicit arrays; use `[]` when none.
- `dbSetup`, `webDeploy`, and `serverDeploy` should be explicit even when `none`.
- `git`, `install`, and `packageManager` should always be explicit.
- For MCP project creation, `install` should usually be `false` because dependency installation can exceed client timeouts; run install separately.
- Call plan tools before create/add tools.

## Why this matters for Hermes Workflow / Agent Builder

Better-T-Stack is a useful reference for turning a natural language workflow/app request into a safe, reproducible, schema-validated build plan:

1. Schema-first stack compiler
   - User intent -> explicit JSON config -> compatibility validation -> reproducible command/config.
   - Hermes analogue: natural-language Workflow Pack compiler should emit explicit workflow JSON/YAML, not hidden prompt state.

2. Plan-before-write gate
   - `--dry-run`, `bts_plan_project`, and `bts_plan_addons` provide non-mutating previews.
   - Hermes analogue: proposal-only execution policy projection before write/side effect.

3. Runtime schema introspection
   - `schema --name ...` makes the CLI itself the source of truth for input shape.
   - Hermes analogue: Workflow/Agent Builder should expose schema introspection so agents do not hardcode stale option sets.

4. Full explicit config
   - Avoids ambiguous defaults in agent automation.
   - Hermes analogue: generated workflows should declare surfaces, permissions, model routing, evidence gates, install/write behavior, and deploy targets explicitly.

5. Compatibility matrix
   - CLI validates stack combinations (DB/ORM/backend/runtime/frontend/API).
   - Hermes analogue: workflow compiler should reject invalid module combinations before dispatch.

6. Reproducible config file
   - `bts.jsonc` records stack choices and reproducible command.
   - Hermes analogue: every Workflow Pack/Agent Card should have a generated lock/config capturing choices, schema version, reproducible creation command, and later `add` compatibility state.

7. Addon ecosystem as pack pattern
   - Addons like MCP, skills, ultracite, biome, oxlint, pwa, docs are modular selectable capabilities.
   - Hermes analogue: Workflow Pack modules should be addable through declarative pack options, not hand-edited hidden conventions.

## Gaps / caveats

- It is web/TS-stack scaffolding, not a general workflow runtime.
- It can write files and install dependencies; intake should remain read-only unless explicitly creating a project.
- MCP server exists, but installing/adding it to Hermes or editors is a side effect and should be gated.
- Compatibility and schemas should be read from current CLI/docs when used; do not freeze a one-time list globally.
- It optimizes app scaffolding, not taskpool truth, evidence lifecycle, human gates, or long-running workflow closeout.

## Absorb recommendation

Create a Hermes evolution task:

`Better-T-Stack JSON-first scaffold pattern：吸收到 Hermes Workflow/Agent Builder 编译器`

Acceptance target:
- Define a Hermes workflow/app scaffold compiler pattern:
  1. intent intake
  2. schema introspection
  3. explicit config generation
  4. compatibility validation
  5. dry-run/proposal output
  6. human gate for writes/install/deploy
  7. reproducible lock/config
  8. add-on/pack mutation path
- Keep Better-T-Stack as reference; do not install/run or create a real project unless separately authorized.

## Red lines

- Do not run `create-better-t-stack` to create files unless the user asks for an actual project.
- Do not run dependency install as part of analysis.
- Do not register its MCP server in Hermes/editor config without explicit authorization.
- Do not treat it as the Hermes workflow runtime; use it as a schema-first scaffold/compiler reference.
- Do not let generated app config become taskpool SSOT; Hermes taskpool/evidence ledger remains authority.
