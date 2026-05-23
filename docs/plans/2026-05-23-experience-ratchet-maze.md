# Experience Ratchet Maze Implementation Plan

> **For Hermes:** Use subagent-driven-development skill only after this external MVP is validated. Keep Hermes core default-off.

**Goal:** Land a maintainable dev-brain external overlay for cross-project experience capture, validation, promotion proposals, and rollback.

**Architecture:** `~/.hermes/scripts/experience-ratchet-maze.py` owns the external CLI/state machine. `~/.hermes/experience-ratchet/` owns runtime atoms/proposals/logs. `~/.hermes/skills/autonomous-ai-agents/hermes-experience-ratchet/` documents operation. Hermes core remains untouched; future core integration consumes proposal artifacts only.

**Tech Stack:** Python stdlib, JSON files, Hermes skills, git-scoped personal Hermes repo commits.

---

## Decisions

- External overlay first, no Hermes core mutation.
- Proposal-only landing zones: skill, memory, profile, taskpool, project_doc, public_consensus, noop.
- Promotion requires evidence and falsifier; deprecate/rollback/revoke requires reason.
- Multi-model output is dissent/analysis evidence, not truth.

## Files

- `/Users/charles/.hermes/scripts/experience-ratchet-maze.py`
- `/Users/charles/.hermes/skills/autonomous-ai-agents/hermes-experience-ratchet/SKILL.md`
- `/Users/charles/.hermes/docs/plans/2026-05-23-experience-ratchet-maze.md`
- Runtime after init: `/Users/charles/.hermes/experience-ratchet/`

## Tasks

- [x] Task 1: Run real multi-model review and preserve dissent — artifact: `/Users/charles/.hermes/tick-20260523-070206-792848-p71653-3568104d-691af86b`
- [x] Task 2: Choose maintainable boundary — external dev-brain overlay, no core mutation
- [x] Task 3: Create CLI/store/state-machine MVP
- [x] Task 4: Create operating skill
- [x] Task 5: Initialize store and run smoke test — smoke home `/tmp/experience-ratchet-smoke.8DxbrS`, default atom `hermes-dev-brain-d6e518cb233e`
- [x] Task 6: Validate files and commit scoped changes in `/Users/charles/.hermes` — validation passed; scoped git commit planned next

## Smoke Test Commands

```bash
python3 -m py_compile ~/.hermes/scripts/experience-ratchet-maze.py
python3 ~/.hermes/scripts/experience-ratchet-maze.py init
atom_id=$(python3 ~/.hermes/scripts/experience-ratchet-maze.py new --project hermes-dev --claim 'Experience ratchet overlay must remain proposal-only until promoted artifacts are independently verified.' --pattern-type architecture --landing-zone public_consensus --tag hermes --applies 'cross-project experience promotion' --anti 'single-session WIP' --falsifier 'if proposal artifacts directly mutate memory/skills/profiles/taskpool, overlay boundary is violated' --evidence 'command:consult_models T1 2026-05-23 weak consensus' | python3 -c 'import sys,json; print(json.load(sys.stdin)["atom_id"])')
python3 ~/.hermes/scripts/experience-ratchet-maze.py transition "$atom_id" normalized --reason 'schema smoke normalized'
python3 ~/.hermes/scripts/experience-ratchet-maze.py transition "$atom_id" validated --evidence 'command:py_compile+init+validate smoke pass'
python3 ~/.hermes/scripts/experience-ratchet-maze.py propose "$atom_id"
python3 ~/.hermes/scripts/experience-ratchet-maze.py validate
```

## Resume Protocol

1. Read this plan.
2. Run `git -C ~/.hermes status --short -- scripts/experience-ratchet-maze.py skills/autonomous-ai-agents/hermes-experience-ratchet docs/plans/2026-05-23-experience-ratchet-maze.md`.
3. Continue from the first unchecked task.
4. Do not touch unrelated dirty files in `/Users/charles/.hermes`.
