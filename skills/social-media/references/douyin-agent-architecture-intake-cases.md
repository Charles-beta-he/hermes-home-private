# Douyin agent-architecture intake cases

Use this reference after `references/douyin-social-intake-evidence-workflow.md` when a Douyin/TikTok-style post claims an AI-agent memory, collaboration, workflow, or control-plane project is “爆火” or worth absorbing. These notes are case patterns, not endorsements of the named projects.

## Case pattern: memory-system posts

Example source class: posts comparing a hand-assembled memory stack with an OpenClaw/SurrealDB graph memory project such as `qmemory`.

Evidence to capture:
- Canonical short-link redirect and item id.
- SSR `router_data.json`, item summary, images/video frames, and OCR/contact sheet.
- Candidate GitHub/NPM repos from visible text and tags; save repo metadata and README excerpts.
- Compare video/social claims against package/repo facts: stars/forks/version, dependencies, release freshness, license, and compatibility notes.

Reusable analysis lens:
- Separate the storage choice from the architecture: SurrealDB/ChromaDB/etc. is less important than a typed memory substrate with evidence, scope, salience/confidence, validity windows, version lineage, and controlled prompt injection.
- Distinguish context compaction from durable memory retrieval. A compression tool is not a memory graph.
- Treat background linker/reflect/decay features as side-effecting memory writers that need audit/proposal gates.
- Do not replace the active agent memory system from a social post. Absorb class-level patterns into a governed memory graph projection / scoped recall API first.

Recommended verdict shape:
- “Worth absorbing as architecture pattern, not as a direct dependency” unless repo evidence proves maturity and compatibility.

## Case pattern: agent collaboration / workspace posts

Example source class: posts about “OpenAgents Workspace”, “AI Agent 协作系统”, or multiple tools such as Claude Code, Codex CLI, Cursor, and OpenCode sharing one workspace.

Evidence to capture:
- Video frames/contact sheet because key claims are often shown only in slides.
- Visible metrics and repo URL, but mark OCR uncertainty when blurred.
- GitHub API for likely/current repo; explicitly call out mismatches between slide metrics and current repo facts.
- README/AGENTS/INVARIANTS or equivalent governance docs, not just landing page copy.

Reusable analysis lens:
- The valuable abstraction is not “Slack UI for agents”; it is a workroom/control-plane object: objective, participants, shared scoped context, artifacts, evidence refs, decisions, permissions, and acceptance state.
- Multi-agent collaboration must be evidence-first: agents append events/claims/artifacts instead of silently mutating lifecycle.
- Shared browser/file/thread context needs leases, least privilege, redaction, and audit logs.
- Human mentions such as `@agent` should map to bounded work orders, not broad authority.
- If the upstream project includes market/payment/settlement rails, keep that separate from local personal-assistant/workroom applicability.

Recommended verdict shape:
- “Worth absorbing as Agent Workroom / Collaboration OS pattern; do not chase social popularity or import the repo wholesale.”

## Anti-conditions

- Do not promote social star/fork claims unless independently verified by the source repo/API.
- Do not store one-off post URLs in global memory. Keep them in scoped evidence notes.
- Do not create a new skill for each social post. Patch the social-intake workflow or add a scoped reference under the umbrella.
- Do not turn external repo-specific implementation details into global Hermes rules without repeated evidence across sources.
