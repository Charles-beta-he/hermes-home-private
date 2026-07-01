# External Demo → Cross-End Project Landing

Use when the user approves absorbing an external/social/demo effect and says to add it as a project or land it across ends.

## Classifier

Split the conversation outcome before writing durable state:

- Reusable UX/capability pattern → project SSOT or skill reference.
- Project-specific paths, source URLs, evidence files, task IDs → project profile/progress ledger, not global skill body.
- Concrete implementation work → taskpool/Kanban cards with evidence gates, not a fake “done” skill.
- User preference/style correction → memory/user profile plus the governing skill if it changes the workflow.
- Session progress → ledger only; do not save to global memory unless it is a stable profile/SSOT pointer.

## Landing sequence

1. Restate the absorbed capability as owned product language, not the reference brand/skin.
2. Create a project profile and SSOT root before runtime work when the user says “添加项目 / 落地到各端”.
3. Write at least:
   - `00-model/<project>-ssot.md` — objective, thesis, absorbed assets, rejected mechanics, hard boundaries.
   - `01-contract/<capability>-contract.md` — shared states/props/stage contract/end-specific projection rules.
   - `02-roadmap/<end>-landing-roadmap.md` — per-end order and acceptance evidence.
   - `03-evidence/source-evidence-index.json` — source artifacts and boundaries.
   - `progress-ledger.md` — current truth, components, relations, open gates, proof.
4. Register the project in Portfolio OS / project registry when available, with relations and merge policies.
5. Create taskpool/Kanban cards for each real implementation surface; each card must include:
   - SSOT/contract/ledger paths.
   - source evidence path.
   - red lines and anti-conditions.
   - acceptance evidence: code/test/build plus screenshot/readback/delivery proof as appropriate.
6. If the user explicitly says `全盘推进`, `不要有剩余`, or equivalent, do not stop at cards when a safe local reversible slice exists. If the exact production repo/surface is not authorized or not yet identified, land a local SSOT runtime prototype or dry-run harness that proves the absorbed pattern with owned naming, tests/static verifier, browser/readback evidence, and ledger/profile writeback. Close cards only when that prototype genuinely satisfies their scoped acceptance; otherwise keep production integration as a separately gated surface.
7. Run JSON/profile/doctor/readback verification before claiming projectization is complete.
8. If commit is blocked by a pre-existing secret scan or unrelated dirty worktree, do not bypass hooks or stage unrelated files. Report the scoped commit boundary and leave the files uncommitted.

## Acceptance wording

Safe claim:

> Project/profile/SSOT/ledger/tasks are landed and verified; runtime implementation remains pending per-end evidence.

Unsafe claim:

> The feature is implemented across all ends.

Use the unsafe claim only after each end has same-slice code, tests, screenshots/readbacks, and ledger updates.
