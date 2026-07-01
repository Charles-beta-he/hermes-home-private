---
name: project-portfolio-operating-system
description: "Use when governing multiple Hermes-managed projects as a portfolio: project profiles, progress ledgers, relation graph, merge/supersede decisions, reusable module extraction, portfolio doctor, and evidence-gated ratchet promotion."
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [portfolio, projects, governance, ratchet, progress-ledger, merge]
    related_skills: [product-workflow-operating-system, abstraction-governance, hermes-experience-ratchet, planning-with-files]
---

# Project Portfolio Operating System
## When to Use

- Use when the user's request explicitly matches `project-portfolio-operating-system` or this skill's documented domain.
- Use when this skill is already selected by the Hermes skill router and the task still fits the current goal.
- Don't use for: adjacent workflows with a more specific skill, generic Q&A, or tasks that lack evidence for this skill's domain.


Scope: Hermes-managed durable projects that may span sessions, repos, integrations, apps, skills, or product workflows.

Applicability: use when the user asks about multiple projects, project progress, project merge/abstraction, portfolio-wide governance, or when a project should not be treated as a one-off chat.

Anti-conditions:
- Do not use this skill for trivial one-turn tasks without durable project identity.
- Do not copy secrets, OAuth sessions, raw user data, task progress, or product facts between projects.
- Do not mark projects `validated`, `promoted`, `production-ready`, or `released` without evidence from tests, doctor output, readback, screenshots, API responses, or other proof.
- Do not modify project code through portfolio governance unless the user explicitly authorizes code changes for that project. Metadata/profile/ledger updates are separate from project implementation.

## Canonical installed surfaces

- Portfolio profile: `/Users/charles/.hermes/project-profiles/project-portfolio-os.json`
- Portfolio SSOT: `/Users/charles/.hermes/workflows/portfolio/project-portfolio-os/`
- Registry: `/Users/charles/.hermes/workflows/portfolio/project-portfolio-os/01-registry/portfolio-registry.json`
- Doctor: `/Users/charles/.hermes/workflows/portfolio/project-portfolio-os/scripts/portfolio_doctor.py`
- Strict verify: `/Users/charles/.hermes/workflows/portfolio/project-portfolio-os/scripts/portfolio_os_verify.py`
- Silent watchdog: `/Users/charles/.hermes/scripts/portfolio_os_watchdog.py`
- Latest watchdog report: `/Users/charles/.hermes/workflows/portfolio/project-portfolio-os/05-status/portfolio-doctor-latest.json`

## Core workflow

1. Read the portfolio registry and relevant project profiles first.
2. Ensure every durable project has:
   - `project_type`
   - `ssot_root`
   - `progress_ledger`
   - `relations`
   - `current_components`
   - `promotion_policy`
3. Choose the correct cross-project action:
   - full merge only when objective/capability/authority/rollback align;
   - relation-only when facts or authority differ;
   - shared module extraction when the transferable pattern can be entity-stripped;
   - supersede/archive only with successor and rollback evidence.
4. Record project uplift in the correct layer:
   - proposal/signal for ideas without proof;
   - validated-slice for verified local artifact/test/readback;
   - promoted only when the default production path is evidenced.
5. Run the doctor before and after portfolio-level changes.
6. Update the relevant progress ledger and portfolio status after material changes.

## Commands

Doctor:

```bash
python3 /Users/charles/.hermes/workflows/portfolio/project-portfolio-os/scripts/portfolio_doctor.py --json
```

Strict production verification:

```bash
python3 /Users/charles/.hermes/workflows/portfolio/project-portfolio-os/scripts/portfolio_os_verify.py
```

Silent watchdog, verbose manual mode:

```bash
python3 /Users/charles/.hermes/scripts/portfolio_os_watchdog.py --verbose
```

## Casual-chat uplift policy

Casual conversation may produce project uplift, but must land at the right level:

- understanding only: no write;
- proposal/signal: decision log, progress-ledger signal, relation note, task candidate, or experience atom;
- validated progress: only after a concrete artifact and readback/verification.

Never convert casual insight directly into implementation-complete or production-ready status.

## Work-project exclusion and vertical-to-platform promotion

When the user says certain projects are work/client projects, move them into an on-demand execution bucket: exclude them from autonomous portfolio advancement unless the user explicitly switches context or names the project. This is a metadata/execution-policy change by default, not permission to cancel tasks, mutate lifecycle, or touch project code.

When a narrow vertical project has accumulated shared platform capabilities, preserve the stable project ID but reframe the product model as a platform plus first vertical. Record the platform abstraction in the project profile/registry/ledger, keep project facts scoped, and verify with portfolio doctor/strict verify. See `references/work-project-exclusion-and-platform-promotion.md`.

## Hermes CLI / operator-surface integration

When promoting Portfolio OS beyond metadata/scripts into Hermes runtime surfaces, use `references/hermes-cli-integration-pattern.md`. Key requirements: keep commands read-only by default, use `get_hermes_home()` for profile-aware paths, add temp-home tests including a protected-project guard, verify with focused pytest and live CLI readback, and stop on tool safety-gate blocks instead of retrying or routing around them.

## Projectizing extension directions from prototypes/console surfaces

When a user references earlier expansion directions, long-term self-extension content, dashboard capability panels, or a local console/prototype folder, use `references/projectizing-extension-directions.md`. Classify each direction before writing: durable project vs shared module/capability family vs relation-only vs proposal. Create metadata/profile/ledger/registry entries only by default; do not edit the source prototype or product code. Preserve maturity truth: source-observed or dashboard-listed capabilities are not validated runtime capabilities until current tests/readback prove them.

When a user approves an external AI OS / assistant architecture signal as a durable Hermes direction, use `references/ai-os-architecture-signal-projectization.md`: create a project profile, SSOT workspace, evidence index, roadmap, default-off governance gates, task candidates, and portfolio relations; keep runtime changes, sensing, external side effects, and worker authority gated until separate implementation evidence exists.

When the next step is to advance Hermes self-extension or a control-console project beyond proposal/source-observed, use `references/self-extension-control-console-operationalization.md`. It covers mission decision-gate unblocking, stale-signal local-ledger recovery, control-console verification chains, artifact capture, maturity mapping, and portfolio writeback boundaries.

Production pitfalls from the CLI integration session:
- Read-only is not automatically safe: profile-controlled paths can still hang or exhaust memory if the command unbounded-reads a huge/special file. Require regular-file checks and byte limits before reading profile/registry/ledger paths.
- Schema checks must be fail-closed: validate field types/shapes, not only field presence. Registry `projects`/`relations` and profile `relations` must reject malformed containers and entries.
- Detect duplicate project IDs across profile files; do not let `load_profiles()` or set membership silently hide one file behind another.
- Provide JSON at the natural default operator surface too (`hermes portfolio --json`), not only nested subcommands.
- For protected projects, keep an explicit validation guard (e.g. UVISA no-code-change metadata rule) and test that missing guard fails.

## Additional reference patterns

- `references/agent-os-projectization-and-readonly-projection.md` — use when an AI OS / agent-control-plane architecture signal is approved as a durable Hermes project; land profile/SSOT/ledger/portfolio metadata plus read-only CapabilityGraph/Evidence/Context/Authority projection artifacts, then stop before runtime routing or side-effect authority without a separate gate.

## Verification checklist

- [ ] Portfolio doctor returns `ok: true`.
- [ ] Strict verify returns `ok: true`.
- [ ] Registry includes every known project profile.
- [ ] Relation targets resolve or are explicitly marked external.
- [ ] Every ledger distinguishes proposal/needs-evidence from validated/promoted.
- [ ] Any project code boundary, especially explicit no-code-change projects, is respected.
## Common Pitfalls

1. Applying this skill mechanically after the user's goal has shifted. Re-check the current request before acting.
2. Treating a plan, stale memory, or prior report as proof of completion. Verify with fresh readback.
3. Ignoring neighboring skills or narrower workflows that better match the task. Prefer the most specific applicable skill.
## Verification Checklist

- [ ] The current user request still matches this skill's trigger class.
- [ ] Required files, tools, commands, or external state were checked before action.
- [ ] Outputs, edits, or side effects were verified by readback or direct inspection.
- [ ] Boundaries, unresolved assumptions, and any deferred work were stated clearly.
