# Local procedure rehearsal → validation projection

Applicability: a procedure-validation registry reports local procedures as `stale`, and they can be refreshed with isolated local-only rehearsals without external send or credential access.

Anti-conditions:
- Do not use this to open external delivery, OAuth, Lark task access, provider quorum, publish/deploy, or other authority-blocked procedures.
- A local rehearsal receipt does not certify the whole Agent OS.

## Correct projection path

`procedure_rehearsals.py` appends its own `procedure-rehearsals/` and `procedure-receipts/` directories beneath `--output-dir`. Pass the selfcheck root (normally `~/.hermes/state/selfcheck`), not the nested `.../procedure-rehearsals` directory.

Wrong:

```bash
python3 procedure_rehearsals.py local-delivery \
  --output-dir ~/.hermes/state/selfcheck/procedure-rehearsals
```

This can return `ok:true` yet place the receipt under a doubly nested path that the validation registry does not scan; the procedure remains stale.

Correct:

```bash
python3 procedure_rehearsals.py local-delivery \
  --output-dir ~/.hermes/state/selfcheck \
  --payload local-refresh
python3 procedure_rehearsals.py experience-ratchet-lifecycle \
  --output-dir ~/.hermes/state/selfcheck
```

Then rebuild the dynamic projection twice when the first pass emits receipts and the second pass consumes/projects them:

```bash
python3 dynamic_selfcheck_coverage.py run --home "$HOME" --quiet-success
python3 dynamic_selfcheck_coverage.py run --home "$HOME" --quiet-success
hermes agent-os status --json
```

## Verification

- Rehearsal output says `external_send:false` and `ok:true`.
- Receipt paths are directly under `~/.hermes/state/selfcheck/procedure-receipts/`.
- Fresh status changes only the intended local procedures to `e2e_passed` with `latest_receipt_fresh:true`.
- Authority-blocked and genuine `e2e_failed` procedures remain unchanged.
- Record the remaining certification boundary; do not interpret `e2e_passed` local procedures as global certification.
