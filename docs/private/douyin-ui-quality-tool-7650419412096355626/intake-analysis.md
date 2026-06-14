# Douyin 视频：Impeccable / AI UI 反土味设计工具 intake

Captured: 2026-06-14

## Source

Original share:
> 6.17 复制打开抖音，看看【Tony讲实话的作品】AI 写的 UI 巨土？一个开源工具直接根治 自带... https://v.douyin.com/gmLA575Ac-A/ M@W.md DhO:/ :1pm 10/19

Resolved:
- short: https://v.douyin.com/gmLA575Ac-A/
- share: https://www.iesdouyin.com/share/video/7650419412096355626/?from_ssr=1
- canonical: https://www.douyin.com/video/7650419412096355626

Metadata:
- aweme_id: `7650419412096355626`
- author: `Tony讲实话`
- desc: `AI 写的 UI 巨土？一个开源工具直接根治 自带全套设计体系，根治 AI 同质化土味界面，极简快捷指令，抛光、审计、评审一键搞定。兼容 Cursor、Copilot 所有主流 AI 编码工具。#干货分享 #github #UI #网站推荐 #编程`
- create_time: 2026-06-13
- stats at capture: 536 likes, 633 collects, 78 shares, 3 comments
- video downloaded: `video.mp4`
- frame contact sheet: `contact_2s.jpg`
- raw router summary: `router_item.json`

## Video OCR / visible claims

The video recommends an open-source project called `Impeccable`:
- visible tagline: `The design language that makes your AI harness better at design.`
- visible stars in video: around 36.9K; GitHub API at capture reports 38,091.
- visible license: Apache-2.0.

Main claims from video frames:
- AI frontend interfaces are easy to become `土` / generic.
- The tool is a high-star open-source project.
- It includes white-label / top-tier design thinking.
- It has built-in color, typography, layout, motion design system guidance.
- It has 27 design avoidance rules in the video narration/frames; GitHub README says 41 deterministic detector rules.
- Commands mentioned/visible: `impeccable document`, `impeccable extract`, `impeccable shape`, `impeccable critique`, `impeccable audit`, `impeccable polish`, `impeccable pin`, `impeccable detect`.
- It can optimize UI through short commands instead of long prompts.
- It can be used in online collaboration and local/offline modes.
- It supports mainstream AI coding tools like Cursor, Copilot, Codex, Claude Code.

## Canonical GitHub mapping

GitHub search for the tagline confirmed:
- repo: `pbakaus/impeccable`
- URL: https://github.com/pbakaus/impeccable
- description: `The design language that makes your AI harness better at design.`
- language: JavaScript
- license: Apache-2.0
- stars at capture: 38,091
- forks: 2,097
- open issues: 30
- created: 2025-11-16
- pushed: 2026-06-14
- npm package from package.json: `impeccable`, version `2.3.2`, Node >=24.

README confirms:
- `Impeccable` is design guidance for AI coding agents: 1 skill, 23 commands, live browser iteration, and 41 deterministic detector rules.
- Quick start: `npx impeccable skills install`, then `/impeccable init` in the AI coding tool.
- `init` writes `PRODUCT.md` and offers `DESIGN.md` so later commands know audience, brand/product lane, voice, anti-references, colors, type, and components.
- Commands include: craft, init, document, extract, shape, critique, audit, polish, bolder, quieter, distill, harden, onboard, animate, colorize, typeset, layout, delight, overdrive, clarify, adapt, optimize, live.
- CLI detector: `npx impeccable detect src/`, `detect index.html`, `detect https://example.com`, `detect --fast --json .`.
- Supports Cursor, Claude Code, OpenCode, Pi, Gemini CLI, Codex CLI, VS Code Copilot, etc.

## Detector / anti-pattern evidence

The repo's detector registry includes common AI UI slop rules such as:
- side-tab accent border
- border accent on rounded element
- overused fonts
- single font for everything
- flat type hierarchy
- gradient text
- purple/cyan AI color palette
- cream/beige default palette
- nested cards
- monotonous spacing
- bounce/elastic easing
- dark mode with glowing accents
- icon tile stacked above heading
- italic serif display headline
- hero eyebrow / pill chip
- repeated section kicker labels
- numbered section markers
- em-dash overuse
- marketing buzzwords
- aphoristic cadence copy
- oversized H1, etc.

This is exactly the class of issue the user describes: the UI looks ugly/generic, but it is hard to verbalize why. Impeccable turns vague visual dislike into named, deterministic or semi-deterministic findings.

## Value for Hermes / user workflow

High value as a reference and possibly as an optional tool, because it addresses a known delivery gap: AI-generated UI can pass functional checks but still feel generic or ugly.

Best absorption target:
1. Add a `visual-taste anti-slop gate` to UI delivery, before final acceptance.
2. Map Impeccable's anti-pattern taxonomy into Hermes UIMax/design audit language.
3. For projects where Node >=24 and side effects are authorized, optionally run `npx impeccable detect --fast --json .` as an evidence-producing check.
4. Use `/impeccable init`-like context creation as a pattern: product/brand/audience/anti-reference/design tokens must be explicit before UI generation.
5. Use short command semantics (`polish`, `critique`, `audit`, `typeset`, `layout`, `quieter`, `bolder`) as natural-language UI repair intents.

## Fit with existing Hermes skills

Existing Hermes already has:
- `uimax-audit`: broad UI quality audit across visual, responsive, a11y, code, interaction, console.
- `baseline-ui`: typography/motion/accessibility defaults.
- `ckm:design` / `ckm:ui-styling`: brand/design guidance.

Impeccable fills a sharper gap:
- naming generic AI slop patterns;
- deterministic detector rules for some visual/copy/code symptoms;
- command vocabulary for design critique and repair;
- project-local `PRODUCT.md` / `DESIGN.md` context before UI work.

## Boundaries / red lines

- Do not install or run `npx impeccable skills install` automatically; it writes provider skill/hook files.
- Do not modify project hooks (`.codex/hooks.json`, `.cursor/hooks.json`, `.claude/settings.json`) without explicit approval.
- Do not treat Impeccable as the only UI quality authority: it detects anti-patterns, but does not replace real browser verification, viewport screenshots, accessibility, business flow completion, or user taste.
- Do not blindly enforce its taste rules; some projects intentionally use dark glow, Inter, numbered sections, or cards if brand/context supports it.
- If running the CLI, use a dry/read-only detector mode first and record JSON output as evidence.

## Recommended absorption task

`Impeccable：吸收 AI UI 反土味检测到 Hermes UIMax / 视觉品味门禁`

Acceptance target:
- Compare Impeccable taxonomy with current UIMax scoring.
- Add a Hermes `anti_ai_slop` UI audit dimension or subcheck.
- Define optional `impeccable detect --fast --json` integration as read-only evidence, gated by Node/tool availability and user approval.
- Define `PRODUCT.md`/`DESIGN.md`-like context packet for Hermes UI generation.
- Add output format for "你说不出来哪里丑" cases: named issue -> evidence -> why it feels bad -> concrete repair.