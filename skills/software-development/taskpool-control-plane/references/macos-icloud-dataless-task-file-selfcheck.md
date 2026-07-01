# macOS iCloud dataless task-file selfcheck pitfall

Applicability: Hermes/local-brain taskpool selfcheck or full task iteration fails on macOS while reading Markdown task files, especially under an iCloud/Obsidian vault.

Anti-conditions:
- Do not use this to mask real taskpool lifecycle/proof failures after files are readable.
- Do not delete, move, or hydrate user vault files without explicit user approval.
- Do not record a one-off unreadable path as a global rule; diagnose the current unreadable file each time.

## Symptom

`brain_task_orchestrator.py selfcheck --json` or another full task scan raises:

```text
OSError: [Errno 11] Resource deadlock avoided
```

The traceback usually points at `path.read_text(encoding="utf-8")` inside task iteration.

## Diagnosis pattern

1. Find the first unreadable task markdown by iterating `*.md` and reading each file until the exception occurs.
2. Inspect that file rather than the whole taskpool:

```bash
ls -lO@ "/path/to/unreadable task.md"
stat -f '%N %z bytes %Sp flags=%f' "/path/to/unreadable task.md"
```

3. If flags show `compressed,dataless`, treat it as a macOS/iCloud storage artifact. A duplicated file with a ` 2.md` suffix may be dataless while the original file is readable.
4. Verify whether the corresponding non-duplicate/original task file is readable before claiming data loss or taskpool corruption.

## Safe handling

- If the user authorizes cleanup/hydration, hydrate or move the dataless duplicate, then rerun full selfcheck.
- If no authorization is available, report the specific unreadable path and stop; do not silently delete/move it.
- Keep unrelated verification results separate: Portfolio/pytest/config checks can still be valid even when full taskpool selfcheck is blocked by one unreadable vault file.

## Lesson

The durable lesson is the diagnostic and approval pattern, not that taskpool or the filesystem tool is broken. Once the file is hydrated or removed with approval, rerun the canonical selfcheck and use that result as the current truth.
