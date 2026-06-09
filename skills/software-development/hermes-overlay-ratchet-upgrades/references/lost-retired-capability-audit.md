# Lost / retired old capability audit pattern

Use this pattern when a user asks whether a Hermes private/upstream ratchet lost, retired, or rolled back old private capabilities.

## Goal

Produce an evidence-backed report, not a vague reassurance. Classify old capabilities by current availability and explain whether each was carried, absorbed, retired by design, quarantined for later ratchet, or only partially represented in registry/docs.

## Evidence sources

1. Current upgraded branch:
   - `git status --short --branch`
   - `git rev-parse HEAD origin/private/main upstream/main`
   - `git merge-base --is-ancestor upstream/main HEAD`
2. Immediate pre-ratchet backup branch/tag created before the merge.
3. Older private-line backup refs, especially if the repository had an earlier force-with-lease convergence.
4. Overlay registry and ratchet plans under `docs/private/`.
5. Stashes, but treat them as WIP evidence only; never `stash pop` during audit.
6. post-update-check and targeted test results from the upgrade.

## Comparison workflow

1. Identify refs:
   - immediate backup: e.g. `backup/private-main-pre-<date>-upstream-ratchet`
   - older private line: e.g. `origin/backup/origin-private-main-before-upstream-align-<date>`
   - current: `HEAD`
2. Compare file presence for each registered capability family:
   - `git cat-file -e OLD:path`
   - `test -e path`
3. Search current symbols rather than trusting file names:
   - helpers may have moved into upstream modular seams;
   - deleted old components may be absorbed by a new page/component with equivalent behavior.
4. Inspect stashes with `git stash show --name-status --include-untracked`, but do not apply them.
5. Build a report table with these categories:
   - newly removed or absorbed during the latest ratchet;
   - older private-line capabilities still missing/quarantined;
   - registry drift / partially declared overlays;
   - confirmed carried forward;
   - stashed WIP evidence not active in HEAD.

## Classification rules

- `carried`: current HEAD contains helper + call site + test/gate evidence.
- `absorbed`: old path disappeared, but upstream/current architecture provides equivalent behavior at a new seam.
- `retired`: old monolith or duplicate seam was intentionally not kept because upstream architecture superseded it.
- `quarantined`: old capability exists only in backup/stash/docs and needs a separate scoped ratchet.
- `partial`: registry/doc claims more files or behavior than current HEAD actually has.
- `unknown`: evidence is insufficient; stop short of deletion or retirement claims.

## Reporting expectations for this user

- User cares about “不丢功能/不降精度/纯增益”; make losses explicit even if the upgrade itself passed.
- Separate backend capability loss from UX shortcut loss. Example: a deleted desktop cron dropdown may not lose cron backend actions if full cron detail still exposes pause/resume/run/edit/delete, but compact-sidebar convenience may have regressed.
- Call out optional-import fail-open cases. If current tools optional-import an old guard module and the module is missing, say that the extra guard is inactive even if the broader tool still works.
- Do not claim full multi-model certification when consult status is degraded; use local evidence and gates precisely.
- Land the report under `docs/private/` and commit/push if operating in the Hermes private repo where scoped commits are allowed.

## Recommended report filename

`docs/private/lost-retired-old-capabilities-report-YYYYMMDD.md`

## Common high-risk old capability families

- norm governance / durable write guards;
- taskpool validation/security gates;
- browser replay evidence;
- post-chat reflection and run-envelope ledgers;
- MCP semantic probes;
- registry entries whose helper file exists but standalone retrieval/tool/test surfaces are absent.
