# GitHub Agent Repositories Evidence Packet

Version: 1.0.0
Captured: 2026-07-09
Purpose: initial live GitHub evidence for using open-source agent projects as role-pattern, orchestration-pattern, executor, or discovery references for Root-Cause Ownership Council.

## Evidence boundary

This packet is not an endorsement, dependency decision, or production integration approval. It records live GitHub API/readme facts observed during research. Re-check before adoption because repository status, license, and maintenance can change.

## Repository classes

### Role / agent-team pattern sources

Use these to extract reusable role cards and team workflow patterns.

| Repo | Observed evidence | Fit |
|---|---|---|
| `FoundationAgents/MetaGPT` | GitHub API: ~69k stars, MIT, Python, pushed 2026-01-21. README describes "The Multi-Agent Framework" and "Assign different roles to GPTs" / software-company multi-agent system. | Strong role decomposition source: PM, architect, engineer, QA, reviewer patterns. Use as inspiration, not direct runtime default. |
| `OpenBMB/ChatDev` | GitHub API: ~33k stars, Apache-2.0, Python, pushed 2026-06-29. Description: LLM-powered multi-agent collaboration for development. | Software-lifecycle role source. Good for developer/reviewer/tester separation. |
| `crewAIInc/crewAI` | GitHub API: ~55k stars, MIT, Python, pushed 2026-07-08. Description: role-playing autonomous AI agent orchestration. | Good role+goal+task+crew pattern. |
| `crewAIInc/crewAI-examples` | GitHub API: ~6k stars. README lists full applications: content creator flow, email responder, lead scoring, meeting assistant, game builder, landing page, marketing, screenplay writer. | Concrete examples for role/task cards and workflow packaging. |
| `camel-ai/camel` | GitHub API: ~17k stars, Apache-2.0, Python, pushed 2026-07-07. Topics include multi-agent systems and AI societies. | Good for agent society / role-play / critic patterns. |

### Runtime / orchestration pattern sources

Use these to study graphs, handoffs, state, control planes, checkpoints, review loops, and runtime packaging.

| Repo | Observed evidence | Fit |
|---|---|---|
| `langchain-ai/langgraph` | GitHub API: ~36k stars, MIT, Python, pushed 2026-07-06. Description: "Build resilient agents." | Strong for turning R-B-H-F-E-O-S into state graph with checkpoints and human gates. |
| `microsoft/agent-framework` | GitHub API: ~12k stars, MIT, Python, pushed 2026-07-08. Description: building/orchestrating/deploying AI agents and multi-agent workflows in Python/.NET. | Production orchestration reference, especially multi-provider and multi-runtime patterns. |
| `microsoft/autogen` | GitHub API: ~59k stars, CC-BY-4.0, Python, pushed 2026-04-15. README states maintenance mode and directs new users to Microsoft Agent Framework. | Historical multi-agent conversation reference; do not choose for new runtime without migration analysis. |
| `openai/openai-agents-python` | GitHub API: ~27k stars, MIT, Python, pushed 2026-07-08. Description: lightweight multi-agent workflow framework. | Handoffs, guardrails, tracing, simple workflows. |
| `google/adk-python` | GitHub API: ~20k stars, Apache-2.0, Python, pushed 2026-07-08. Description: code-first toolkit for building/evaluating/deploying agents. | Evaluation/deployment reference, especially Gemini/Google ecosystem. |
| `agno-agi/agno` | GitHub API: ~41k stars, Apache-2.0, Python, pushed 2026-07-08. README emphasizes control plane, tracing, scheduling, RBAC, human review loops, multi-channel interfaces. | Strong control-plane and governance reference. |

### Executor / validation sources

Use these as possible worker adapters or inspiration for execution lanes, not as governance authority.

| Repo | Observed evidence | Fit |
|---|---|---|
| `anthropics/claude-code` | GitHub API: ~136k stars, Python, pushed 2026-07-08. Description: terminal agentic coding tool. | Coding executor. Governance and evidence gates should remain outside it. |
| `google-gemini/gemini-cli` | GitHub API: ~105k stars, Apache-2.0, TypeScript, pushed 2026-07-08. Description: open-source AI agent in terminal. | Coding/review/CLI executor, useful with Gemini strengths. |
| `browser-use/browser-use` | GitHub API: ~103k stars, MIT, Python, pushed 2026-07-08. Description: make websites accessible for AI agents. | Browser automation/validation reference. Real mobile/PWA/iOS acceptance still needs device/runtime evidence. |

### Discovery indices

Use these to find candidates, not as technical proof.

| Repo | Observed evidence | Fit |
|---|---|---|
| `e2b-dev/awesome-ai-agents` | GitHub API: ~28k stars. README describes open-source and closed-source agent list plus web UI filter. | Ecosystem discovery source. |
| `kyrolabs/awesome-agents` | GitHub API: ~2.5k stars. README categories: frameworks, testing/evaluation, software development, research, conversational/general, game/simulation, knowledge management, automation, browser, multimodal. | Ecosystem discovery and taxonomy source. |

## Adoption rules

1. Resolve repo identity and license before any copy/adoption.
2. Inspect code and examples, not just README/star count.
3. Extract small patterns first: role card, handoff protocol, evidence gate, graph node, control-plane guard.
4. Keep Hermes as control plane / ledger / evidence / policy layer unless a later explicit integration gate authorizes otherwise.
5. Treat external agents as worker adapters or reference implementations, not authority sources.
6. Do not import secrets, logos, product names, installer chains, or unofficial API flows.
7. Before runtime integration, create a scoped evaluation profile, run local smoke tests, and record readback evidence.
