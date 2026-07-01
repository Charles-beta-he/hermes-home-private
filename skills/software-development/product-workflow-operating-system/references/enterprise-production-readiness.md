# Enterprise Production Readiness Reference

Scope: use when a user asks whether an AI/mobile/product workflow can launch, become enterprise-production-grade, or be scored for production readiness.

Applicability:
- Product asks include `是否可上线`, `企业生产级`, `production ready`, `全盘推进至落地`, `beta`, `TestFlight`, `launch readiness`, or similar.
- The artifact is an AI assistant, PM agent, voice workflow, mobile app, execution gateway, or governed automation.
- The user expects implementation and evidence, not only a verbal assessment.

Anti-conditions:
- Do not claim enterprise readiness from unit tests/builds alone.
- Do not treat governance drafts as runtime controls.
- Do not convert unresolved credentials, legal approval, real-device QA, external side-effect authority, or release ownership into “done.”

## Enterprise readiness model

Use a scored artifact, not a loose opinion. Minimum dimensions:

| Dimension | What to check |
| --- | --- |
| Core user loop | Primary ICP can complete the intended job with readback and recovery. |
| Voice/realtime UX | If voice is promised: partials, final transcript, failure handling, VAD/barge-in/TTS if marketed as realtime. |
| Execution authority | External actions have confirmation, audit, rollback, and readback. Dry-run is not production execution. |
| Product workflow | Product/design/strategy requests create durable artifacts, not generic chat replies. |
| Engineering quality | Tests, lint, build, E2E/manual matrix, native crash/permission/no-network coverage. |
| Security/privacy | Secrets excluded, data retention/deletion/export, privacy copy, permission disclosure. |
| Release/ops | Repo/revision, version/build number, release channel, rollback, monitoring, crash/logging. |
| Enterprise controls | SSO/RBAC/admin policy/audit log/data residency where enterprise customers are targeted. |

Recommended weighted decision:

```text
<45  prototype
45-69 internal alpha
70-84 limited beta
85+  enterprise ready only if no P0 blockers remain
```

## Full-landing expectation

For `全盘推进至企业生产级` tasks, keep landing safe local layers until a true boundary appears:

1. PM/intent router for product requests.
2. Durable artifact contract: story card, PRD slice, launch readiness, acceptance criteria, enterprise scorecard.
3. Conversation/workspace ledger integration so artifacts are not side notes.
4. UI/readback surface for the scorecard and next gate.
5. Tests proving product requests route to artifacts and non-product requests remain on the normal path.
6. Governance drafts for privacy, release, QA, and enterprise controls when runtime implementation is not yet authorized.
7. Real tests/builds/screenshots.

Stop only at true gates:

- real external executor authority;
- credential/provider setup;
- legal/privacy approval;
- real-device manual permission/voice QA;
- repo/release ownership;
- SSO/RBAC/audit runtime decisions.

## Common pitfalls

1. **Score inflation trap**: governance documents and simulator builds improve readiness, but do not equal enterprise controls or real-device QA. Keep blockers in the scorecard.
2. **Dry-run-as-production trap**: a dry-run gateway can validate projection and retry logic, but production execution requires a real executor/readback protocol and authority gate.
3. **Artifact side-note trap**: PM analysis in a markdown file is not product logic unless the app/workflow routes relevant intents into durable artifacts and readback.
4. **Public launch wording trap**: distinguish local demo, internal alpha, limited beta, and enterprise production. Do not collapse them into a single “上线” answer.
5. **Not-a-repo release trap**: if a project directory is not a git repo or has no release provenance, release governance is blocked even if builds pass.

## Verification checklist

- [ ] Scorecard dimensions and weights are explicit.
- [ ] Decision is one of: local demo, internal alpha, limited beta, enterprise production.
- [ ] P0 blockers are listed separately from P1/P2 improvements.
- [ ] Runtime/product changes are tested, not only documented.
- [ ] Governance drafts are labeled as drafts and linked to the score, not treated as shipped controls.
- [ ] Evidence includes commands, build/test outputs, screenshots, and repo/release status.
