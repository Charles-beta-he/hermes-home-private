# Social/repo intake evidence — Douyin VibeCoding / claude-workflow-studio

Date: 2026-06-13

## Social source

- Source text from user: `4.12 复制打开抖音，看看【不想上学真菌的图文作品】「VibeCoding大赏」。请允许我介绍一下cl... https://v.douyin.com/44yeP0XZOi8/ rRK:/ 10/03 q@E.us :3pm`
- Resolved URL: https://www.douyin.com/note/7648901090390618538
- Page title: `「VibeCoding大赏」。请允许我介绍一下claude- - 抖音`
- Author visible on Douyin page: `不想上学真菌`
- Published at: `2026-06-08 14:02:45`
- Visible metrics at intake: likes `3467`, comments `132`, another visible count `1824`, another visible count `258`; author profile shows fans `211`, total likes `5918`.
- Visible description excerpt: “「VibeCoding大赏」。请允许我介绍一下claude-workflow-studio：一个多agent工作流管理平台，提供可视化和便捷的工作流搭建……给我经常使用的claude code也建立一个这样的可视化平台……通过系统级别的限制，严格让AI按照你在图形界面搭好的工作流上面跑，避免了因AI幻觉而导致工作流跑偏的问题……从一开始的‘表面上遵循跑通’到现在能做到真正的严格遵循……”
- Hashtags/keywords visible: `#vibecoding大赏 #ai新星计划 #ai`.

Interpretation: treat the Douyin post as a lead. The claim to evaluate is not “viral video quality”; it is a concrete workflow-control pattern: visual workflow DAG + system-level guardrails forcing Claude Code / agents to follow an explicit graph instead of prompt-only workflow adherence.

## Canonical mapping

GitHub Search for exact `claude-workflow-studio` mapped to:

- Repo: https://github.com/FocuZHe/claude-workflow-studio
- Full name: `FocuZHe/claude-workflow-studio`
- Description: `Web-based visual platform to orchestrate multi-agent Claude Code workflows. Create agents, chain them into pipelines, watch them collaborate in real time.`
- Stars/forks at intake: 53 stars / 9 forks
- Language: JavaScript
- Default branch: `master`
- License: MIT
- Topics: `claude-code`, `express`, `javascript`, `multi-agent`, `nodejs`, `typescript`, `websocket`, `workflow`
- Updated at: 2026-06-13T15:25:13Z

## Repo structure inspected

Top-level:
- `.gitattributes`, `.gitignore`, `LICENSE`, `README.md`, `README_EN.md`
- Windows helper scripts: `install.bat`, `start.bat`, `stop.bat`, `restart.bat`, `logs.bat`, startup scripts
- `bin/`, `dist/`, `docs/`, `scripts/`, `src/`, `tests/`, `screenshots/`
- `ecosystem.config.js`, `package.json`, `package-lock.json`, `tsconfig.json`, `tsconfig.frontend.json`

`src/`:
- `src/client/`
- `src/server/`
- `src/types/`

Docs:
- `docs/architecture.md`
- `docs/architecture_EN.md`
- `docs/frontend-backend-mapping.md`
- `docs/full-sdk-architecture.md`
- migration/optimization docs

## README / architecture signals

README claims:
- Web visual platform to orchestrate/monitor/manage multiple Claude Code agents.
- Experimental preview; author explicitly warns not production-tested and not for important files without review.
- Features include: dual-track closed-loop architecture, visual workflow builder, 6 node types, workflow templates, skills market, AI judgement node, human approval node, WebSocket streaming, checkpoint resume, memory system, embedded PTY terminal, multiple workspaces, task queue, knowledge base, analytics, crash recovery, read-only AI chat, API key encryption, command whitelist, concurrency protection, workspace sandbox.
- Stack: HTML/CSS/TypeScript/JS SPA, Node.js + Express + TypeScript, WebSocket `ws`, Claude Agent SDK / Anthropic SDK, `sql.js` WASM SQLite + JSON files, `node-pty` terminal.

Architecture docs signals:
- System diagram: browser SPA → HTTP/WS → Express/WebSocket server → service layer → TypeScript state machine → Claude Agent SDK subprocesses → checkpoint/output → WebSocket broadcast.
- Key motto: “脑子归 AI，手脚归代码” — TypeScript code controls workflow execution; main agent cannot fake child-agent execution.
- Workflow DAG is parsed/topologically sorted, nodes executed by code; parallelism via `Promise.all`, approval via Promise suspension, conditions via AI JSON evaluation.
- `full-sdk-architecture.md` mentions p-limit concurrency, AbortController/SIGKILL lifecycle, event flow, worktree isolation, retry/backoff, logs, model aliases.
- `frontend-backend-mapping.md` maps UI buttons/pages to API endpoints and WebSocket events.

## Hermes interpretation

This maps directly to Hermes Workflow/Agent Builder preferences:
- visual workflow as projection/UI, not canonical task state;
- code-governed DAG execution instead of prompt-only compliance;
- node-level gates: agent, condition, approval, subworkflow, end;
- checkpoint/resume and event stream for observability;
- workspace/worktree isolation;
- explicit human approval boundary;
- command whitelist and sandbox red lines.

Potential landing zones:
- Hermes workflow-orchestrator / Agent Builder control plane.
- Taskpool evidence DAG and Mission runner projection.
- Dashboard read-only workflow graph projection.
- Event-governed side-effect executor patterns.

Risks / anti-drift:
- Repo is experimental and Windows-oriented; do not copy runtime wholesale.
- Do not let a visual builder become a second SSOT over taskpool/Mission ledgers.
- Do not import its skills market or execute arbitrary skill installation during intake.
- PTY/terminal and file manager are high-risk surfaces; require allowlist, audit, and human gate before any Hermes implementation.
- Treat stars/social post as weak signal; use repo code/docs as source of architectural evidence.
