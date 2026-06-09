# cmux architecture/security intake for Hermes taskpool

Source: user reply referencing prior cmux analysis. Target repo identified and inspected:
- GitHub: https://github.com/manaflow-ai/cmux
- Local clone used for intake: `/tmp/hermes-cmux-analysis`
- Commit inspected: `83dfeab` on `main` (tag/nightly at clone time)
- Description: Ghostty-based macOS terminal with vertical tabs and notifications for AI coding agents
- License: repository API license `NOASSERTION`; `LICENSE` states dual license: GPL-3.0-or-later + commercial license.

## User intent

Add follow-up work to taskpool from prior cmux analysis. User specifically replied to the section that proposed deeper study:

- competitor/product analysis around OpenCode/Codex terminal workflows and cmux moat:
  - native performance
  - agent notifications
  - browser automation
  - CLI/socket primitives
  - remote workspace
- architecture source deep-dive:
  - `Sources/TerminalController*`
  - `Sources/Workspace*`
  - `CLI/cmux.swift`
  - `Packages/CmuxControlSocket`
  - `Packages/CmuxSocketControl`
  - `docs/cli-contract.md`
  - `docs/agent-hooks.md`
  - `docs/remote-daemon-spec.md`
  - `docs/agent-browser-port-spec.md`
- security audit focus:
  - socket auth
  - CLI relay auth
  - remote daemon artifact verification
  - hook installer safety

## Intake observations already grounded

Repository/product shape:
- macOS-native Swift/AppKit/SwiftUI app; terminal rendering via libghostty / Ghostty fork.
- Vertical workspace/sidebar + panes + surfaces model.
- CLI/socket API for workspace/pane/surface/browser control.
- Agent hook integrations for Claude Code, Codex, OpenCode, Gemini, Copilot, etc.
- In-app WKWebView browser automation ported from agent-browser concepts.
- Remote SSH workspaces with cmuxd-remote, proxy/relay, persistent PTY sessions.

Relevant docs inspected:
- `README.md`
- `docs/cli-contract.md`
- `docs/agent-hooks.md`
- `docs/remote-daemon-spec.md`
- `docs/agent-browser-port-spec.md`
- `docs/ghostty-fork.md`
- `CONTRIBUTING.md`
- `AGENTS.md`

## Potential Hermes value

Cmux is relevant to Hermes not as code to copy, but as a reference architecture for an AI-agent workspace control plane:

1. Workspace / pane / surface abstraction
   - map to task workspace, execution surface, browser/evidence surface, human attention surface.
2. Agent notification routing
   - map to taskpool events: needs_human_input, awaiting_approval, proof_ready, blocked_by_external.
3. Browser + terminal co-residency
   - map to Hermes browser harness evidence panel bound to a task/workspace.
4. CLI/socket primitives
   - map to stable local control-plane API contracts and self-identify calls.
5. Agent hook/session restore pattern
   - map to AgentAdapter lifecycle/session/resume contract with safety gates.
6. Remote workspace/daemon pattern
   - map to edge-worker or remote execution adapters while preserving taskpool SSOT.

## Constraints / anti-drift

- Do not copy GPL-licensed code into Hermes. Treat cmux as architectural reference unless commercial/license compatibility is explicitly resolved.
- macOS binding is acceptable for this exploration, but Hermes SSOT/taskpool schema must not become macOS-only; macOS-specific UI/socket/browser surfaces should remain adapters.
- Do not auto-install cmux, hooks, or third-party agents during intake.
- Security audit must be evidence-first: read source and tests before making safety claims.
- Distinguish product inspiration from implementable Hermes primitives.

## Proposed task acceptance

Deliver a grounded report under `~/.hermes/docs/private/` covering:
- cmux moat/product analysis vs Ghostty/tmux/Zellij/Warp/Cursor/Claude Code Teams/OpenCode/Codex workflows;
- source architecture map for TerminalController, Workspace, CLI, socket packages, browser automation, remote daemon, hooks;
- security audit of socket auth, CLI relay auth, remote artifact verification, hook installer, resume command signing/approval, secret scrubbing, browser automation boundary;
- Hermes mapping: what to absorb, what not to absorb, and staged implementation plan for local-brain/taskpool/browser-harness;
- license/compliance boundary and macOS adapter boundary.
