# Cron Telegram delivery debugging

Use this reference when a scheduled Hermes report or reminder appears to have "not sent" to Telegram.

## Triage shape

1. Separate generation from delivery.
   - `cronjob list` can show `last_status: ok` while `last_delivery_error` is non-empty.
   - Read the job output under `~/.hermes/cron/output/<job_id>/...` before concluding the report failed to generate.
   - Check any report artifact paths mentioned inside the cron output.

2. Correlate scheduler logs.
   - Look for `Running job '<name>'`, `Turn ended`, `Job '<name>' completed successfully`, and then delivery lines.
   - Also search for `missed its scheduled time` / `Fast-forwarding to next run` to rule in/out a skipped fire.

3. Validate Telegram SDK in the *actual cron/gateway runtime* and with dotenv loaded.
   - Cron/gateway may run from `~/.hermes/hermes-agent/.venv` while interactive CLI checks use `~/.hermes/hermes-agent/venv` (or vice versa). Do not assume the first venv that imports `telegram` is the one that scheduled delivery used.
   - Check both repo venvs when present, then run the config/import probe with the runtime that failed:

```bash
cd ~/.hermes/hermes-agent
for py in ./.venv/bin/python ./venv/bin/python; do
  [ -x "$py" ] || continue
  "$py" - <<'PY'
import sys, importlib.util
print('python', sys.executable)
print('telegram_spec', importlib.util.find_spec('telegram'))
try:
    from telegram.ext import Application
    import telegram
    print('telegram_ok', getattr(telegram, '__version__', None), telegram.__file__)
except Exception as e:
    print('telegram_import_error', type(e).__name__, e)
PY
done
```

```bash
cd ~/.hermes/hermes-agent
./.venv/bin/python - <<'PY'  # switch to ./venv/bin/python if that is the scheduler runtime
import sys
sys.path.insert(0, '.')
from hermes_cli.env_loader import load_hermes_dotenv
load_hermes_dotenv()
from gateway.config import load_gateway_config, Platform
from gateway.platforms import telegram as tg
print('telegram_available', tg.TELEGRAM_AVAILABLE, 'check', tg.check_telegram_requirements())
cfg = load_gateway_config()
p = cfg.platforms.get(Platform.TELEGRAM)
print('enabled', bool(p and p.enabled), 'token_set', bool(getattr(p, 'token', None)))
PY
```

   - If the active runtime lacks the SDK and has no `pip`, install into that runtime with `uv` instead of switching to the wrong environment:

```bash
uv pip install --python ~/.hermes/hermes-agent/.venv/bin/python 'python-telegram-bot==22.6'
```

4. Run a direct standalone delivery smoke after config validation.
   - This tests the same standalone path cron uses when not using a live adapter.
   - Send a short diagnostic message to the configured home/known chat; verify `success=true` and `message_id`.

5. For a scheduled report, force the scheduler path when verifying the fix.
   - Tool-level `cronjob(action='run')` may only mark the job due; it does not by itself prove the scheduler executed and delivered.
   - Use CLI trigger plus one tick, then read back the job record:

```bash
hermes cron run <job_id>
hermes cron tick
python - <<'PY'
from pathlib import Path
import json
job_id='<job_id>'
jobs=json.loads(Path('~/.hermes/cron/jobs.json').expanduser().read_text(errors='replace'), strict=False)['jobs']
j=[x for x in jobs if x.get('id')==job_id][0]
print({k:j.get(k) for k in ['last_run_at','last_status','last_error','last_delivery_error','next_run_at']})
PY
```

   - Success criteria: `last_status == 'ok'` and `last_delivery_error is None` after the forced tick.

6. Interpret `python-telegram-bot not installed` carefully.
   - If imports succeed in one Hermes venv but fail in another, the root cause is runtime/venv skew; install/fix the runtime actually used by cron/gateway.
   - If imports succeed in the actual runtime and standalone send works, the message is likely an over-broad `ImportError` catch or stale runtime/module state, not actual missing dependency.
   - Preserve the original error text, but do not stop at `pip install`; capture the real failing import/source when fixing code.

7. Watch for live-adapter connection-pool pressure separately.
   - `Pool timeout: All connections in the connection pool are occupied` indicates Telegram adapter send/edit pressure.
   - It may explain transient live-adapter failures, but it is a separate mechanism from a completed cron run whose final delivery used the standalone path.

## Verification checklist

- Report generated artifact exists and is readable.
- Job `last_status` and `last_delivery_error` are both inspected.
- Scheduler log shows whether the job ran, completed, skipped, or failed.
- Telegram target resolves to the expected chat ID/name.
- Hermes venv can import `telegram`, `telegram.ext`, and load config with token set.
- A short standalone send returns `success=true` plus a concrete `message_id`.

## Anti-conditions

Do not save a durable claim that Telegram, cron, or `send_message` is broken just because one run failed. If retry/smoke succeeds, save the diagnostic pattern and any code-level over-broad exception issue separately.