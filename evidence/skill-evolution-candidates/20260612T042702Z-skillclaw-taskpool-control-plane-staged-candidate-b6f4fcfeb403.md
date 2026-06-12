# Skill candidate staging: skillclaw-taskpool-control-plane-staged-candidate

- candidate_id: `20260612T042702Z-skillclaw-taskpool-control-plane-staged-candidate-b6f4fcfeb403`
- status: `staged`
- source_skill: `/Users/charles/.hermes/skills/software-development/taskpool-control-plane/SKILL.md` sha256=386e06e754483d0983462e49328a7d5b02de35efcac74b7b6ec4768705457c7a
- proposal: `/Users/charles/.hermes/evidence/skill-evolution-candidates/skillclaw-taskpool-control-plane-proposal-20260612.md` sha256=bb472c23c2678e6139e5d46791550caa0166b10fe76eeba710d47858691c568f

## Deterministic checks
- [x] existing_skill_exists: /Users/charles/.hermes/skills/software-development/taskpool-control-plane/SKILL.md
- [x] skill_has_frontmatter: frontmatter keys: description,name
- [x] skill_has_name_or_description: requires reusable skill identity
- [x] evidence_paths_exist: missing=[]
- [x] proposal_references_evidence: matched=["/Users/charles/.hermes/docs/private/skillclaw-intake-gap-analysis-2026-06-10.md", "/Users/charles/.hermes/skills/software-development/taskpool-control-plane/references/skillclaw-staged-evolution-intake.md", "/Users/charles/.hermes/scripts/skill_candidate_staging.py", "/Users/charles/.hermes/scripts/test_skill_candidate_staging.py"]
- [x] proposal_has_rollback: proposal must describe rollback/revert path
- [x] proposal_has_patch_intent: proposal must be an actionable skill patch candidate
- [x] trigger_breadth_limited: broad_hits=[]
- [x] output_not_formal_skill_store: /Users/charles/.hermes/evidence/skill-evolution-candidates

## Evidence
- `/Users/charles/.hermes/docs/private/skillclaw-intake-gap-analysis-2026-06-10.md` sha256=a3dcb5ca86eec84d3e6a7a9c6f588dcd5f185367f56ee4154e7a803a17ab2489
- `/Users/charles/.hermes/skills/software-development/taskpool-control-plane/references/skillclaw-staged-evolution-intake.md` sha256=b7e7bc7fe63c6f9924c94487d6406fdbd597a55fb8cb7f0c729448a110698811
- `/Users/charles/.hermes/scripts/skill_candidate_staging.py` sha256=bfbce12d6e12abe920c462d9448955e276502719b3d118c1223d6b936e489853
- `/Users/charles/.hermes/scripts/test_skill_candidate_staging.py` sha256=c1f0dfc16eada26f9f9549f19c167901ae49dcc235f8b9956dfea840413e479f

## Governance
No direct skill write was performed. Apply requires human review or `skill_manage`-equivalent controlled executor with read-back/proof-check.
Blocked side effects: config rewrite, proxy start, cloud upload, cross-profile write, auto-publish.

## Proposal body

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

