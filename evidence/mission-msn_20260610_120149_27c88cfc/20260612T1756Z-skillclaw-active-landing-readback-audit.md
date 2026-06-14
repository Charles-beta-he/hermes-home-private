# SkillClaw active landing read-back audit — 2026-06-12T17:56 +08:00

Scope: one bounded local-only mission slice after taskpool_status_changed signal. No push/deploy/secrets/external sends/destructive deletes. This slice did not mutate the active skill store; it read back the active taskpool-control-plane skill, reran staged-candidate proof/read-back checks, and ran focused harness tests.

## Commands and observed evidence

```bash
python3 ~/.hermes/scripts/brain_task_orchestrator.py selfcheck --json
```

Observed: `status=PASS`, `task_count=323`, `invalid_count=0`; boundary reported `debt_invalid_count=67` as terminal/unrelated backlog debt, not active fail-closed invalids. Warnings remained for one stale local edge node heartbeat / dangerous capability policy.

```bash
rg -n "SkillClaw|skillclaw|staged-evolution" /Users/charles/.hermes/skills/software-development/taskpool-control-plane
```

Observed active read-back:

- `/Users/charles/.hermes/skills/software-development/taskpool-control-plane/SKILL.md:241` contains the SkillClaw/MetaClaw staged-evolution entry pointing to `references/skillclaw-staged-evolution-intake.md`.
- `/Users/charles/.hermes/skills/software-development/taskpool-control-plane/references/skillclaw-staged-evolution-intake.md` exists and describes the SkillClaw-style staged intake policy.

```bash
python3 ~/.hermes/scripts/skill_candidate_staging.py proof-check \
  --candidate /Users/charles/.hermes/evidence/skill-evolution-candidates/20260612T050459Z-skillclaw-taskpool-control-plane-staged-candidate-b6f4fcfeb403.json
```

Observed: `status=proof_failed`, `ok=false`; only failing deterministic check was `source_skill_sha256_matches` because the staged candidate expected source skill hash `c2300d999827408deec7e77871436beb1356fedc5d50b2d29f2716f8bd4aee72` but active skill now hashes to `fbb58a536408610e6d4eb80592f03e94bf382fdb86c4a49bc918ddfdad91f116`. Proposal and evidence hashes still matched.

Interpretation: the staged candidate is no longer a green pre-apply artifact after the active skill changed. The active landing appears present by read-back, but the existing staged-candidate proof gate correctly goes red on source-hash drift. Do not treat this candidate proof-check as green unless either (a) a post-apply closure artifact is created, or (b) a new candidate is restaged from the current active source hash.

```bash
python3 ~/.hermes/scripts/skill_candidate_staging.py read-back \
  --candidate /Users/charles/.hermes/evidence/skill-evolution-candidates/20260612T050459Z-skillclaw-taskpool-control-plane-staged-candidate-b6f4fcfeb403.json
python3 -m pytest /Users/charles/.hermes/scripts/test_skill_candidate_staging.py -q
```

Observed: read-back returned `ok=false` for the same source-skill hash mismatch; focused tests passed: `5 passed in 0.21s`.

```bash
git -C /Users/charles/.hermes status --short -- \
  /Users/charles/.hermes/skills/software-development/taskpool-control-plane/SKILL.md \
  /Users/charles/.hermes/skills/software-development/taskpool-control-plane/references/skillclaw-staged-evolution-intake.md \
  /Users/charles/.hermes/scripts/skill_candidate_staging.py \
  /Users/charles/.hermes/scripts/test_skill_candidate_staging.py
```

Observed: active skill landing is still local/uncommitted in the private overlay:

```text
 M skills/software-development/taskpool-control-plane/SKILL.md
?? skills/software-development/taskpool-control-plane/references/skillclaw-staged-evolution-intake.md
```

## Result

Completed this bounded audit slice:

- verified active SkillClaw entry/reference are present;
- verified staging harness tests still pass;
- found a real post-apply evidence gap: the old staged candidate proof-check now fails by design because the active skill hash changed;
- preserved the failure as negative evidence rather than silently declaring the old candidate green.

## Risk / blocker

Risk: lifecycle/dashboard synchronization must not use the old staged candidate proof-check as green after active landing. A narrow local fix is needed to create a post-apply closure proof (or restage from current active hash) before closing this evolution loop.

## Next bounded step

Create a post-apply closure artifact or restaged candidate against active hash `fbb58a536408610e6d4eb80592f03e94bf382fdb86c4a49bc918ddfdad91f116`, then rerun read-back/proof-check/selfcheck. No push/deploy/secrets/external sends.
