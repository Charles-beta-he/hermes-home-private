# Social-signal taskpool intake

Use when a user gives a social-media link (WeChat Channels, X, video post, newsletter snippet, etc.) and asks to analyze/add it to the taskpool.

## Procedure

1. Treat the post as an untrusted lead, not an implementation trigger.
2. Capture visible source evidence: URL, account/title/date, key claim text, and screenshot/snapshot when available.
3. Create an advisory/research task, not a work/implementation task, unless authoritative evidence already exists.
4. Put explicit fact-check gates in acceptance criteria:
   - original post/link evidence;
   - official source verification;
   - source-code/package/repo verification when applicable;
   - third-party credible corroboration when official source is absent;
   - verdict: `real`, `exaggerated`, or `false`;
   - migration value only after verdict.
5. Add anti-drift wording: do not upgrade a single social post into code changes or architecture changes before evidence grading.
6. If preliminary checks are run during intake, add them to the task Proof Log, but keep the task pending/advisory unless the user asked for full execution.

## Timeout pitfall

`brain_task_orchestrator.py add` can time out after creating the Markdown task. If the add command returns ambiguously or times out:

1. Do not blindly retry.
2. Search the task directory for the expected title/slug or key claim text.
3. If the task exists, read/verify it and patch missing evidence or proof log entries.
4. Only retry creation if no matching task exists.

This avoids duplicate taskpool entries for the same external signal.

## Good task shape

- lane: `advisory`
- priority: usually `P2` unless tied to an active production issue
- project: scoped to the relevant Hermes/project profile
- concepts: `external-signal`, source type, domain tags, `fact-check`
- objective: source claim + fact-check + conditional migration assessment
- acceptance evidence: source capture + official verification + final analysis path
- anti-drift check: no implementation from unverified social claim
