# Douyin intake — 游戏创作竟然这么简单 / Claude Code Game Studios

- Source short URL: `https://v.douyin.com/eXy5Uoy0wNQ/`
- Canonical: `https://www.douyin.com/video/7650447512389651775`
- IES source used for extraction: `https://www.iesdouyin.com/share/video/7650447512389651775/`
- Author: 老马快下班
- Published: 2026-06-13 18:00:00
- Stats at extraction: 366 likes, 329 collects, 54 shares, 7 comments
- Local evidence: `/Users/charles/.hermes/docs/private/douyin-game-creation-7650447512389651775/`

## Media evidence

- `router_item.json` — extracted Douyin metadata
- `video.mp4` — downloaded video
- `contact_frames.jpg` — frame contact sheet for OCR/visual analysis
- `frames/frame_*.jpg` — sampled frames

## OCR / visible content

The video introduces GitHub project:

- `Donchitos/Claude-Code-Game-Studios`
- GitHub: `https://github.com/Donchitos/Claude-Code-Game-Studios`
- Repo description from GitHub API/README: “Turn Claude Code into a full game dev studio — 49 AI agents, 72/73 workflow skills, and a complete coordination system mirroring real studio hierarchy.”
- GitHub facts at extraction: about 21.5k stars, 3.1k forks, MIT license, created 2026-02-12, updated 2026-06-14.

Visible video phrases:

- “克劳德代码游戏工作室”
- “把一个 Claude Code 的会话变成一个完整的游戏开发工作室”
- “49名特工、73项技能、一个协调一致的游戏团队”
- “游戏创作者的硬核黑科技来了”
- “门槛直接被压到地板上”
- “现在在 GitHub 上已经拿下 21K 星标”
- “49个专业技能代理分工协作”
- “覆盖从玩法构思、代码编写、美术设计、音频制作”
- “到测试上线的完整开发链路一站式搞定”
- “从项目起步 创建脑爆 架构”
- “设计、开发、测试、发布”
- “没有落空，一个人也能做出工业化标准的完整游戏”
- “真正的开发利器”

README structure verified:

- Agents: 49 specialized agents across design, programming, art, audio, narrative, QA, production.
- Skills: 73 slash commands, including `/start`, `/brainstorm`, `/design-system`, `/create-epics`, `/create-stories`, `/dev-story`, `/story-done`, `/gate-check`, `/qa-plan`, `/release-checklist`.
- Hooks: 12 scripts for commit/push/assets/session lifecycle/compact/agent audit/gap detection.
- Rules: 11 path-scoped coding standards for gameplay, engine, AI, UI, network, shaders, tests, docs, assets.
- Templates: 41 docs such as GDD, UX specs, ADRs, sprint plans, HUD design, accessibility.

## What it really is

This is not “AI can magically make games”. It is a **studio-process scaffold for Claude Code**:

1. Decompose game creation into roles.
2. Encode domain-specific agents and slash-command workflows.
3. Add hooks/rules/templates as quality rails.
4. Keep the human as product/creative decision maker.
5. Use staged gates from brainstorm → design → epic/story → implementation → QA → release.

The valuable pattern is the operating system, not the specific game code.

## Transferable Hermes patterns

### 1. Domain-studio workflow pack

Game development is a good stress test for Hermes Workflow Packs because it spans:

- product/creative direction
- technical architecture
- asset pipeline
- UI/UX
- QA/playtest
- release/live ops

Useful abstraction:

```text
Domain Studio Pack = roles + commands + gates + templates + path rules + session hooks + evidence log
```

### 2. Human-controlled multi-agent collaboration

README explicitly says it is collaborative, not autonomous:

- Ask
- Present 2–4 options
- User decides
- Draft
- Approve

This maps well to Hermes safety preference: structure and expertise without silent autonomous writes.

### 3. Path-scoped rules

The `.claude/rules` directory maps file domains to standards. Hermes can absorb the abstraction:

```text
path/domain -> applicable rules -> proof gates -> allowed side effects
```

### 4. Skill workflow catalog

The slash-command catalog is equivalent to a domain-specific workflow registry. Hermes should learn the registry shape, not import every command directly.

### 5. Session lifecycle hooks

The repo uses hooks for session start/stop, pre/post compact, audit trail, and gap detection. Hermes already has stronger control-plane concepts; the reference reinforces lifecycle observability and compaction recovery.

## Risks / non-goals

- Do not install `.claude` settings/hooks into Hermes or any project without explicit approval.
- Do not treat star count or social video popularity as engineering proof.
- Do not bulk-import 49 agents/73 skills into active Hermes skills.
- Do not imply AI game creation is trivial; game quality still needs engine/runtime/profiling/playtest evidence.
- Do not let a fixed studio hierarchy overrule a small solo-project lightweight path.

## Recommended absorption

Create a Hermes task to design a **Game/Creative Studio Workflow Pack reference adapter**:

- Evidence-first read-only intake of `Donchitos/Claude-Code-Game-Studios`.
- Extract command taxonomy, role taxonomy, path-rule taxonomy, hook taxonomy, and template taxonomy.
- Convert into a generic Workflow Pack schema.
- Keep actual installation/import behind human gate.

## Initial verdict

Worth learning as a domain workflow/studio-organization reference. Best absorbed into Hermes Agent/Workflow Builder as a pack pattern:

```text
Domain Studio = role graph + command graph + artifact graph + gates + path rules + session lifecycle evidence
```

Not suitable as a direct dependency or universal agent architecture.
