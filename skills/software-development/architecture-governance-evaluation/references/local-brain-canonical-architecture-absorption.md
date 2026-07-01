# Local Brain to Canonical Architecture Absorption

Scope: architecture/governance work where a Hermes project has accumulated local-brain artifacts (profiles, SSOTs, progress ledgers, phase docs, receipts, gate packets, projections) and the user asks to abstract, consolidate, or avoid patchwork documentation.

Applicability:
- User asks to “向上抽象”, “不要补丁式屎山”, “结合本地大脑整理记录”, or to turn existing workflow/control-plane evidence into a long-term architecture packet.
- There are multiple local-brain sources with overlapping target models, phase ledgers, ADRs, gate packets, or project profiles.

Anti-conditions:
- Do not use this to rewrite runtime behavior, execute side effects, or claim implementation completion from docs alone.
- Do not copy task progress or one-off receipts into global memory/skills; keep them in project profile/ledger or a scoped absorption map.
- Do not delete or rename old evidence before a manifest-backed archive/disposition phase.

## Procedure

1. Establish the canonical trunk
   - Pick one long-term architecture packet/SSOT path.
   - Name the architecture and runtime/kernel abstraction.
   - Declare that old phase docs become source/evidence unless explicitly marked active subsystem specs.

2. Inventory local-brain sources
   - Project profile.
   - SSOT/model docs.
   - Architecture/schema docs.
   - Roadmaps/progress ledgers.
   - Gate packets and remaining-gate indexes.
   - Projection/doctor reports.
   - High-risk receipts/certifications.
   - Taskpool/mission/concurrency plans.

3. Classify each source
   - active vision/source;
   - active schema/source;
   - active subsystem spec;
   - project-local progress ledger;
   - historical evidence;
   - high-risk receipt/certification;
   - public derivative.

4. Extract transferable patterns
   - Entity-strip local paths, task IDs, message IDs, branch names, and one-off timestamps.
   - Keep relationships: default-off gates, shadow-first promotion, exact-target authority, evidence closure, readiness-before-scale, resume-as-routing, interruptibility policy, projection-only terminal slices.

5. Land in canonical docs
   - Vision/principles: high-level thesis and theory-to-constraint mapping.
   - Current architecture map: source roles and existing component boundaries.
   - Target architecture: desired runtime/control loop.
   - Domain model: Intent/Evidence/Gate/Closure/Compensation objects.
   - Authority doc: side-effect taxonomy, default-off, exact high-risk requirements.
   - Runtime surfaces: Control Tower/dashboard/gateway/resume/interruptibility.
   - Migration roadmap: strangler phases plus readiness-before-scale.
   - Verification doc: closure, compensation, high-risk smoke, and scale acceptance.
   - ADR/source index: disposition for old docs.
   - Absorption map: table from old local-brain source -> pattern -> canonical landing.

6. Update scoped local brain
   - Update the project profile with canonical packet pointers and target abstraction names.
   - Append a progress-ledger record with scope, files changed, absorbed sources, and explicit non-runtime boundary.
   - Do not store project-specific paths or session outcomes in global memory.

7. Verify
   - Check required docs exist and are referenced by the index.
   - Parse any updated JSON project profile.
   - Read back progress ledger marker.
   - Report untracked/dirty boundaries and avoid mixed commits when unrelated dirty files exist.

## Output shape

Report:
- canonical packet path;
- architecture/runtime names;
- absorbed source list;
- docs updated;
- project profile / ledger writeback;
- verification evidence;
- boundaries not crossed;
- next safe step, usually disposition banners or a lightweight doc doctor.
