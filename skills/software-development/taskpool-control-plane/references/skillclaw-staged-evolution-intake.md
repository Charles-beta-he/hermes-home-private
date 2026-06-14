# SkillClaw-style staged skill evolution intake

Use this reference when a user shares SkillClaw, MetaClaw, OpenClaw/Garden-style skill evolution repos, or asks whether a minimal skill-evolution loop will later become a full landing.

## Core interpretation

Treat SkillClaw-like projects as **post-session skill evolution architecture**, not as a request to install a proxy or let an external system become the Hermes skill SSOT.

The useful pattern is:

```text
session/task proof -> skill candidate -> staged artifact -> deterministic validation -> human/skill_manage apply -> read-back/proof-check
```

Do not jump directly to:

```text
skillclaw setup/start -> rewrite ~/.hermes/config.yaml -> route Hermes traffic through proxy -> cloud/shared storage
```

That path touches config, auth, session capture, private skill data, and possibly cloud storage; it requires explicit human authorization and a rollback packet.

## Intake sequence

1. Inspect the live repo first.
   - Confirm repo URL, license, default branch, stars/forks/update state, and commit SHA.
   - Read README architecture sections, package manifest, CLI entrypoints, config adapter code, session summarizer/aggregator/verifier pipeline, and tests.
2. Write a private gap-analysis artifact under `docs/private/`.
   Include source identity, inspected commit, evidence files, capability mapping, Hermes landing zones, risks/red lines, and smallest next slice.
3. Add a rich taskpool task rather than a vague repo-summary task.
   - `lane=evolution`
   - `project=hermes-agent`
   - `architecture_target=skill-graph` for skill lifecycle/dedup/verification/sharing work.
   - Use `local-brain` only when the dominant work is transcript/proof storage or taskpool runtime.
4. If the user approves and asks whether it will continue upgrading, create follow-through tasks immediately:
   - minimal Hermes-native staging harness;
   - full landing roadmap / permission matrix.
5. Run `proof-check`/`selfcheck` when available and report the real event-hook outcome. If the hook auto-claims/runs a task, name that explicitly instead of creating duplicate work.

## Recommended task decomposition

### Task A — Source review / gap map

Goal: turn the external repo into a grounded Hermes evolution task.

Acceptance evidence:
- gap-analysis document;
- source inventory and commit SHA;
- capability mapping;
- security/privacy boundary;
- smallest verifiable local slice.

### Task B — Hermes-native minimal staging harness

Goal: implement the safe first loop without proxy/config/cloud side effects.

Acceptance evidence:
- staging artifact schema;
- candidate generation command/script;
- deterministic checks for frontmatter, trigger breadth, evidence refs, linked files, and rollback;
- dry-run against one real local transcript/task proof bundle;
- no direct writes to formal skills.

### Task C — Full landing roadmap

Goal: answer “will this upgrade later / can it fully land?” with executable phases.

Required phases:
1. record-only evidence capture;
2. staged candidate queue;
3. human-approved `skill_manage` apply;
4. limited auto-apply for low-risk patches;
5. profile/device federation;
6. optional external SkillClaw adapter behind explicit config/cloud authorization.

## Red lines

- Do not run `skillclaw setup` or `skillclaw start` during intake.
- Do not rewrite `~/.hermes/config.yaml` or any other profile config without explicit authorization and backup/restore proof.
- Do not upload private Hermes skills, transcripts, taskpool notes, or session logs to OSS/S3/Nacos/cloud services during intake.
- Do not make SkillClaw or any external store a parallel SSOT for Hermes skills.
- Do not let an LLM verifier be the sole publish authority; deterministic checks and human/skill_manage gates remain required.
- Do not directly apply generated skill patches; write staged artifacts first.

## Full landing semantics

“Full landing” for this class means a governed Hermes-native pipeline, not immediate full automation:

```text
UI/CLI entry -> candidate SSOT -> validation ledger -> controlled executor -> skill_manage apply -> read-back -> proof-check/selfcheck -> dashboard/taskpool visibility -> commit/rollback
```

Escalate authority layer-by-layer. Stop at the first boundary that needs human permission: config mutation, proxy traffic routing, cloud/shared storage, cross-profile writes, deleting/merging skills, or automatic publication.

## Pitfalls

1. Treating a repo that claims Hermes support as safe to install. Support claims are not an authorization to mutate this user's Hermes config.
2. Confusing source-review completion with implementation completion. A gap doc means intake is done; it does not prove a staging harness exists.
3. Creating a new narrow “SkillClaw” skill too early. Prefer updating taskpool/skill-graph governance references until a recurring class-level workflow is proven.
4. Omitting follow-through tasks after user approval. If the user says “认可” and asks about full landing, create the minimal-loop and full-roadmap tasks immediately.
5. Letting “collective evolution” upload raw private sessions. Use local proof summaries and staged candidates unless explicit sharing approval exists.
