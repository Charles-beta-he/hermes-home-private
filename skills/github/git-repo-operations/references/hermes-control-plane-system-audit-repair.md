# Hermes control-plane system audit and scoped repair

Use when a Hermes/control-plane home has system-level selfcheck failures, a dirty runtime checkout, hook/cron/edge-worker drift, or a user asks for a model-led system/architecture audit followed by safe local repair.

## Applicability

- Active system is a local Hermes/control-plane home such as `~/.hermes`.
- Symptoms include detached runtime checkout, post-update guard failures, hook registry schema drift, stale local registry entries, or local service bind-address risk.
- User authorizes local safe repair, but not push/deploy/destructive cleanup/credential entry.

Anti-conditions:
- Do not use this as authority to push, deploy, reset hard, delete untracked evidence, bulk-stage a dirty home, change provider credentials, lower quorum, or change fail-open/fail-closed semantics without explicit approval.
- Do not treat an external model audit as evidence by itself. It can prioritize; local commands/tests prove.

## Model-led audit packet pattern

1. Build a read-only evidence packet first:
   - current timestamp;
   - Hermes version;
   - exact model probe receipt if using Claude Code/Fable (`is_error=false` and `modelUsage` includes the concrete model);
   - runtime repo branch/status/log;
   - `post-update-check.py --fix` summary;
   - cron jobs summary with `last_status`/delivery errors;
   - taskpool/brain selfchecks;
   - provider status where relevant;
   - local service/port evidence for exposed workers.
2. Ask the model for system + architecture + multi-angle audit, with boundaries:
   - no file changes or commands by the model;
   - P0/P1/P2 ranking;
   - root-cause hypotheses;
   - fix and verification plan;
   - explicit do-not-do list.
3. Treat the model output as advisory. Execute only the local, reversible, evidence-backed subset.
4. After repair, send a compact repair evidence packet back to the model for independent audit; correct any model misreadings with local evidence.

## Safe repair ladder

1. Protect rollback state before branch or config changes:
   - record detached/current SHA;
   - create a protection branch if on detached HEAD;
   - stash or commit only scoped dirty files before switching branches;
   - preserve existing stashes.
2. Restore runtime branch baseline only after protection:
   - check `branch --contains HEAD`, target branch tip, ahead/behind counts, and status;
   - switch to the expected branch if safe;
   - do not reset or discard detached-only commits.
3. Fix schema-manifest drift by adding declarations, not changing behavior:
   - for lifecycle gates, add explicit `hook_class` and `fail_policy` matching existing `fail_closed`/observer semantics;
   - plugin hook string shorthands may need conversion to mapping entries with `name`, `hook_class`, `fail_policy`;
   - verify with the hook registry selfcheck.
4. Fix local service exposure with least authority:
   - if an edge/local worker with command/file capabilities listens on `0.0.0.0`, change config/LaunchAgent to `127.0.0.1` unless the user explicitly authorized LAN exposure;
   - reload the service and read back `lsof` showing `127.0.0.1:<port>`;
   - if registry entries key worker IDs by bind host, re-register local config and ensure stale `0.0.0.0` entries are replaced.
5. Use TDD for registry or control-plane behavior changes:
   - write a failing test reproducing stale duplicate local-node behavior;
   - implement the smallest replacement/dedup rule;
   - run the focused test and the full related test file.
6. Commit only the scoped repair files:
   - inspect `git diff --check` and `git diff --cached --name-status`;
   - commit with a narrow message;
   - leave unrelated runtime/evidence/workflow files unstaged.

## Verification checklist

- Runtime checkout is on the expected branch and `brainctl --json brains validate` has `passed=true` with no errors.
- `post-update-check.py --fix` shows prior BROKEN items turned OK and no new BROKEN items.
- Hook registry selfcheck returns `ok=true` and `issues=[]`.
- Edge/local worker tests pass if registry behavior changed.
- Port readback shows loopback binding for local-only workers (`127.0.0.1:<port>`), not `*:port`.
- Edge/selfcheck reports one current local node, no stale LAN-bound duplicate, and no warnings/errors.
- A post-repair model audit was run only against evidence, and any model misconceptions were corrected with local proof.
- Final report separates completed P0/P1 repairs from P2 debt and authority-gated follow-ups.

## Pitfalls

- A detached runtime branch can cascade into multiple unrelated-looking selfcheck failures. Fix branch baseline before patching code.
- `private_repo_governance` and another guard may disagree on detached HEAD; do not rely on one green guard when another source of truth fails.
- A local service config change from `0.0.0.0` to `127.0.0.1` may leave stale registry records if worker IDs include bind host. Re-register and verify the stale worker was replaced.
- Adding `fail_policy` fields is safe only when it records existing behavior. Changing actual fail-open/fail-closed semantics is a separate governance proposal.
- External model reviews may hallucinate commit provenance or interpret protected historical branches as new work. Always reconcile with `git status`, branch containment, and local diffs before reporting.
