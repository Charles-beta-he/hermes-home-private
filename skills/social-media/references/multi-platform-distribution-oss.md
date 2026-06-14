# Multi-platform social distribution OSS patterns

## Scope and applicability

This reference is a **scoped OSS candidate map**, not a global endorsement. Use it when a user asks to evaluate or prototype multi-platform social/video distribution for agent-generated content packages. The named repositories below are examples verified in one research session; future agents must re-check live repo state, licenses, and supported-platform claims before integration.

Anti-conditions:

- Do not use this as proof that any platform can currently be posted to from the local machine.
- Do not treat listed repositories as installed, configured, authenticated, or production-ready.
- Do not copy GPL/AGPL source into a proprietary/private product without a license review; prefer external CLI/API boundaries.
- Do not auto-publish public content without explicit user approval.

## Evidence-first verification workflow

1. Search GitHub for both Chinese and international platform terms:
   - Chinese lane: `多平台 发布 小红书 抖音 B站 视频号`, `视频 矩阵 发布 小红书 抖音 快手`.
   - International lane: `postiz social media scheduling`, `social media scheduler open source`, `crosspost social media`.
2. For each candidate, verify with repo metadata and local source/docs inspection, not README claims alone:
   - stars/forks/update/license;
   - supported platform list;
   - presence of concrete adapters/selectors/API providers;
   - CLI/MCP/API boundary;
   - login model and publish-history/status model.
3. Write a compact private evidence note before recommending integration.
4. Treat platform posting as an external side effect: default to draft/fill/preview, not silent publish.

## Candidate map from verified OSS

### Chinese platform lane

Best first adapter candidate: `hanliang97/MatrixMedia`

- Electron + Puppeteer + CLI + MCP.
- Targets documented in its CLI skill: `dy | tt | ks | blbl | bjh | sph | xhs` for 抖音、头条、快手、B站、百家号、视频号、小红书.
- Agent-friendly artifacts:
  - `CLI_SKILLS.md` documents `cli login`, `cli publish`, `cli accounts`, `cli history`.
  - `.cursor/skills/matrixmedia-cli-publish/SKILL.md` gives AI-callable workflow and failure handling.
  - `mcp/src/tools/publish.ts` exposes a `publish_video` MCP tool.
- Login caveat: CLI login is Douyin-only in docs; non-Douyin platforms require the user to log in once in GUI, then CLI reuses the session partition.
- License caveat: GPL-2.0 — prefer external CLI/MCP boundary rather than copying source.

Selector/payload reference candidate: `gitcoffee-os/postbot`

- TypeScript/Plasmo extension, Apache-2.0.
- Has concrete platform publisher files under `src/media/publisher/platform/` for video/moment/article/audio.
- Verified 小红书 video publisher uploads via file input, fills title/content/cover, and only clicks publish when `contentData.isAutoPublish` is true.
- Good source for selectors and platform field limits; less direct as an adapter because it is extension/content-script oriented.

Heavy queue reference candidate: `kebenxiaoming/matrix`

- Python + Playwright scripts for 抖音、快手、视频号、小红书.
- Has queue/login/upload scripts and MySQL/Redis/supervisor assumptions.
- Useful for learning queue/cookie patterns, but too heavy for a first prototype.

### International platform lane

Best first adapter candidate: `gitroomhq/postiz-agent`

- CLI for Postiz API aimed at agents.
- Supports commands like `postiz integrations:list` and `postiz posts:create`.
- Multi-platform example uses comma-separated integration IDs.
- Needs Postiz hosted/self-hosted instance and connected integrations.

Full platform reference candidate: `gitroomhq/postiz-app`

- AGPL-3.0 social scheduler with providers for international platforms such as X, LinkedIn, YouTube, TikTok, Instagram, Facebook, Reddit, Mastodon, Bluesky, etc.
- Prefer API/CLI use or external-service boundary; avoid copying AGPL code unless obligations are acceptable.

Lightweight scheduler reference candidate: `Anil-matcha/Free-AI-Social-Media-Scheduler`

- MIT, Next.js app; README says YouTube and TikTok live, other platforms coming soon.
- Good for UI/scheduling reference, not a complete multi-platform base yet.

## Recommended adapter abstraction

Define a platform-neutral publish package and adapter boundary:

```ts
type PublishPackage = {
  title: string
  body?: string
  tags?: string[]
  media: { type: 'image' | 'video'; path: string }[]
  cover?: string
  platformOverrides?: Record<string, unknown>
}

type DistributionAdapter = {
  platform: string
  checkLogin(): Promise<LoginStatus>
  mapPayload(pkg: PublishPackage): Promise<PlatformPayload>
  dryRun(pkg: PublishPackage): Promise<DryRunResult>
  fillDraft(pkg: PublishPackage): Promise<DraftResult>
  requestPublish(pkg: PublishPackage): Promise<PublishRequest>
  history(): Promise<PublishHistory[]>
}
```

First prototype acceptance:

- Generate `publish-package.json` and per-platform mapped payloads.
- Check login/account status when adapter supports it.
- Run dry-run/preview only; do not publish.
- Record proof: command, mapped payload, login status, and adapter limitations.

## Governed local dry-run adapter pattern

When the user approves moving from research to implementation, land a **local dry-run adapter** before any browser automation or public publishing:

1. Write tests first for safety behavior: `publish` mode rejects without explicit approval; generated commands contain preview/draft markers; all results have `will_publish=false`.
2. Implement a small local script that reads `publish-package.json`, validates media paths, maps platform-neutral fields to MatrixMedia/Postiz command previews, and emits an evidence JSON bundle.
3. Treat missing external binaries as a reported login/status field such as `unknown_binary_missing`, not as a reason to fake success or execute publish.
4. Keep GPL/AGPL projects behind CLI/API/MCP boundaries. Do not copy their source into Hermes/private code.
5. Store evidence under a request-specific directory and commit only redaction-safe JSON/text artifacts; generated demo media can remain untracked if ignored.
6. Taskpool closeout should cite script, test, sample package, dry-run result, and proof/selfcheck, while clearly saying the publish executor remains unopened.

This pattern turns “OSS can support distribution” into a governed artifact chain: package -> adapter mapping -> login/status preview -> dry-run evidence -> human approval boundary.

- If the prototype becomes a Hermes-local artifact, record it in taskpool with evidence paths and a scoped commit; do not leave the follow-up as chat-only.

## Red lines / pitfalls

When a user approves a researched OSS distribution path with wording like “认可 / 全盘落地”, treat that as approval to land the **safe local dry-run layer**, not approval to log in or publicly publish.

A good first implementation slice is:

1. Add a small standalone adapter script that reads `publish-package.json` and emits evidence JSON.
2. Keep GPL/AGPL projects behind external CLI/API/MCP command previews; do not vendor or copy their source.
3. Implement adapters as planners first: validate package shape, map fields, build login/status and draft/publish command previews, and set `will_publish=false`.
4. Add tests that prove:
   - `mode: "publish"` is rejected without a separate explicit approval gate;
   - MatrixMedia/Postiz plans stay at `dry-run`/`draft` and do not execute publish;
   - the CLI writes a readable evidence bundle.
5. Store a sample package and dry-run output under a request-scoped evidence directory; include only non-secret fixture paths and redacted/non-real account identifiers.
6. If committing evidence in a governed repo, avoid evidence JSON keys/values that trip secret scanners (`credential`, `auth`, `password`, `token`, etc.). Prefer neutral wording such as `human_control_boundary: "human_only_no_secret_entry"`.

This pattern moves from “there are OSS candidates” to a usable Hermes/Solo Pipeline seam while preserving the human approval boundary.

## Red lines / pitfalls

- Do not type passwords, verification codes, or account secrets. User must handle login/QR/phone verification.
- Do not silently auto-publish. Public publish requires explicit human approval.
- Do not store plaintext credentials in skills, task notes, memory, or docs.
- Browser automation is brittle: selectors, anti-bot, and UI changes require health checks and clear failure evidence.
- Be explicit about licenses: GPL/AGPL projects are safer as external commands/services than copied code.
- Distinguish capability claims from verified source evidence; inspect actual adapters/providers before declaring support.
