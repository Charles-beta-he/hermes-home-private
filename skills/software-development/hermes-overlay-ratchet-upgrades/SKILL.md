---
name: hermes-overlay-ratchet-upgrades
description: "Use when operate a locally customized Hermes checkout that tracks upstream while preserving local enhancements through overlay manifests, drift detection, and multi-model certification."
references:
  - references/overlay-registry-governance.md
triggers:
  - Hermes local checkout has many uncommitted or untracked enhancements
  - User asks whether local behavior matches upstream
  - hermes update may overwrite vendor patches
  - Need a ratchet-style upgrade path combining upstream changes with local overlays
  - Need to certify whether a capability is helper-landed vs mainline-integrated
  - Need to distribute or migrate users onto a private/custom Hermes branch without exposing git complexity
---

# Hermes Overlay Ratchet Upgrades

## Overview

Operate a locally customized Hermes checkout that tracks upstream while preserving local enhancements through overlay manifests, drift detection, and multi-model certification. It is organized as an evidence-grounded review gate: separate findings from preferences, cite the inspected artifact or state, and keep adjacent workflows out of scope.

## When to Use

Use this skill when the request matches the `hermes-overlay-ratchet-upgrades` trigger and the domain-specific boundaries in this skill apply.

Do not use it for:
- generic one-off questions that do not need this workflow;
- neighboring specialist workflows with a narrower matching skill;
- durable memory or project-profile writes unless this skill explicitly governs that landing zone.

Use this when Hermes is running from a local source checkout plus editable install, especially when local enhancements live in run_agent.py, agent/, or tools/ and may drift from upstream.


- Don't use for: tasks outside this skill's trigger class, requests with a more specific neighboring skill, or situations where required evidence/tooling is unavailable.
## Source-State and Snapshot Drift

This skill also absorbs the former `git-state-aware-debugging` workflow as a support pattern for overlay work. Before blaming dependencies, upstream, or runtime routing, prove which source snapshot the failing consumer is reading:

1. Compare `HEAD`, staged index, and worktree for suspect files (`git status --short`, `git show :path`, direct file read, and `git show HEAD:path`).
2. Treat staged/unstaged divergence on the same file as a first-class bug source, especially when automation consumes generated patches, staged snapshots, or review bundles.
3. Fix the layer the consumer actually reads, then re-stage or discard drift intentionally.
4. Load `references/git-state-aware-debugging.md` for the archived detailed checklist and Hermes run-agent ordering example.

## Core model

Treat the system as four layers:

1. Upstream baseline: clean origin/main behavior.
2. Local overlays: explicit local enhancements with bounded touchpoints.
3. Replay/governance: scripts that detect drift and re-apply or reject overlays.
4. Certification: multi-model evidence deciding absorb / keep / redesign.

The goal is not “preserve every patch forever”. The goal is a ratchet:
- if upstream absorbed the capability, retire the overlay;
- if not, replay it in a controlled, tested way;
- never leave unexplained runtime drift.

## Procedure

1. Identify the real runtime first.
   - Check which hermes executable is used.
   - Check the shebang and venv Python.
   - Confirm whether runtime imports come from ~/.hermes/hermes-agent editable source or from a packaged install.
   - Compare the Hermes venv package versions, not just system python3.

2. Separate package-version issues from source-drift issues.
   - Inspect pyproject.toml, lockfile, and installed versions in the Hermes venv.
   - A system Python mismatch is usually irrelevant if CLI runs from Hermes venv.
   - If a behavior comes from untracked or modified source files, classify it as overlay drift, not dependency drift.

3. Compare local vs upstream before diagnosing behavior.
   - git status --short --branch
   - git rev-parse HEAD and origin/main
   - grep upstream for the suspect symbol or file
   - If upstream lacks the file or import, the behavior is local-only by definition.

4. Classify each enhancement.
   - Helper-landed: helper module exists locally.
   - Mainline-integrated: mainline call sites actually invoke it.
   - Default-off experimental: config flags exist but are off.
   - Certified: helper + mainline + tests + verification evidence.

5. For Hermes/OpenClaw-style enhancements, audit these seams explicitly.
   - helper module exists (agent/openclaw_control_plane.py etc.)
   - config keys exist in ~/.hermes/config.yaml
   - mainline call sites invoke the helper (run_agent.py, prompt_builder.py, tools/memory_tool.py, routers)
   - tests cover helper behavior and integration behavior separately

6. Run upgrade hygiene gates before any upstream sync.
   - git diff --check
   - local self-check scripts such as ~/.hermes/scripts/hermes-pre-update-verify.sh
   - post-update drift detection such as ~/.hermes/scripts/post-update-check.py
   - Fail closed on dirty formatting, syntax, or broken patch targets.

7. Build an overlay registry.
   For each local enhancement record:
   - id
   - purpose
   - touched files
   - default mode (on/off)
   - tests
   - replay strategy
   - absorb-when condition
   - rollback strategy

8. Use multi-model certification only for hard judgments.
   Recommended split:
   - Codex/GPT: mechanical diff and impact map
   - Claude: architecture judgment (absorbed vs keep vs redesign)
   - MiMo/DeepSeek: low-cost adversarial review for missed breakpoints
   - Final truth gate: accept only with evidence bundle

9. For risky mainline seams, ratchet in two steps instead of one.
   - First certify a review package only: seam location, claim/evidence links, rollout bounds, and non-goals.
   - Keep that certification explicitly no-action; do not bundle immediate implementation authorization into the same packet.
   - Then land the code via TDD under a top-level kill switch, default-off, advisory-only, and fail-soft behavior.
   - For Hermes turn orchestration, the right kind of v1 landing is: execute once per turn at the certified seam, stash runtime state only, and avoid forced provider/model/tool/memory side effects.

## Pitfalls

- Do not mistake system python3 package versions for Hermes runtime versions.
- Do not attribute local-only behavior to upstream without grepping origin/main first.
- pyproject.toml and lockfile may drift together upstream; that is repo-governance debt, not automatically the runtime root cause.
- A helper file existing locally does not mean the capability is fully landed. Verify call sites.
- Experimental config keys being present does not prove the feature is active.
- Do not update Hermes on a dirty tree; git diff --check failures are real blockers, not cosmetic noise.
- Do not `git stash pop` an update-created autostash just because it exists. First classify it as audit material vs truly replay-worthy overlay.
- Do not trust replay helper scripts blindly. If a regex-driven patch helper re-applies a drift, inspect the diff immediately and verify syntax; preserve the architectural intent, not the broken textual transform.
- If hook-registry selfcheck fails because a shell hook sits outside the allowlist, fix the trust boundary by moving/mirroring the hook into `~/.hermes/scripts/` or `~/.hermes/agent-hooks/` and updating config references. Do not weaken the allowlist check.
- Do not mix review-package ratification with implementation authorization in the same certification packet. That ambiguity commonly causes noop-vs-change truth-gate failures.
- For first mainline landing of a local cognition/control-plane overlay, do not start by wiring downstream consumers. First land the seam itself behind default-off + env kill switch, verify disabled/enabled/fail-soft behavior, then expand consumers in later steps.

## Replay pattern after `hermes update`

When `HEAD` already matches `origin/main` and an auto-created stash remains:

1. Inspect the stash before replaying anything.
   - Compare stash file list against current worktree diff.
   - Keep the small set of overlays still live in worktree separate from the much larger stash snapshot created on the old baseline.
2. Use `post-update-check.py` to decide what actually needs replay.
   - Prefer replaying only the specific drifts the checker surfaces.
   - Treat checker-green tracked overlays as already landed locally.
3. Re-apply drift fixes narrowly, then verify with the Hermes venv.
   - Use `./venv/bin/python -m py_compile ...` rather than an arbitrary system python.
   - Run targeted pytest slices for the touched surfaces.
4. If profile-mirrored config exists, update it too.
   - Otherwise the next export/restore can resurrect a path or policy drift you already fixed.

See `references/post-update-ratchet-replay-pattern.md` for a concrete session pattern covering autostash triage, MCP timeout replay, and hook allowlist remediation.

## Full upstream merge ratchet pattern

When `private/main` must absorb a large `upstream/main` rather than just replay a small post-update drift:

1. Protect the private line before merging.
   - Commit or intentionally ignore private evidence files.
   - Create a backup branch and backup tag at the pre-merge private HEAD.
   - Push `private/main`, the backup branch, and the backup tag before resolving conflicts.
2. Prefer upstream architecture as the base when upstream split or modularized the conflicted surface.
   - Replay private behavior into the new seam instead of preserving the old monolith.
   - Example class: turn-loop overlays may move from `conversation_loop.py` into an upstream `turn_finalizer.py` seam.
3. Distinguish text resolution from index resolution.
   - No conflict markers does not mean git considers the path resolved; run `git diff --name-only --diff-filter=U` and `git add` resolved paths.
4. Run `post-update-check.py --fix` after targeted tests, not only before them.
   - The checker can catch missing importable seam helpers that are default-off at runtime but required by overlay governance tests.
5. If external multi-model consult stalls, continue with evidence-first local certification.
   - Do not fabricate model consensus.
   - Produce a carry / absorb / retire table from inspected diffs, conflict decisions, tests, and post-update-check output.
   - If the consult returns later, read its certification status precisely and patch the ratchet report instead of overwriting the verified engineering result. A grounded truth gate with `degraded_not_certified` still means “facts corroborated, quorum not complete,” not full multi-model certification.
6. Before declaring the upgrade complete, re-check that `upstream/main` has not advanced during the work.
   - Run a fresh fetch, compare `upstream/main`, and verify `git merge-base --is-ancestor upstream/main HEAD`.
   - If upstream advanced, create a new backup branch/tag at the just-verified private HEAD, merge the new upstream tip, rerun the same gates, and push again.
7. Treat hook-side self-check failures as advisory until rerun under the Hermes venv.
   - Upstream merge hooks may invoke system `python3`; if that fails on modern syntax (for example `str | None`), immediately rerun `./venv/bin/python ~/.hermes/scripts/post-update-check.py --fix` before classifying the merge as broken.

See `references/full-upstream-merge-ratchet-20260609.md` for a concrete full-merge case including auto-relay, conductor runtime, memory provider rollback, CLI modularization decisions, late degraded multi-model consult handling, and post-completion upstream advancement.

## Private/custom branch distribution UX

When designing distribution for a private or locally customized Hermes line, make the user contract one recommended bootstrap command and `hermes update`; hide repo URL, branch, upstream, venv, and migration details inside the installer. Prefer a GitHub-CLI bootstrap that first prints the recommended path, verifies private-repo access, clones or refreshes the private checkout, then delegates to a repo-local finalizer. The finalizer should write install metadata (channel/origin/upstream/branch) so `hermes update` defaults to the private branch rather than falling back to `main`, and official-to-private migrations should preserve `~/.hermes` user data while only replacing the code checkout. See `references/private-repo-distribution-ux.md` for the detailed end-user UX, bootstrap/finalizer split, error-message taxonomy, migration flow, and tradeoffs.

## Lost / retired capability audit after an upgrade

When the user asks for missing, lost, retired, or rolled-back old capabilities after a ratchet upgrade, do a separate evidence audit rather than only restating that tests passed:

1. Compare current `HEAD` against the immediate pre-ratchet backup and any older private-line backup refs.
2. Inspect overlay registry/plans and stashes as evidence, but do not apply stashes during the audit.
3. Classify each capability as carried, absorbed, retired, quarantined, partial, or unknown.
4. Explicitly call out optional-import fail-open cases and UX shortcut regressions separately from backend capability loss.
5. Write a durable report under `docs/private/lost-retired-old-capabilities-report-YYYYMMDD.md` and commit it when operating in the Hermes private repo.

See `references/lost-retired-capability-audit.md` for the detailed workflow and report expectations.

## Verification checklist

- Runtime path confirmed (which hermes, shebang, venv Python)
- Hermes venv package versions captured
- Local-vs-upstream symbol/file comparison done
- Overlay status classified: absorbed / local-only / partial / certified
- Hygiene gates pass before update
- Post-update replay or retirement decision documented
- Integration tests exist for any mainline-connected enhancement
- [ ] Reviewer calibration: findings include a severity or rubric boundary and cite evidence.
## References

- See references/local-overlay-drift-and-ratchet.md for a concrete Hermes case covering Codex circuit-breaker drift, venv-vs-system version checks, and partial OpenClaw landing signals.
- See references/mainline-review-package-then-guarded-landing.md for the pattern of certifying a risky mainline seam as a no-action review package first, then landing it with default-off, advisory-only, fail-soft wiring.
## Common Pitfalls

1. Applying this skill mechanically after the user's goal has shifted. Re-check the current request before acting.
2. Treating a plan, stale memory, or prior report as proof of completion. Verify with fresh readback.
3. Ignoring neighboring skills or narrower workflows that better match the task. Prefer the most specific applicable skill.
## Verification Checklist

- [ ] The current user request still matches this skill's trigger class.
- [ ] Required files, tools, commands, or external state were checked before action.
- [ ] Outputs, edits, or side effects were verified by readback or direct inspection.
- [ ] Boundaries, unresolved assumptions, and any deferred work were stated clearly.
