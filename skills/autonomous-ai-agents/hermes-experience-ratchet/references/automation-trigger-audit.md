# Experience ratchet automation trigger audit

Scope: class-level checks for whether a dev-brain experience-ratchet overlay is actually connected to automated capture, validation, promotion, and skill-staging signals.

Applicability: use when a user asks whether project-level lessons, repeated incidents, or cross-project compatibility patterns are being automatically checked or promoted into skills.

Anti-conditions: do not use this as authority to auto-mutate memory, skills, project profiles, taskpool cards, external systems, or Hermes core. Do not treat session summaries as ExperienceAtoms unless a separate capture/proposal artifact exists.

## Audit chain

1. Atom store health
   - Run the overlay validator.
   - Evidence: validator exit code plus checked/ok counts.
   - Limitation: this proves existing atoms are structurally valid; it does not prove new lessons are being captured.

2. Session/project summary source
   - Check whether session-end or project-closeout summarizers create reusable context cards, notes, or evidence packets.
   - Limitation: summaries are source material, not ratchet atoms.

3. Ratchet capture path
   - Check whether an explicit capture step creates ExperienceAtom drafts from repeated lessons, user corrections, project closeouts, or high-risk incidents.
   - Required fields before promotion: scope, applicability, anti-conditions, falsifier, landing zone, evidence refs.

4. Backlog and drift watcher
   - A safe watcher should be no-agent, local-only, success-silent, and proposal-only.
   - Track at least old captured atoms, old normalized atoms, old promoted candidates, landing_zone=skill accumulation, validation failures, and contradictions needing relation edges.
   - Output only local repair/proposal packets unless exact authority exists.

5. Selfcheck coverage registration
   - Check whether the ratchet overlay itself is represented in the broader dynamic selfcheck/coverage registry.
   - Missing coverage should generate a proposal for a local-read watchdog rather than directly installing broad automation.

6. Skill candidate staging
   - Promotion into formal skills should pass through a staging artifact containing the existing skill, evidence refs, proposed patch intent, rollback path, and readback/proof-check.
   - The staging gate must not write directly to formal skills.

## Safe default automation design

- no_agent: true
- deliver: local
- side effects: local_read or proposal_file_write only
- success behavior: silent
- failure behavior: emit compact JSON with evidence paths and blocked authorities
- forbidden without explicit authority: direct skill mutation, memory write, profile write, taskpool lifecycle mutation, external dispatch, deploy, push, delete, credential entry

## Domain-skill promotion example

For PWA, React Native, mobile frontend, or other cross-platform compatibility lessons:

- Keep project facts in project profiles or scoped evidence.
- Promote only the entity-stripped pattern, such as the need to separate browser, installed app, WebView/native shell, simulator, real-device, permission, bridge, build, and screenshot evidence boundaries.
- Prefer an existing class-level delivery skill reference first; create a new class-level skill only when the routing trigger, verification matrix, and anti-conditions are independent enough.

## Report format

```text
Automation trigger audit
- Store health: <validator result>
- Capture path: <present/missing/partial>
- Backlog watcher: <present/missing/partial>
- Selfcheck registration: <present/missing/partial>
- Skill staging gate: <present/missing/partial>
- Current safe next action: <proposal-only action>
- Boundaries still closed: <mutations/external actions not authorized>
```
