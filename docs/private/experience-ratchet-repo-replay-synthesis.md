# Experience Ratchet repo replay synthesis

Created: 2026-05-23

## Summary

The first source-backed repo replay batch has been converted into Experience Ratchet atoms and proposal-only artifacts.

Validated object counts:

- Atoms total: 10
- New repo replay atoms: 9
- Proposal artifacts: 9
- MemoryMaze relations added: 6
- Direct memory/skill/profile/Hermes-core mutations: 0

## Atoms

| Atom | Project | Landing zone | Status | Claim |
|---|---|---|---|---|
| agentmemory-82cf8de92265 | agentmemory | project_doc | promoted_candidate | Shared agent memory should be treated as a local server boundary with explicit REST/MCP/plugin contracts, not as direct global memory writes. |
| agentmemory-1b5ce49966a9 | agentmemory | public_consensus | promoted_candidate | Memory supersession/versioning is safer than overwriting memories because it preserves auditability and rollback paths. |
| bytebot-f8e27c2932a5 | bytebot | project_doc | promoted_candidate | Desktop/computer-use agents need an explicit external-control safety boundary before Hermes can adopt takeover or action APIs. |
| bytebot-0bb88eef12ce | bytebot | public_consensus | promoted_candidate | NEEDS_HELP/NEEDS_REVIEW style task states are reusable for fail-closed human takeover instead of pretending autonomous completion. |
| openclaw-wrong-source-ad275766a45a | openclaw-wrong-source | public_consensus | promoted_candidate | Wrong-source repository hypotheses must be retained as superseded/revoked evidence instead of silently overwritten. |
| karpathy-skills-4bddfedcd6b1 | karpathy-skills | skill | promoted_candidate | Simplicity-first coding guidance should be applied as thin verified slices, not as a ban on long-term architecture. |
| rag-anything-ad6e571324cd | rag-anything | project_doc | promoted_candidate | Document intelligence should preserve structure/layout and modal decomposition before semantic retrieval. |
| hermes-upstream-ratchet-3e3fa53b5dd1 | hermes-upstream-ratchet | public_consensus | promoted_candidate | Upstream synchronization must be ratchet-style: detect, review, stage, verify, then promote; never auto-pull into private/main. |
| hermes-upstream-ratchet-b1b0b8bc42f5 | hermes-upstream-ratchet | skill | promoted_candidate | No-agent cron jobs should be silent on no-op success but fail-closed with evidence on actionable states or errors. |

## MemoryMaze relations

- agentmemory-1b5ce49966a9 similar_to hermes-dev-brain-d6e518cb233e
- agentmemory-82cf8de92265 depends_on hermes-dev-brain-d6e518cb233e
- bytebot-f8e27c2932a5 applies_to hermes-dev-brain-d6e518cb233e
- bytebot-0bb88eef12ce similar_to hermes-upstream-ratchet-b1b0b8bc42f5
- openclaw-wrong-source-ad275766a45a verified_by karpathy-skills-4bddfedcd6b1
- hermes-upstream-ratchet-3e3fa53b5dd1 similar_to hermes-dev-brain-d6e518cb233e

## Proposal artifacts

All artifacts live under:

`/Users/charles/.hermes/experience-ratchet/proposals/`

Generated files:

- proposal-agentmemory-1b5ce49966a9-20260523T082247Z.json
- proposal-agentmemory-82cf8de92265-20260523T082247Z.json
- proposal-bytebot-0bb88eef12ce-20260523T082247Z.json
- proposal-bytebot-f8e27c2932a5-20260523T082247Z.json
- proposal-hermes-upstream-ratchet-3e3fa53b5dd1-20260523T082247Z.json
- proposal-hermes-upstream-ratchet-b1b0b8bc42f5-20260523T082247Z.json
- proposal-karpathy-skills-4bddfedcd6b1-20260523T082247Z.json
- proposal-openclaw-wrong-source-ad275766a45a-20260523T082247Z.json
- proposal-rag-anything-ad6e571324cd-20260523T082247Z.json

## Promotion policy

These are promoted_candidate proposal artifacts, not applied changes. They must be reviewed before patching skills, profiles, public consensus, memory, project docs, or Hermes core.

Hard boundary retained:

- no direct memory write
- no direct skill patch
- no direct profile patch
- no taskpool/core mutation from Experience Ratchet
- no external repo install/run
- no source summary without repo-backed evidence and falsifier

## Verification

Commands run:

```bash
python3 ~/.hermes/scripts/experience-ratchet-maze.py validate
python3 ~/.hermes/scripts/experience-ratchet-maze.py query
find ~/.hermes/experience-ratchet/proposals -maxdepth 1 -type f -name '*.json' | wc -l
```

Observed:

- validate: ok, checked=10
- query: count=10
- proposals: count=9
