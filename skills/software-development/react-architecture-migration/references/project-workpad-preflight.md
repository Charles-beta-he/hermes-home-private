# React Project Workpad Preflight

Extracted from `/Users/charles/.hermes/skills/software-development/react-architecture-migration/SKILL.md` on 2026-07-01T08:54:33.968451+00:00 to reduce root SKILL.md load while preserving detailed workflow content. The root skill keeps a progressive-loading pointer to this reference.

## Project Workpad Preflight (Long-running Frontend Loops)

Before starting a long-running React/frontend closure loop, especially when the user says “继续下一步”, “loop”, “pua-loop”, “A+”, or when a project-specific Workpad exists:

1. Load/read the project Workpad from `~/Documents/brain/05-实践与项目/projects/<project>/Workpad - <project>.md` if present.
2. Treat Workpad North Star, Red Lines, Anchors, Skill Route, Business Flow Matrix, and Acceptance Matrix as the active project contract.
3. If the Workpad references a comparison/prototype anchor, verify the anchor path exists before claiming parity. If the expected reference path is missing but a candidate exists elsewhere, record it as unresolved/provisional and ask or explicitly flag before parity-diff work.
4. Do not write project-specific transient state to global memory; update the Workpad/Evidence Ledger instead.
5. After each loop, deposit evidence into `docs/UI_TEST_CASES.md`, ADRs when needed, and the Workpad Evidence Ledger.
