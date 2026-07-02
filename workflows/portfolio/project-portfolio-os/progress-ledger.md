# Progress Ledger — Hermes Project Portfolio Ratchet OS

Updated: 2026-06-21 05:00 CST
Project: `project-portfolio-os`
Type: `portfolio-governance`
Role: portfolio graph, project relation, progress-ledger, and ratchet governance
Status model: unprofiled → profiled → ledgered → contract-ready → validated-slice → promoted → released/observing

## Current truth
- Profile: `/Users/charles/.hermes/project-profiles/project-portfolio-os.json`
- SSOT root: `/Users/charles/.hermes/workflows/portfolio/project-portfolio-os`
- Portfolio OS: `/Users/charles/.hermes/project-profiles/project-portfolio-os.json`
- This ledger is metadata/SSOT only; it does not modify project code.

## Components
| Component | Status | Evidence | Next gate |
|---|---|---|---|
| Project profile | profiled | `/Users/charles/.hermes/project-profiles/project-portfolio-os.json` | keep profile fields current |
| Progress ledger | ledgered | this file | add component-specific proof as work advances |
| Relation graph | ledgered | portfolio registry | verify relations with doctor |
| Implementation/product state | needs-evidence | not inferred by portfolio setup | read project-specific SSOT before claiming progress |

## Relations


## Open gates
1. Add project-specific component inventory from its canonical SSOT/repo without changing code.
2. Attach real proof for any promoted or validated implementation claim.
3. Keep secrets/auth/session/runtime state out of cross-project merge.

## Operating rule
Every material future step must update this ledger with evidence or mark the state as proposal/needs-evidence. Do not rely on chat context for current state.

## Enterprise production landing — 2026-06-21 05:27 CST
- Skill `project-portfolio-operating-system` created and verified by `skill_view`.
- Strict verifier `scripts/portfolio_os_verify.py` returns `ok: true`.
- Silent watchdog `/Users/charles/.hermes/scripts/portfolio_os_watchdog.py` returns `ok: true` and writes latest report.
- Cron watchdog `124af8e50119` scheduled as `portfolio-os-doctor-6h` every 6 hours, deliver local, no-agent.
- Production receipt: `05-status/production-receipt.md`.
- Boundary: no project code changes; UVISA code guard remains active.

## Hermes CLI integration update — 2026-06-21 09:32 CST

### Runtime surface
- `hermes portfolio` now exposes read-only Portfolio OS operator commands in Hermes CLI.
- Subcommands: `status`, `doctor`, `verify`, `projects`.
- JSON output: `--json` supported on default status and subcommands.

### Verification evidence
- `./venv/bin/python -m py_compile hermes_cli/portfolio_os.py hermes_cli/subcommands/portfolio.py hermes_cli/main.py`: pass.
- `./venv/bin/python -m pytest -o addopts='' tests/hermes_cli/test_portfolio_os.py -q`: 7 passed.
- `./venv/bin/hermes portfolio --json`: ok true.
- `./venv/bin/hermes portfolio verify --json`: ok true, 0 errors/warnings.
- `./venv/bin/hermes portfolio doctor`: Portfolio OS OK.
- Independent reviewer: passed true, no security_concerns, no logic_errors.

### Boundaries
- CLI integration is read-only; no project code mutation.
- UVISA profile guard remains enforced.
- Existing non-task Hermes worktree noise was not staged.

## Project candidate signal — Hermes long-term self-extension — 2026-06-21 09:35 CST

### Source signal
User asked whether prior expansion directions and long-term self-extension content can be upgraded into a project.

### Portfolio classification
- Proposed project id: `hermes-self-extension-os`.
- Proposed type: `agent-runtime-evolution / mission-control-plane`.
- Current state: `proposal/needs-evidence`, not implementation-complete.
- Parent relation: governed by `project-portfolio-os`.
- Platform relation: extends `hermes` through governed local runtime/mission-control capabilities.
- Knowledge relation: consumes/promotes reusable patterns through `hermes-skill-learning` and experience-ratchet atoms.

### Upgrade rule
Can become a durable project when it has its own profile, SSOT root, progress ledger, relation graph, promotion policy, and doctor/verify gates. It must remain separate from product projects and must not silently mutate mission cadence/budget, push remote code, deploy, write secrets, or change protected project code.

### Recommended long-term direction
Upgrade as a separate umbrella/control-plane project rather than merging into `hermes` directly. `hermes` remains the runtime/platform; `hermes-self-extension-os` governs research → plan → local proof → review → commit/skill/doctor promotion loops.


## Projectization update — console extension directions — 2026-06-21 09:45 CST
- Added durable project profiles/ledgers for `hermes-self-extension-os`, `hermes-control-console`, and `career-ops`.
- Evidence source: `/Users/charles/Desktop/folder/hermes-control-console/docs/long-term-stable-control-console-plan.md`, `public/hermes-dashboard.json`, and `src/App.tsx` fallback capability directions.
- Classification: console project becomes operator surface project; self-extension becomes mission/control-plane project; career-ops becomes proposal-stage personal-productivity project.
- Boundaries: metadata/profile/ledger only; no UVISA project code change; no console source code change; no push/deploy/external side effect.

## Mineradio reference C-mode rollout — 2026-07-01 09:55 CST
- User directive: exclude UAEC/UVISA work projects; all other ongoing Hermes-managed projects use C-mode (bounded implementation absorption).
- Rollout JSON: `/Users/charles/.hermes/workflows/portfolio/project-portfolio-os/04-merge-candidates/mineradio-c-mode-rollout-2026-07-01.json`
- Rollout summary: `/Users/charles/.hermes/workflows/portfolio/project-portfolio-os/04-merge-candidates/mineradio-c-mode-rollout-2026-07-01.md`
- Registry updated: `reference_absorption_policies[].id = mineradio-reference-c-mode-rollout-2026-07-01`.
- Included projects: hermes, hermes-skill-learning, lark, mobile-offline-avatar-travel, project-portfolio-os, hermes-self-extension-os, hermes-control-console, career-ops, single-session-multitopic-trace, hermes-capability-model-router, hermes-persona-wake-stage, hermes-agent-os-control-plane.
- Excluded projects: `uvisa-app-2.0`, `uaec-h5`.
- Boundary: portfolio rollout is implementation intent/queue, not proof that every project has runtime code changed. Each project must read its SSOT, land a bounded local implementation slice or contract, run proof, and append evidence to its own ledger before being called absorbed.

## Mineradio C-mode absorption intake — 2026-07-01
- Portfolio rollout: `/Users/charles/.hermes/workflows/portfolio/project-portfolio-os/04-merge-candidates/mineradio-c-mode-rollout-2026-07-01.json`
- Mode: C / bounded implementation absorption for non-work project.
- Exclusions respected: no UAEC/UVISA work-project changes from this rollout.
- C targets:
  - Add portfolio-level reference absorption rollout registry and C-mode default for non-work projects.
  - Track per-project absorption proof separately; portfolio relation is not implementation proof.
- Boundary: this intake is not runtime completion; project is only C-absorbed after its own SSOT is read, a bounded local slice or implementation-ready contract is landed, tests/static/browser proof pass, and evidence is appended here.

## Projectization update — Hermes Embodied Workflow OS — 2026-07-02T18:43:34+08:00
- Added durable project profile: `/Users/charles/.hermes/project-profiles/hermes-embodied-workflow-os.json`.
- SSOT root: `/Users/charles/.hermes/workflows/projects/hermes-embodied-workflow-os`.
- Purpose: outer tool/body layer around Hermes brain+CLI; stable workflow core plus adapters for Web/PWA/App/PC/glasses/voice/embedded/robot/NAS/proxy/ExternalControl.
- Research evidence: `/Users/charles/.hermes/workflows/projects/hermes-embodied-workflow-os/02-research/core-works-and-arguments.md` and `/Users/charles/.hermes/workflows/projects/hermes-embodied-workflow-os/02-research/evidence-index.json`.
- Existing project integration map: `/Users/charles/.hermes/workflows/projects/hermes-embodied-workflow-os/03-integration/existing-project-integration-map.md`.
- Multi-model architecture review: `/Users/charles/.hermes/tick-20260702-101349-760163-p20773-dd66cf15-28477ee1/final/certification_manifest.json`; advisory only, not full certification.
- Boundary: metadata/profile/ledger/research only; no source code, hardware, external side effect, cron/gateway/runtime mutation, publish/deploy, destructive operation, credential entry, or physical actuation.

## Update — 2026-07-02T18:58:00+08:00 — hermes-embodied-workflow-os advancement
- Project advanced from research-backed architecture plan to competitor-evaluated implementation-ready packet.
- Artifacts: competitor evaluation, source samples, P1/P2 PRD, workflow state, task candidates, benchmark scorecard.
- Boundary: planning/docs/local evidence only; no code/runtime/taskpool/hardware mutation.
- Next gate: human approval for P1 implementation or governed taskpool ingest.
