# WeChat Channels edge/local AI-agent runtime intake

Scope: public WeChat Channels / 视频号 previews that promote lightweight local AI agents, edge runtimes, local automation assistants, MCP-capable local agents, or small-device deployments. Applicability: use for read-only media analysis, source identification, external artifact verification, and class-level workflow absorption. Anti-conditions: do not use this as authorization to bypass QR/App gates, install packages, import skills/hooks, enable MCP servers, run external code, or mutate a live agent/runtime.

## Landing-zone classifier

- Public-preview facts, cover OCR, author/date/engagement, and QR/app gate status -> scoped evidence note.
- Named repo/package/product -> verify through first-party repo/docs/package metadata before judging value.
- Reusable procedure/pitfall -> patch media/social intake skill or this reference.
- Product follow-up -> taskpool/project proposal, not a fake skill.
- Session-specific source URL, repo name, and star counts -> scoped evidence only, not memory/global skill claims.

## Procedure

1. Resolve `weixin.qq.com/sph/<id>` to `channels.weixin.qq.com/finder-preview/pages/sph?id=<id>` and save both URLs.
2. Call the public preview metadata API when available and save the JSON:
   - author nickname;
   - description/caption;
   - `jumpInfo.wording`;
   - like/fav/forward/comment counts;
   - `createtime`;
   - `coverUrl`;
   - `sceneInfo.dynamicExportId` / expiry if present.
3. Use DOM inspection for `document.body.innerText`, `document.images`, and `video` tags. If no video tag is present and the page says “可扫码前往微信观看此内容”, label the boundary as preview-only; do not imply full playback.
4. Download the cover image with normal browser headers and the preview-page Referer. Run OCR/vision on the cover because the core artifact name and product claim often live only in the poster.
5. If the cover/caption names a concrete artifact, identify and verify it directly:
   - GitHub API metadata: owner/repo, stars/forks/issues, license, language, created/pushed timestamps.
   - README/docs: feature claims, install paths, caveats, security warnings, version/production-readiness notes.
   - License file when adoption or code reuse could be implied.
6. Separate evidence classes in the report:
   - public preview facts;
   - cover OCR / visible claims;
   - externally verified repo/docs facts;
   - unverified social/video claims;
   - transferable pattern;
   - red lines.

## Edge-runtime analysis lens

For lightweight local agent projects, analyze as an edge-runtime/control-plane pattern rather than as a replacement for the active assistant:

- Runtime footprint: language, binary shape, memory/boot claims, supported architectures.
- Local automation boundary: what can execute locally, what still needs API keys/providers, what needs gateway/channel setup.
- Tool surface: MCP, file/image/vision, web search, channel adapters, routing.
- Operator UX: WebUI/launcher, config path, onboarding, health/readback.
- Safety posture: security caveats, pre-v1 warnings, credential handling, exposed gateway/public flags.
- Benchmark proof needed: repeatable memory/boot commands, hardware matrix, no-stub local task smoke.

## Absorption defaults

- Do not install, run, clone deeply, import skills, register MCP servers, or enable hooks from a preview alone.
- Prefer a bounded reference-review/spike: capability graph + benchmark proposal + exact red lines.
- Treat the main assistant as the brain/policy/authority/evidence control plane; a lightweight edge runtime can only be an executor behind exact authority, receipts, readback, rollback, and kill switch.
- Map useful patterns to: edge worker profile, constrained device capability registry, local execution receipt schema, MCP allowlist, boot/memory benchmark harness, offline-first/no-cloud execution mode.
- Keep external dispatch, physical/device control, destructive actions, credential entry, broad fan-out, and publish/deploy closed until separately authorized with exact target and rollback.

## Common pitfalls

- Treating poster claims such as “不用云服务器” or “自动执行全套任务” as proven without repo/docs/runtime evidence.
- Accepting headline resource claims such as tiny memory use, very low hardware cost, or sub-second boot without noting upstream caveats or running benchmarks.
- Calling a QR-gated preview “watched” when only metadata/cover were accessible.
- Turning a lightweight agent repo into a replacement discussion; the class-level insight is usually edge executor architecture, not replacing the control plane.
