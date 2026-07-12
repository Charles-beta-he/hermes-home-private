# Portfolio semantic truth repair

Use when a portfolio/project-registry audit finds that structural checks pass but project status, evidence, or maturity claims are semantically weak.

## Trigger

- Portfolio doctor / strict verify is green, but a Fable/multi-model/manual audit reports gaps like:
  - empty `current_components`;
  - `validated-*` status without current declared evidence;
  - project status says `unverified` or `missing` but the portfolio summary treats it as pass;
  - work projects excluded from autonomous advancement still generate noisy generic warnings;
  - evidence/readback artifacts exist on disk but are not declared in profile/registry.

## Landing-zone rule

This is a metadata/registry/SSOT repair pattern, not project implementation.

Allowed by default:
- profile/registry metadata edits;
- portfolio progress-ledger entries;
- local semantic audit scripts;
- read-only doctor/verify/audit readbacks;
- Fable/multi-model advisory review.

Not allowed without a separate exact authority gate:
- project code changes;
- lifecycle/status promotion to validated/production;
- external dispatch, publish, deploy, push;
- destructive cleanup;
- credential/payment/secret entry;
- touching protected work-project code such as UVISA/UAEC unless the user explicitly switches to that project.

## Procedure

1. Run the structural baseline first:
   - portfolio doctor;
   - strict verify;
   - registry/profile set reconciliation.
2. Build or run a semantic audit layer that treats each project as a coverage dimension. A dimension is covered only when it has:
   - current local readback evidence;
   - verdict;
   - known gaps / blind spots;
   - next action.
3. Fix sparse profiles honestly:
   - fill `current_components` from existing profile/ledger/SSOT facts;
   - if a profile is intentionally minimal, say so explicitly in `audit_semantics` rather than leaving `{}`;
   - for work/client projects, add an explicit work-project exemption and keep code advancement closed unless the user switches context.
4. Resolve maturity-claim drift:
   - if a `validated-*`, `promoted`, `production`, or similar status lacks current evidence, downgrade the portfolio-facing status to an evidence-honest state such as `ledgered-needs-evidence`;
   - preserve `previous_status` so the history is not lost;
   - set `audit_semantics.next_audit_action` describing the exact evidence needed to restore the higher status.
5. Resolve known-negative statuses honestly:
   - if a project says files are missing or claims are unverified, do not convert it to runtime PASS;
   - keep the negative status and add `audit_semantics` such as `known_gap_not_validated` plus the restore/readback gate.
6. Declare evidence rather than relying on discovery:
   - add `portfolio_evidence` or equivalent declared evidence paths for current local readback artifacts;
   - do not invent evidence; if only profile/ledger exists, say the project is ledgered/needs-evidence.
7. Re-run verification:
   - py_compile any new scripts;
   - JSON-validate changed registry/profile/manifest files;
   - portfolio doctor;
   - strict verify;
   - semantic audit with `--fail-on-warning` if available.
   - Also run the Hermes CLI operator surface when available: `hermes portfolio --json` and `hermes portfolio verify --json`. The CLI verifier may be stricter than the project-local scripts: it requires `portfolio_profile: true`, a UVISA `portfolio_code_guard` containing `Do not modify UVISA project code`, and required Portfolio OS docs/status/receipt paths (`00-model/portfolio-os.md`, `02-literature/core-works-and-arguments.md`, `03-governance/merge-and-abstraction-governance.md`, `04-merge-candidates/initial-project-relations.md`, `05-status/portfolio-status.md`, `05-status/production-receipt.md`). If these are missing, create truthful metadata/operator-surface receipts; do not invent production deployment evidence.
8. Ask the review model/Fable to review the repair only in the limited domain: declared coverage and metadata truthfulness. Require it to state what is not certified.
9. Write a manifest and progress-ledger entry with hashes/paths and explicit boundaries.

## Reporting language

Use:
- `PASS (limited to declared coverage + metadata truthfulness)`
- `100% coverage under the declared project-dimension model; this does not mean production health`
- `downgraded unsubstantiated validated claims while preserving previous_status`

Avoid:
- `portfolio is fully healthy`
- `all projects are validated`
- `runtime ready`
- `production complete`

## Pitfalls

- A green structural doctor does not prove semantic truthfulness.
- A mission `resume` can still be a false restoration when the tick budget is exhausted. After any mission resume/budget action, require `hermes mission doctor <id> --json` showing status ok and tick budget ok. If an exact local budget extension is authorized, record rollback backup, target mission id, before/after budget, preserved blocked actions, unchanged cadence, and fresh doctor readback; do not open external/push/deploy/secret/destructive gates unless separately authorized.
- An audit script edited in the same change can become self-certifying; mitigate with explicit downgrades, visible known gaps, manifest hashes, and independent/Fable review.
- Exemptions can become a silent bypass. Work-project exemptions need explicit reason, next action, and should not be used to hide real implementation claims.
- Adding `current_components` is not proof that components work; it is only a profile truthfulness repair unless backed by runtime/readback evidence.
