# Douyin memory-system OSS intake pattern

Use when a Douyin/short-video post compares agent memory systems, OpenClaw/Hermes memory, MCP memory servers, graph memory, or related OSS projects. This reference captures the reusable workflow from the `surrealdb-knowledge-graph-memory`/Qmemory intake, without making that one repo a default dependency.

## Landing-zone classifier

- **Reusable architecture pattern** → skill/reference: graph memory substrate, scoped recall, evidence/write-back gates.
- **Specific repo facts** → scoped evidence note with URL, commit/API metadata, package metadata, and anti-conditions.
- **Concrete Hermes implementation** → taskpool/proposal with acceptance criteria; do not create a fake “install this repo” skill.
- **Session progress** → do not persist except in the evidence note.

## Evidence steps

1. Resolve `v.douyin.com` to the canonical `iesdouyin.com/share/{note|video}/{id}/` URL.
2. Parse `window._ROUTER_DATA` when available and save item metadata: author, desc, stats, images/video candidates, comments.
3. Download only lawful/available note images or sampled frames into a request-specific evidence directory.
4. OCR/visually inspect the media and separate visible text from inference.
5. If the post references OSS by name or screenshot text, verify directly against GitHub/NPM/PyPI/docs before judging value.
6. Capture repo metadata and package metadata together; mismatches are high-signal risk evidence.
7. Write a scoped intake note with: source facts, OCR, verified repo facts, transferable patterns, what not to copy, risks, and recommended absorption path.

## Memory OSS evaluation checklist

When evaluating a memory-system repo from social media, check:

- Storage model: flat files, vector DB, SQL/graph DB, event log, or projection layer.
- Data model: session/message/memory/entity/task/tool-call/agent identity/edge types.
- Retrieval: graph neighborhood, full-text/BM25, vector similarity, recency fallback, reranking, and token budgeting.
- Write path: evidence refs, categories, scope, salience/confidence, validity intervals, version lineage, contradiction handling.
- Injection path: where memory enters prompts, max token budget, project/task/channel scoping, and stale-fact filtering.
- Side effects: background linkers/reflection/decay jobs, whether they mutate durable memory directly, and auditability.
- Integration boundary: native plugin, MCP server, CLI, HTTP API, or library; note host assumptions like OpenClaw/Claude/Hermes.
- Maturity risks: stars/forks are weak evidence but useful context; stronger signals are tests, releases, package metadata consistency, docs matching dependencies, and reproducible examples.

## Transferable pattern for Hermes-like agents

Prefer absorbing the **class-level architecture** rather than the library:

1. Create a read-only memory graph projection over existing sources first: sessions, user memory, skills, project profiles, taskpool, cron output, gateway source, evidence notes.
2. Add a scoped recall API that takes objective/project/task/session/channel/risk/max_tokens and returns a small evidence-linked context pack.
3. Keep write-back governed: produce memory candidates with landing-zone classification; reject session progress from durable memory; route procedures to skills, project facts to profiles, and implementation work to taskpool.
4. Share the same recall API across subagents, cron, gateway, mission ticks, and main chat instead of giving each channel a separate ad-hoc prompt builder.
5. Treat compaction and memory as separate layers: context compression should flush/anchor high-salience facts before summary, but not become the durable memory store.

## Pitfalls

- Do not treat a social-media comparison screenshot as engineering proof.
- Do not install or register a memory repo just because it looks cleaner in a post.
- Do not replace existing memory with an unverified repo without a harness and rollback plan.
- Do not let background LLM linkers/reflectors mutate durable memory without audit/proposal gates.
- Do not give subagents/cron unrestricted global recall; scope and evidence gates are mandatory.
- If README and package metadata disagree (for example required DB major version vs dependency major version), report it as a compatibility risk before recommending adoption.

## Suggested final framing

- Verdict: worth absorbing / partial / not worth it.
- Evidence: canonical post, local evidence directory, verified repo/package facts.
- Real object: what the repo/system actually is.
- Absorb: architecture patterns only.
- Do not copy: dependency, side effects, or unverified claims.
- Next step: no action, taskpool proposal, or implementation harness.
