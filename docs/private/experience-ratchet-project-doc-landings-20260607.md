# Experience Ratchet Project-Doc Landings — 2026-06-07

This file is the project-document landing artifact for low-risk Experience Ratchet proposals whose `landing_zone` is `project_doc` and `required_human_review=false`.

## Scope

- Landing zone: project_doc
- Policy: proposal-only claims are promoted only after evidence review and a durable doc landing.
- This document does not mutate Hermes core behavior, memory, provider config, credentials, or runtime permissions.

## Landed claims

### agentmemory-82cf8de92265 — local memory server boundary

Claim: Shared agent memory should be treated as a local server boundary with explicit REST/MCP/plugin contracts, not as direct global memory writes.

Operational interpretation:
- Shared memory backends are integration surfaces, not permission to write always-on prompt memory directly.
- Any REST/MCP/plugin bridge must preserve source observation metadata, privacy/retention policy, and rollback/supersession semantics.
- If those controls cannot be verified, the integration remains project-local/advisory.

Evidence refs preserved from proposal:
- file: /Users/charles/.hermes/hermes-agent/docs/private/agentmemory-gap-analysis.md lines 23-37
- repo: rohitg00/agentmemory commit bc641077913c0ac043e702a8f6519189e89b1721
- command: experience-ratchet-maze validate PASS 2026-05-23

Falsifier: if the memory backend cannot enforce retention/privacy/source observation metadata, keep it as project-local artifact only.

### bytebot-f8e27c2932a5 — external-control safety boundary

Claim: Desktop/computer-use agents need an explicit external-control safety boundary before Hermes can adopt takeover or action APIs.

Operational interpretation:
- Desktop/browser/computer-use takeover must remain behind explicit permission, observability, and stop/escape semantics.
- Action APIs that are unauthenticated, privileged by default, or not auditable stay reference-only.
- Evaluation should distinguish read-only observation, mediated action, and privileged external control.

Evidence refs preserved from proposal:
- file: /Users/charles/.hermes/hermes-agent/docs/private/bytebot-gap-analysis.md lines 25-43
- repo: bytebot-ai/bytebot commit 3d37894ce07ef8d8b40adc7fd309ad96c2a71313
- command: experience-ratchet-maze validate PASS 2026-05-23

Falsifier: if action APIs are unauthenticated or privileged by default, integration remains reference-only.

### rag-anything-ad6e571324cd — document intelligence before semantic retrieval

Claim: Document intelligence should preserve structure/layout and modal decomposition before semantic retrieval.

Operational interpretation:
- For PDFs, images, tables, charts, and multi-modal documents, extraction should preserve layout/source spans/artifacts before semantic summarization.
- Retrieval output that cannot cite source spans or structural artifacts remains advisory.
- This claim belongs to document-intelligence/RAG project design, not to global memory or generic search defaults.

Evidence refs preserved from proposal:
- file: /Users/charles/.hermes/hermes-agent/docs/private/rag-anything-hermes-gap-analysis.md lines 19-43
- command: experience-ratchet-maze validate PASS 2026-05-23

Falsifier: if structural extraction cannot cite source spans/artifacts, retrieval output remains advisory only.

## Verification

- Created by bounded full-pool advancement after user authorization on 2026-06-07.
- Expected ratchet validation command: `python3 ~/.hermes/scripts/experience-ratchet-maze.py validate`.
- Transition evidence string should reference this file path and retain proposal-only governance boundary.
