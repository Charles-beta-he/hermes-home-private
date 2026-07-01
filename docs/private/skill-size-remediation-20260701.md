# Hermes skill size remediation

Date: 2026-07-01
Trigger: user approved continuing execution after skill invocation taxonomy auditor reported `skill_too_large` errors.

## Objective

Reduce hard `skill_too_large` findings without deleting workflow knowledge or changing runtime/external side-effect gates.

## Constraints

- Local file edits only.
- No external installs, credentials, network side effects, or taskpool force-close.
- Preserve extracted content under `references/` next to its source skill.
- Keep root `SKILL.md` as routing/control-plane entry contract with pointers to detailed references.

## Actions

### 1. taskpool-control-plane

Source:
`/Users/charles/.hermes/skills/software-development/taskpool-control-plane/SKILL.md`

Extracted section:
`## Blocked-Task Resolution Workflow`

New reference:
`/Users/charles/.hermes/skills/software-development/taskpool-control-plane/references/blocked-task-resolution-workflow.md`

Result:
- before: 101080 chars
- after: 99532 chars
- hard `skill_too_large`: cleared
- root now points to the reference and preserves anti-condition.

### 2. pytorch-fsdp

Source:
`/Users/charles/.hermes/skills/mlops/training/pytorch-fsdp/SKILL.md`

Extracted section:
`## Quick Reference`

New reference:
`/Users/charles/.hermes/skills/mlops/training/pytorch-fsdp/references/quick-reference-patterns.md`

Result:
- before: 160144 chars
- after: 3750 chars
- hard `skill_too_large`: cleared
- root now keeps routing, setup notes, and pointer to generated docs.

### 3. research/last30days

Source:
`/Users/charles/.hermes/skills/research/last30days/SKILL.md`

Extracted section range:
`## FIRST: Internalize the Research` through pre-`## Security & Permissions`

New reference:
`/Users/charles/.hermes/skills/research/last30days/references/synthesis-and-presentation-contract.md`

Result:
- before: 131912 chars
- after: 98232 chars
- hard `skill_too_large`: cleared
- root keeps minimum synthesis rule and pointer to detailed presentation contract.

### 4. archived research-paper-writing copy A

Source:
`/Users/charles/.hermes/skills/.archive/curator-umbrella-2026-06-10/research/research-paper-writing/SKILL.md`

Extracted section range:
`## Phase 5: Paper Drafting` through pre-`## Common Pitfalls`

New reference:
`/Users/charles/.hermes/skills/.archive/curator-umbrella-2026-06-10/research/research-paper-writing/references/paper-drafting-submission-and-deliverables.md`

Result:
- before: 103841 chars
- after: 34636 chars
- hard `skill_too_large`: cleared

### 5. archived research-paper-writing copy B

Source:
`/Users/charles/.hermes/skills/.archive/curator-umbrella-2026-06-17/research/references/absorbed/research-paper-writing/SKILL.md`

Extracted section range:
`## Phase 5: Paper Drafting` through pre-`## Common Pitfalls`

New reference:
`/Users/charles/.hermes/skills/.archive/curator-umbrella-2026-06-17/research/references/absorbed/research-paper-writing/references/paper-drafting-submission-and-deliverables.md`

Result:
- before: 103841 chars
- after: 34636 chars
- hard `skill_too_large`: cleared

## Verification

Commands run:

```bash
python3 /Users/charles/.hermes/scripts/skill_invocation_taxonomy_auditor.py --selftest --pretty
python3 /Users/charles/.hermes/scripts/skill_invocation_taxonomy_auditor.py --write-report --pretty
```

Latest report:
`/Users/charles/.hermes/docs/private/skill-invocation-taxonomy/latest.md`
`/Users/charles/.hermes/docs/private/skill-invocation-taxonomy/latest.json`

Readback summary:

```json
{
  "ok": true,
  "total": 266,
  "severity": {"warn": 287},
  "skill_too_large_count": 0,
  "core_body_large_count": 41
}
```

## Remaining non-blocking debt

- 41 `core_body_large` warnings remain; these are advisory size warnings, not hard loader-limit errors.
- `taskpool-control-plane` and `last30days` remain close to 100k and should receive further staged slimming later.
- Some roots still miss standardized sections (`Common Pitfalls`, `Verification Checklist`, anti-conditions). These are warnings, not hard size errors.

## Boundary

No skill content was intentionally discarded. Detailed sections were moved to adjacent `references/` files with provenance headers. No runtime config, external service, credentials, or taskpool force-close was performed.
