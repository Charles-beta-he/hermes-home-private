# Superagent Research Harness Absorption Pattern

Scope: domain-level workflow-capability-graph reference for analyzing public media leads about deep-research agents, superagent harnesses, evidence-search workflows, multi-agent report generators, and skill/tool marketplaces. Applicability: use when the user asks to learn/absorb/analyze a project shown in a video or public post and wants transferable workflow architecture. Anti-conditions: do not use this as permission to install third-party runtimes, copy external skills into a live profile, bypass login/app gates, or treat marketing claims as verified runtime proof. Falsifier: if direct execution on a real task contradicts the claimed workflow, demote the affected claim to artifact-specific evidence only.

## Transferable pattern

Treat public media as a lead, not proof. Verify the underlying artifact directly before generalizing.

```text
public media lead -> visible facts/OCR -> external artifact verification -> research task graph -> evidence ledger -> claim map -> structured report -> adaptation boundary
```

## Evidence tiers

```yaml
preview_facts:
  - canonical/resolved URL
  - author/channel/date/location when visible
  - caption text
  - cover-frame OCR
  - QR/app/login gate status

verified_artifact_facts:
  - official repo/site/package/docs URL
  - API/readme metadata
  - license/default branch/language/update timestamps
  - architecture/docs/source readback

unverified_claims:
  - marketing claims from video/caption
  - hidden app-gated content
  - performance/quality claims not reproduced locally
```

## Capability graph

```yaml
atomic_modules:
  - public_media_intake
  - research_intent_router
  - research_plan_builder
  - source_card_normalizer
  - claim_map_builder

composite_workflows:
  - external_artifact_verification
  - parallel_evidence_collection
  - report_synthesis_workflow

gates:
  - preview_boundary_gate
  - artifact_verification_gate
  - citation_gate
  - artifact_readback_gate
```

## Research workflow contract

```text
question/scope
-> research plan: dimensions, hypotheses, source strategy, data requirements, report skeleton
-> parallel evidence collection: web/API/repo/docs/domain collectors
-> source cards: URL, title, date, claim, reliability
-> claim map: clustered claims + citations + contradictions
-> synthesis: chaptered report, tables/charts, executive summary
-> readback: artifact exists, citation links, limits labeled
```

## Implementation ratchet after absorption

When the user says “全盘推进 / project-level authorization / until human intervention,” do not stop at the analysis document if safe reversible work remains. Progress through owned boundaries in this order and verify each slice:

1. **Static source-card prototype**
   - Input: explicit source JSON or manually verified preview/repo facts.
   - Output: `evidence-ledger.json` + `report.md`.
   - Gate: every major claim must have a source card; hidden/app-gated content remains labeled unverified.

2. **Read-only public API collector**
   - Example capability: GitHub public API repo metadata + README from `owner/repo`.
   - No credentials required; no install; no external write.
   - Test URL parsing, API payload normalization, README decoding, and CLI wiring with fake fetchers before live smoke.

3. **Explicit local readback collector**
   - Read only user/agent-provided file paths from a cloned repo or docs bundle.
   - Mark reliability as local readback and use `file://` citations.
   - Do not recursively scan broad trees unless separately authorized; explicit file lists are safer and reproducible.

4. **Manifest runner**
   - Store reproducible source declarations in a manifest with fields like `sources`, `github_repos`, and `local_sources`.
   - CLI should accept `--sources`, `--github-repo`, `--local-source`, and/or `--manifest` and merge them into one graph.
   - Smoke with JSON validation, file-size/readback, source-card count, citation-gate status, and boundary flags.

5. **Stop at first real authority boundary**
   - Model/search credentials, autonomous broad web crawling, third-party runtime install, imported third-party skills, login-gated video extraction, and publishing/channel delivery all require explicit authorization.

## Agent wrappers

```yaml
Media Intake Agent:
  wraps: [public_media_intake]
  policy: label QR/app gates; do not infer hidden content
  authority: read_only

Artifact Verification Agent:
  wraps: [external_artifact_verification]
  policy: first-party sources first; record time-scoped facts
  authority: external_read

Research Orchestrator Agent:
  wraps: [research_intent_router, research_plan_builder, parallel_evidence_collection]
  policy: decompose into bounded collectors; preserve evidence ledger
  authority: external_read

Synthesis Agent:
  wraps: [claim_map_builder, report_synthesis_workflow]
  policy: every major claim needs citation; separate facts from promotional claims
  authority: local_write
```

## Verification checklist

- [ ] Public-media facts are separated from artifact facts.
- [ ] QR/app/login gates are explicitly labeled.
- [ ] First-party artifact identity was verified before generalizing.
- [ ] Static source-card tests went RED before implementation.
- [ ] Public API collectors are tested with fake payloads before live smoke.
- [ ] Local readback uses explicit paths and source IDs.
- [ ] Manifest run is reproducible and validates JSON output.
- [ ] Report readback includes source cards, claim map, citation gate, and boundary section.
- [ ] Boundary flags assert no third-party runtime install, no external write, and no hidden gated-content claim.

## Red lines

- Do not bypass QR/app/login gates.
- Do not install external packages, skills, MCP servers, hooks, or agent adapters from a media lead.
- Do not copy external code/skills into a live profile without a provenance/scanner/rollback gate.
- Do not treat popularity metrics, captions, or demo claims as runtime proof.
- Do not claim a report-generation workflow works until it has been run on a real task with configured model/search credentials.

## Adaptation target

The safe first landing is a bounded owned capability package, not a wholesale runtime import:

```text
research-task-graph
+ source/evidence ledger
+ parallel collector roles
+ claim/citation gate
+ report skeleton/synthesis contract
+ artifact/readback proof
```

Only after that should runtime integration, new skills, external tools, or channel write-through be considered behind explicit gates.
