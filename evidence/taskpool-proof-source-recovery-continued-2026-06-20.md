# Taskpool proof source recovery continued — 2026-06-20

## User authority

User selected path 1 again: continue searching for earlier/external proof logs.

## Search scope added in this continuation

### Filename / index search

- Spotlight filename search for `auto_run_proof*` under `/Users/charles`.
- Spotlight archive search for likely `hermes` / `brain` / `backup` zip/tgz/tar packages.
- `/Volumes` shallow search for direct proof logs and likely backup archives.
- `tmutil listlocalsnapshots /` check for local Time Machine snapshots.

Results:

- No direct `auto_run_proof.jsonl` found outside active `.hermes` state.
- No mounted `/Volumes` candidates found.
- `tmutil` reported no local snapshots.

### Common sync/backup directories

Checked existence and scanned file names under:

- `/Users/charles/Library/Mobile Documents/com~apple~CloudDocs`
- `/Users/charles/Desktop`
- `/Users/charles/Documents`
- `/Users/charles/Downloads`
- `/Users/charles/.hermes/backups`

New archive candidate found:

- `/Users/charles/Documents/Untitled/Untitled-backups/Untitled-2024-03-20_145514.zip`

Archive inspection results:

- `Untitled-2024-03-20_145514.zip`: no `auto_run_proof`, no relevant proof/workflow ids.
- `/Users/charles/Downloads/personal-hermes-brain-main.zip`: no `auto_run_proof`, no relevant workflow consolidation ids; contains older brain proof notes only.

### All visible archive content scan

Scanned 127 visible zip/tgz/tar archives under the scoped local roots for:

- `0cd6ac5a5e4faaf36f6453051e5952dc17e68f7de3dd3c4709da605cd0a7ee44`
- `2026-06-13-workflow-kernel-consolidated-candidatemodel-routes`
- `2026-06-13-workflow-kernel-consolidated-candidatemodule-contracts`
- `2026-06-13-workflow-kernel-consolidated-candidatesafety-flags`
- `tpcon_4421e19ba058d222`
- `tpwrite_f62e8067efc48f89`
- `rti_2c322fc59264ae3d`

Findings:

- Only migration backup task/kanban/continuation archives contain references.
- `kanban.tgz` logs only show agents reading the candidate consolidation artifact and task notes; they do not contain an autorun proof event.
- `tasks.tgz` contains the same task notes with the same invalid proof hash.
- No archive provided an older `auto_run_proof.jsonl` containing the missing event.

### Session database search

Searched past sessions for:

- `0cd6ac5a5e4faaf36f6453051e5952dc17e68f7de3dd3c4709da605cd0a7ee44`
- `tpcon_4421e19ba058d222`
- `workflow-kernel-consolidated-candidatemodel-routes`
- `candidate_consolidation`

Results: no session hits.

## Current conclusion

The remaining workflow-kernel invalid proof hash has no recoverable source in locally visible active state, backups, common cloud/sync directories, visible archives, mounted volumes, Time Machine local snapshots, or session DB.

Remaining affected tasks:

1. `2026-06-13-workflow-kernel-consolidated-candidatemodel-routes`
2. `2026-06-13-workflow-kernel-consolidated-candidatemodule-contracts`
3. `2026-06-13-workflow-kernel-consolidated-candidatesafety-flags`

Shared invalid proof:

`proof:sha256:0cd6ac5a5e4faaf36f6453051e5952dc17e68f7de3dd3c4709da605cd0a7ee44`

## Remaining external options

To continue path 1, the next required input is a new source not currently visible to the machine:

- a Time Machine disk mounted under `/Volumes`,
- NAS / external disk / old machine export,
- iCloud/Drive archive not currently synced locally,
- any old `.hermes/state/auto_run_proof.jsonl` around 2026-06-12 to 2026-06-14.

Without one of those, any automatic replacement would be proof fabrication or unrelated proof substitution.
