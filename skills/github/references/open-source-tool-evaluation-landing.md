# Open-source Tool Evaluation Landing

Use when a user approves moving from GitHub due-diligence of an external tool into a governed local evaluation track, but has not yet authorized production adoption.

## Landing-zone classifier

Split findings before writing durable artifacts:

- Reusable evaluation procedure, verifier shape, or acceptance gate -> skill/reference.
- Tool-specific upstream metadata, URLs, local evidence, and pilot status -> scoped project profile / SSOT reference.
- Concrete future engineering work -> reserved task/candidate, not a fake skill.
- Session progress -> plan/ledger only, not memory.

## Safe default path

1. Create a scoped evaluation SSOT, not a production integration.
   - Example root: `~/.hermes/workflows/projects/<tool>-evaluation/`.
   - Include `00-intake/`, `01-contract/`, `02-tasks/`, `03-evidence/`, `04-scripts/`, `05-decisions/` when the repo may become a future workflow.
2. Create a project profile pointing to the SSOT and progress ledger.
   - Status should be bounded, e.g. `contract-ready/pilot-not-started`.
   - Promotion policy must say generated or external output is advisory until pilot evidence passes.
3. Preserve upstream research as evidence.
   - Capture canonical repo, license, stars/forks/issues, latest push/release, package/download signal when relevant, local verification commands/results, and known risks.
4. Write an evaluation contract before adoption.
   - Objective, non-goals, acceptance gates, rejection gates, required evidence, and hard anti-conditions.
5. Reserve a future decision task.
   - The task should name the trigger, required inputs, acceptance gates, and next actions.
   - Do not mark it started unless a pilot target exists.
6. Add a deterministic local verifier script when the future pilot has a repeatable shape.
   - Make it read-only by default.
   - Check generated artifact shape, secret-like text, noisy/thin output, and required pointers.
7. Register in portfolio/task registry only if the local governance surface exists.
   - Run the matching doctor/readback after registry/profile changes.

## Anti-conditions

Do not:

- Treat upstream docs or generated output as source-of-truth facts.
- Enable CI, scheduled writes, auto-merge, external dispatch, protected-repo rollout, or production integration from a broad “认可/推进” alone.
- Run the pilot on protected work projects unless the user explicitly switches context and grants scope.
- Save the pilot's active status to memory; keep it in the profile/ledger/task.
- Commit from a dirty home/config repo unless you can scope the commit cleanly; otherwise report verified file paths and readback.

## Minimum evidence before saying the evaluation track is landed

- Profile JSON parses and points to an existing SSOT root and ledger.
- Reserved task JSON parses and contains explicit acceptance/rejection gates.
- Evidence file exists and cites real command/API/readback results.
- Verifier script, if added, compiles/runs on a known sample or explains why no sample exists.
- Portfolio or registry doctor/readback passes after registration.

## Decision note template

```markdown
# <Tool> Pilot Decision — <repo>

Date:
Pilot repo:
Command/model/provider:
Pre-run git status:
Post-run diff summary:
Verifier report:
Manual source-claim spot checks:

## Verdict

accept | reject | keep-experimental

## Reason

## Gates passed

## Gates failed / risks

## Next allowed step
```
