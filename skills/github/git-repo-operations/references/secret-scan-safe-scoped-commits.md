# Secret-scan-safe scoped commits in Hermes/control-plane homes

Applicability: committing a scoped local Hermes/control-plane fix when pre-commit secret scan fails on an ignored/high-risk config file such as `config.yaml`, while the intended staged diff does not include the secret.

Anti-conditions:
- Do not bypass with `--no-verify` unless the user explicitly accepts the risk.
- Do not stage broad runtime/config drift just to satisfy a commit.
- Do not print secret values in the final report.

## Pattern

Some hooks scan high-risk local config files in addition to the staged diff. A commit can fail even when the intended staged files are clean because an ignored config contains an inline credential. Treat this as a real safety gate, not a false positive.

## Fix path

1. Identify the config key shape without exposing the value. Redact output to key name, path, and length/fingerprint only.
2. Migrate inline credentials to an ignored secret store (`~/.hermes/.env`) and replace config values with an environment placeholder supported by the runtime, for example `${STITCH_API_KEY}`.
3. Verify the runtime resolves the placeholder using the same loader path that production uses.
4. Run the secret scanner manually before committing:

```bash
python3 ~/.hermes/scripts/working_tree_secret_scan.py --repo ~/.hermes --staged
```

5. Stage only the intended tracked files. If config is ignored/untracked, do not force-add it unless the user explicitly asked to version the config policy.
6. Inspect staged scope before commit:

```bash
git -C ~/.hermes diff --cached --name-only
git -C ~/.hermes diff --cached --stat
```

7. Commit normally and let hooks run.

## Verification evidence

Report:
- secret scan PASS;
- runtime placeholder resolved, but only with boolean/length evidence;
- staged file list/stat;
- commit hash;
- remaining ignored/untracked evidence/config paths separately.

## Security note

If a tool output displayed the secret during diagnosis, recommend rotating the exposed key even if it is now moved to `.env`.
