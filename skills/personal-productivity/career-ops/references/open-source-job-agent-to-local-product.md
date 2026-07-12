# Open-source job-agent repo → local Career Ops product

Scope: career/job-search workflow absorption. Applicability: use when a user asks to turn an open-source Claude Code/job-agent workspace (for example a repo with `/setup`, `/apply`, portal skills, resume/CV templates, or tracker logic) into a usable Hermes Career Ops capability. Anti-conditions: do not use this as authority to auto-apply to jobs, contact recruiters, scrape credentialed portals, store private CV/JD content in global skills/memory, or claim external job-source reliability without live evidence.

## Objective

Convert transferable workflow structure into a local, privacy-bounded product slice before any external automation:

1. Local workspace initialization.
2. Local JD import.
3. Deterministic JD/CV/profile evaluation.
4. Local report and optional tracker append.
5. Batch ranking of local JDs.
6. Privacy/no-side-effect checks.
7. Multi-model certification over objective evidence.

## Source-repo due diligence checklist

Before adapting a repo, verify from live repo/code evidence rather than README claims only:

- Clone or inspect the repository tree.
- Read README/setup docs and key command/skill files.
- Check whether advertised commands actually exist as command files or are only skill-trigger text.
- Run safe CLI typechecks/tests when toolchain is available.
- Run one low-volume live search only when terms/access permit; report legal/ToS or regional blocks as source reliability boundaries, not as product failure.
- Separate reusable patterns from non-transferable market-specific portal code.

## Productization ladder

1. **Privacy contract first** — confirm user-data layer vs reusable skill layer. Candidate CV/proof/JD content belongs only in the authorized career workspace.
2. **Local CLI first** — implement deterministic local operations before portal automation:
   - `init`
   - `import-jd`
   - `evaluate`
   - `rank`
3. **Truthful scoring** — candidate-fit claims require a supplied local CV/proof source. No-CV mode is only opportunity pre-screening.
4. **Reports over actions** — write Markdown/JSON reports and optional tracker rows; never submit applications or send messages.
5. **URL reads opt-in** — local files are default; URL fetches require an explicit flag such as `--allow-url-read` and still stay read-only.
6. **Verification** — run syntax check, unit tests, smoke import/evaluate, privacy check, and report readback.
7. **Certification** — construct claims without custom prefixes so evidence IDs can link to normalized `C-001`-style claim IDs. If a first multi-model run fails because evidence supports `C1` while claims are normalized to `C-001`, rerun with plain claim text and evidence supports set to the normalized IDs.
8. **Ledger/profile writeback** — record the local MVP scope and hard-closed boundaries in the project ledger/profile. Keep external automation as a later exact-authority gate.

## Minimum acceptance evidence

- `python3 -m py_compile <cli>.py` PASS.
- Unit tests cover init/evaluate/rank and no-CV boundary.
- Smoke path imports a sample JD and writes a local report.
- Privacy check proves reusable skills/global memory do not contain private sentinel content.
- Report explicitly states no application was submitted and no recruiter/employer contact was made.
- Multi-model certification reaches truth-grounded evidence coverage for the local MVP scope, or is reported as degraded advisory only.

## Common pitfalls

- Treating README workflow diagrams as proof that slash commands exist.
- Treating a region-blocked or ToS-sensitive public portal as a stable global sourcing route.
- Copying market-specific portal integrations instead of extracting the portal-skill contract.
- Letting a sample fixture look like real user CV/JD data.
- Updating reusable skills with private candidate details or one-off JD text.
- Claiming a product is ready because model reviewers agree, without command/test/report evidence.
