# Proposal: stage SkillClaw-derived skill evolution guidance for taskpool-control-plane

## Patch intent

Patch the existing `taskpool-control-plane` skill (not a new skill) to keep SkillClaw-like work inside Hermes-native staged candidate flow:

- add a narrow reference entry pointing to `references/skillclaw-staged-evolution-intake.md`;
- trigger only for SkillClaw / OpenClaw / Garden-style skill evolution repo intake or follow-through tasks;
- keep the safe sequence: local proof bundle -> skill candidate -> staged artifact -> deterministic validation -> human/skill_manage apply -> read-back/proof-check;
- explicitly preserve red lines: no `skillclaw setup/start`, no `~/.hermes/config.yaml` rewrite, no proxy/cloud upload, no parallel skill SSOT, no auto-publication.

## Evidence references

- `/Users/charles/.hermes/docs/private/skillclaw-intake-gap-analysis-2026-06-10.md` records inspected repo identity, commit `bf4dc2ee9430ecffb60e19630d26f57dfa2bd326`, capability mapping, and smallest verifiable next slice.
- `/Users/charles/.hermes/skills/software-development/taskpool-control-plane/references/skillclaw-staged-evolution-intake.md` records the class-level intake and red-line policy.
- `/Users/charles/.hermes/scripts/skill_candidate_staging.py` is the local deterministic harness produced for the minimal loop.
- `/Users/charles/.hermes/scripts/test_skill_candidate_staging.py` provides focused regression coverage.

## Acceptance check for later apply

After human/skill_manage review, any real skill patch must prove:

1. read-back of the updated skill entry;
2. no direct mutation outside the active profile skill path;
3. deterministic proof-check or equivalent selfcheck still passes;
4. candidate artifact remains linked to the stage report.

## Rollback

Rollback by discarding the staged candidate artifact and not applying the proposed skill patch. If a later human-approved patch is applied and fails proof-check, revert only the narrow skill entry/reference addition and preserve this proposal as negative evidence.
