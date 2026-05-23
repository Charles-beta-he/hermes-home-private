# Experience Ratchet repo replay matrix

Created: 2026-05-23
Purpose: drive source-backed open-source repository replay through taskpool into ExperienceAtom / MemoryMaze / proposal-only promotion.

## Governance

- Do not generalize from old task summaries alone; every atom must cite source repo metadata, checked commit or freshness result, and an existing or refreshed gap artifact.
- Do not directly write memory / skills / profiles / Hermes core from replay tasks.
- Taskpool is execution/lifecycle; Experience Ratchet remains the state machine and promotion gate.
- Multi-model review is required for cross-repo consensus and promoted_candidate/public_consensus proposals, not for mechanical source freshness rows.

## Replay batch A

| Order | Repo | Existing artifact | Intended extraction | Status |
|---:|---|---|---|---|
| 10 | bytebot-ai/bytebot | docs/private/bytebot-gap-analysis.md | desktop agent external-control, takeover, NEEDS_HELP/NEEDS_REVIEW, security caveats | taskpool intake |
| 20 | rohitg00/agentmemory | docs/private/agentmemory-gap-analysis.md | shared memory server, hook lifecycle, supersession/versioning, retention/privacy | taskpool intake |
| 30 | VoltAgent/awesome-openclaw-skills | docs/private/openclaw-garden-skills-gap-analysis.md | wrong-source correction, supersede/revoke example | taskpool intake |

## Replay batch B

| Order | Repo | Existing artifact | Intended extraction | Status |
|---:|---|---|---|---|
| 40 | multica-ai/andrej-karpathy-skills / forrestchang/andrej-karpathy-skills | docs/private/andrej-karpathy-skills-gap-analysis.md | coding behavior rules with applicability/anti-conditions | queued after batch A |
| 50 | HKUDS/RAG-Anything | docs/private/rag-anything-hermes-gap-analysis.md | multimodal ingestion, structured parsing, modality-aware retrieval | queued after batch A |
| 60 | NousResearch/hermes-agent | docs/private/upgrade-sop.md + overlay-registry.md | upstream semantic ratchet review, fail-closed certification, no-agent cron silence | queued after batch A |

## Cross-repo synthesis

Runs after repo-level extraction tasks produce validated/normalized atoms.

Expected outputs:
- MemoryMaze relations: derived_from, depends_on, contradicts, supersedes, falsified_by.
- Promotion candidates separated by landing_zone.
- Rejected / normalized-only atoms with falsifiers and dissent preserved.
- Proposal artifacts under `~/.hermes/experience-ratchet/proposals/` only.
