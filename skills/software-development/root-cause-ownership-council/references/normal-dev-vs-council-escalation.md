# Normal Development vs Council Escalation

Version: 1.2.0

Scope: routing guardrail that prevents the council from becoming default ceremony while still capturing frontend/backend/UI/UX specialist experience when risk signals appear.

Applicability: use whenever the router must decide between direct implementation, specialist review, ownership audit, full council, or release certification.

Anti-condition: do not use this as an excuse to skip verification. Direct fixes still need focused tests/readback.

## Route table

| Route | Use when | Output |
|---|---|---|
| Direct fix | Single deterministic low-risk defect with direct evidence | Patch + focused verification |
| Specialist review | One domain skill/experience is enough | Specialist findings + scoped verification |
| Ownership audit | Same state/lifecycle has multiple writers/controllers | Owner table + cleanup path |
| Lightweight council | Medium-risk repeated or ambiguous issue | 3-role packet + regression plan |
| Full council | High-risk cross-domain repeated issue or user asks root cause | Full owner/evidence/falsifier packet |
| Release certification | Merge/release/issue close/A+ readiness | Final Certifier verdict + target readback |

## Direct fix triggers

- Typo, static label, deterministic one-file error.
- Failing test points to direct cause and no shared owner conflict.
- UI copy/style tweak with no interaction or state change.
- Docs-only update.

Required evidence:
- focused test/readback or file diff;
- no unrelated broad staging.

## Specialist review triggers

- Frontend UI/UX issue: Xianggua, UIMax, Accessibility, Product Standard.
- API contract issue: API Contract Reviewer.
- Database change: Migration & Data Integrity.
- Endpoint/security change: Security & Permission.
- Async/payment/retry: Concurrency & Idempotency.
- Release/merge: Release Readiness.

Required evidence:
- specialist-specific proof listed in `development-experience-coverage-matrix.md`.

## Council escalation triggers

Escalate when:

- second or third patch for the same symptom appears;
- new fix adds another global listener, route exception, timeout, force reload, or feature flag;
- specialist outputs disagree;
- frontend and backend each claim the other owns the state;
- a UI symptom is actually a lifecycle/ownership problem;
- release/certification needs evidence across multiple domains.

## De-escalation rules

De-escalate when:

- owner table shows only one writer and one direct fix;
- failing test and source code prove a small localized bug;
- user explicitly asks for a prototype and accepts limited verification;
- council would only restate obvious facts.

## Closure standards

Direct fix done:
- focused verification passed;
- changed files match intended scope.

Specialist review done:
- specialist produced findings and required evidence;
- no unresolved blocker or clear escalation path exists.

Council done:
- owner table, evidence ledger, falsifier, minimal boundary, regression matrix, and final verdict exist.

Release/issue done:
- PR merged or target artifact published;
- issue closed if applicable;
- target branch/artifact readback proves expected files/version/behavior;
- residual risks are stated.
