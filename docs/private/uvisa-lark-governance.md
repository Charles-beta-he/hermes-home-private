# UVISA + Lark Hermes Governance

Status: active local governance note
Scope: `/Users/charles/.hermes`, `uvisa-app-2.0`, `uvisa-admin`, `uvisa-backend`
Purpose: prevent credential leakage, screenshot/evidence sprawl, and split workflow facts for Lark + UVISA work.

## Canonical source-of-truth map

| Domain | Canonical source | Derived / secondary | Rule |
|---|---|---|---|
| Lark OAuth/event callback boundary | `/Users/charles/.hermes/project-profiles/lark.json` | memory summary, task notes | Profile stores stable config boundary only; no secrets. |
| Lark task execution / closeout workflow | `/Users/charles/.hermes/skills/software-development/lark-task-reading/SKILL.md` + `references/` | profile overlay copies | Root skill is canonical. Overlay copies must match hash or be removed/symlinked. |
| UVISA project redlines / repo routing | `/Users/charles/.hermes/project-profiles/uvisa-app-2.0.json` | Workpad, memory | Profile stores compact redlines, repo paths, verification policy, and pointers; large maps/history should be external references. |
| Evidence screenshots | Manifest-backed evidence directory | `cache/screenshots`, `.playwright-mcp`, `test-results` | Cache/test screenshots are raw inputs, not durable proof until hashed and linked in a manifest. |
| Runtime secrets/auth/session | Keychain/env/runtime config only | `.env`, `auth.json`, `sessions/`, `state/` | Never persist values in memory/profile/skill/docs/task notes. Git must ignore these paths. |

## Landed guardrails

1. Root Hermes `.gitignore` defines the default runtime/secret boundary:
   - secrets/auth: `.env`, `auth.json`, `shared/`, key files
   - runtime state: `sessions/`, `state/`, `tick-*`, `checkpoints/`, `task_ledger.db`
   - cache/temp: `cache/`, `tmp/`, logs
   - raw evidence media: `evidence/**/*.png|jpg|jpeg|webp|mp4|mov`
2. Redacted audit script:
   - `/Users/charles/.hermes/scripts/uvisa_lark_governance_audit.py`
   - It prints only paths, counts, line numbers, variable/key names, and hashes; it never prints secret values.

## Verification commands

```bash
python3 ~/.hermes/scripts/uvisa_lark_governance_audit.py --json --redact --scope uvisa-lark > ~/.hermes/tmp/uvisa_lark_governance_audit_latest.json
python3 -m json.tool ~/.hermes/tmp/uvisa_lark_governance_audit_latest.json >/dev/null
git -C ~/.hermes check-ignore -v .env auth.json sessions/example.json cache/screenshots/example.png state/continuations/example.json tick-example/state.json
python3 -m json.tool ~/.hermes/project-profiles/lark.json >/dev/null
python3 -m json.tool ~/.hermes/project-profiles/uvisa-app-2.0.json >/dev/null
```

## P0 runbook: stop new leakage

Do now / safe:
1. Keep `.gitignore` and audit script committed as a scoped Hermes governance commit.
2. Run the audit script before and after any cleanup.
3. Treat every `.env`, `auth.json`, `sessions/`, `state/continuations/`, `state/relay-packets/`, `tick-*`, and screenshot cache finding as sensitive by default.

Requires explicit maintenance window:
1. Remove already tracked runtime files from index without deleting local copies:
   - `git -C ~/.hermes rm --cached .env auth.json`
   - `git -C ~/.hermes rm --cached -r sessions cache/screenshots state/continuations state/relay-packets tick-* checkpoints`
2. Rotate credentials that may have been present in tracked files:
   - Lark/Feishu app secret
   - model provider API keys
   - Hermes/Nous auth tokens if present
3. If the private repository was pushed with secrets, consider history rewrite (`git filter-repo`/BFG) only after backup and coordination.

## P1 runbook: unify workflow facts

1. Make root `lark-task-reading` skill canonical.
2. Compare overlay copies by hash:
   - root: `/Users/charles/.hermes/skills/software-development/lark-task-reading/`
   - overlays: `/Users/charles/.hermes/profiles/{mlops,workflow,dev}/skills/software-development/lark-task-reading/`
3. Either remove overlay copies or sync them automatically from root. Do not hand-edit overlays.
4. Add a drift check to the audit script or post-update governance check: mismatched hashes fail the governance check.

## P1 runbook: slim UVISA profile

Target structure:
1. `project-profiles/uvisa-app-2.0.json` remains the compact canonical router/redline file.
2. Bulky deep maps/playbooks/history move to referenced artifacts under a dedicated reference location, e.g.:
   - `/Users/charles/.hermes/project-profiles/references/uvisa-app-2.0/`
   - or a dedicated UVISA project skill/reference bundle.
3. Profile stores pointers and version/hash metadata, not raw screenshots/session/tick history.
4. Memory stores only durable redlines/preferences, not task completion history or volatile paths.

## P1 runbook: evidence manifest

Before deleting or using screenshots as Lark proof, create a manifest with this schema:

```json
{
  "schema": "uvisa_lark_evidence_manifest_v1",
  "task_guid": "...",
  "task_title": "...",
  "proof_kind": "target-ui|login-gate|readback|test-failure|cache-only",
  "local_path": "...",
  "sha256": "...",
  "viewport": "14inch|mobile|unknown",
  "backend": "real|mock|unknown",
  "native_lark_attachment_id": "...|unknown|not_attached",
  "readback_verified": false,
  "classification": "durable-proof|raw-input|duplicate|discardable"
}
```

Rules:
- Login-gate screenshots prove authentication blocker only; they do not prove target task UI.
- `.playwright-mcp` and `test-results` screenshots are raw local artifacts until promoted by manifest.
- Duplicate hashes should be classified before deletion.

## Rollback

- `.gitignore` rollback: `git -C ~/.hermes checkout -- .gitignore` if committed, or remove the file if uncommitted.
- Audit script rollback: remove `/Users/charles/.hermes/scripts/uvisa_lark_governance_audit.py`.
- Do not rollback by re-adding secrets to git. If index cleanup was performed, restore only intentional source files.

## Non-goals

- This document does not store secret values.
- This document does not certify that existing secrets have been rotated.
- This document does not delete evidence or rewrite git history by itself.
