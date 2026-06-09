# Self-strengthening external repo intake and gap-analysis pattern

Use this when the user shares a GitHub repo/article with language like `分析强化自身`, `吸收`, `强化自己`, `全盘推进`, or gives a high-value AI/agent/RAG/tooling repo for Hermes improvement.

## Goal

Do not merely summarize the repo. Convert it into a governed Hermes self-strengthening path:

1. live source inspection,
2. capability classification,
3. Hermes gap analysis,
4. taskpool intake with dependency/priority metadata,
5. plan/update anchor,
6. health verification.

## Minimal live inspection

Before creating a task:

- Confirm repo exists via GitHub API or live page.
- Capture repo stats and metadata: `full_name`, description, stars, forks, language, license, default branch.
- Inspect top-level contents.
- Read README and, when available, at least one docs/modules/tests surface.
- Extract architecture signals, not marketing claims.

Examples of useful signals:

- OpenHands: SDK, CLI, Local GUI REST API + React SPA, Cloud integrations/RBAC/collaboration, Enterprise VPC/Kubernetes, top-level runtime/frontend/enterprise/containers/tests.
- RAG-Anything: document parsing, multimodal content decomposition, modal processors, LightRAG/multimodal KG, modality-aware retrieval, direct content-list insertion, failure-mode docs, parser/processor/query/resilience modules.

## Classification rule

Default self-strengthening repos to:

- `lane=evolution`
- `project=hermes-agent`
- `architecture_target=local-brain` for runtime, memory, evidence, taskpool, skills, orchestration, local plugin, or agent execution patterns.
- `requires_multimodel=true` when implementation could change control-plane behavior, privacy boundaries, permission gates, or evidence lifecycle.

Priority guidance:

- P1 when the repo directly strengthens evidence-first execution, false-completion prevention, recovery/recall, or taskpool safety.
- P2 when it is high-value reference architecture but not immediately gating correctness.
- P3 for ecosystem/watchlist items without a bounded implementation slice.

## Gap analysis artifact

For high-value repos, write a concise gap-analysis document under `docs/private/` before or alongside task creation. Include:

- live source evidence,
- core architecture signals,
- Hermes current gap,
- capability mapping,
- smallest verifiable integration slice,
- red lines / anti-drift constraints,
- follow-up task shape.

Do **not** claim integration just because a gap analysis exists.

## Task metadata to include

Use `brain_task_orchestrator.py add` with rich metadata:

- `--capability-delta`: what Hermes gains if the pattern is absorbed.
- `--anti-drift-check`: non-integration and safety boundaries.
- `--acceptance-evidence`: live inspection + gap doc + prototype/tests + control-plane checks.
- `--dependency-order`: where it sits relative to active capability bundles.
- `--parallel-boundary`: explicit non-goals such as no clone/install/cloud login/external agent/private file processing.
- multimodel contract fields when required.

## Plan anchor

If an existing capability-bundle plan is active, patch it with a class-level node for the new reference pattern, including:

- purpose,
- live source inspection summary,
- absorbable mechanisms,
- red lines,
- landing surfaces.

This prevents external repo insights from becoming isolated one-off tasks.

## Verification

After intake:

1. Read back/search for the created task file.
2. Patch the task note with actual source-intake proof, validation rows, blockers, and final handoff.
3. Run taskpool health checks when tools are available:
   - dispatch tick summary,
   - `proof-check`,
   - `selfcheck`.
4. Record verification artifact paths in the task note.

## Pitfalls

- Do not create vague `analyze repo X` tasks after the user asks to strengthen Hermes; classify and encode acceptance before intake.
- Do not clone/install/run an external agent or RAG stack during intake unless the user explicitly asks and safety boundaries are clear.
- Do not add heavyweight dependencies to Hermes core as the first step; prefer stdlib/local manifests and proof artifacts for the initial slice.
- Do not let RAG/retrieval outputs override taskpool policy, source provenance, or user/developer instructions.
- Do not index or store secrets; redaction status must be explicit for evidence/indexing prototypes.
