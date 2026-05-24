# Lark Task Reader Troubleshooting

> Session-discovered issues with lark_task_reader.py and Lark API integration.

## Bug: TOKEN_EXPIRED when token is valid

**Root cause:** `lark_task_reader.py` line 179 checks `tokens[k].expiresAt` but lark-mcp auth store uses `expiresAt` (with 's'). The token key IS the JWT value. When `authStore.initialize()` resolves, `storageDataCache.tokens` is a dict where:
- keys = JWT token strings
- values have `expiresAt` (float, unix seconds) — NOT `expireAt`

**Fix:** The script at line 179 should use `expiresAt` (already correct in current code). If TOKEN_EXPIRED still appears, the issue is likely a race condition with `authStore.initialize()`. Retry once.

**Verification:**
```bash
node -e "
const {authStore} = require('/Users/charles/.nvm/versions/node/v24.14.0/lib/node_modules/@larksuiteoapi/lark-mcp/dist/auth/store.js');
authStore.initialize().then(() => {
  const tokens = authStore.storageDataCache.tokens || {};
  const keys = Object.keys(tokens);
  if (!keys.length) { process.stderr.write('NO_TOKEN\n'); process.exit(1); }
  const valid = keys.find(k => !tokens[k].expiresAt || Date.now() / 1000 <= tokens[k].expiresAt);
  if (!valid) { process.stderr.write('TOKEN_EXPIRED\n'); process.exit(1); }
  process.stdout.write(valid);
  process.exit(0);
}).catch(e => { process.stderr.write(String(e)); process.exit(1); });
```

## Bug: Tasklist scope matching fails

**Root cause:** `/task/v2/tasks` returns `tasklists[].guid` (NOT `tasklist_guid`). The `prioritize_tasks()` function looks for `tasklist_guid` key, finds nothing, sets scope to `none` for all tasks.

**API shape:**
```json
// /task/v2/tasklists response
{"guid": "f54ae60c-...", "name": "UVISA-2.0新版开发"}  // key is "guid"

// /task/v2/tasks response
{"tasklists": [{"guid": "f54ae60c-..."}]}  // key is "guid", not "tasklist_guid"
```

**Workaround:** Fetch tasklist GUIDs directly from `/task/v2/tasklists`, then use `/task/v2/tasklists/{guid}/tasks` to get scoped tasks.

**Verification script:**
```python
import sys, json
sys.path.insert(0, str(__import__('pathlib').Path.home()/'.hermes/scripts'))
from lark_task_reader import get_token, LarkClient

token = get_token()
client = LarkClient()

# 1. Get tasklist GUIDs
tl_data = client.get("/task/v2/tasklists", token, query={"page_size": 50})
tl_map = {}
if tl_data.get("code") == 0:
    for tl in (tl_data.get("data", {}).get("items", [])):
        tl_map[tl.get("name", "")] = tl.get("guid", "")

# 2. Fetch tasks from specific tasklist
UVISA_TL = tl_map.get("UVISA-2.0新版开发")
if UVISA_TL:
    data = client.get(f"/task/v2/tasklists/{UVISA_TL}/tasks", token, query={"page_size": 100})
    items = data.get("data", {}).get("items", [])
    print(f"UVISA-2.0 tasks: {len(items)}")
```

## Bug: completed_at is string '0', not int 0

**Root cause:** Lark API returns `completed_at: "0"` (string) for incomplete tasks. Python `not "0"` is `False` (truthy string), so `filter(lambda t: not t.get('completed_at'))` drops ALL tasks.

**Fix:** Filter by `status == 'todo'` instead of checking `completed_at`.

## Key API Facts
- `lark-mcp whoami` shows current auth status
- `lark-mcp login` needs `--domain https://open.larksuite.com` for international
- Fixed port 3010 for OAuth redirect
- App ID: `cli_a96f6a6211f91ed2`
- `/task/v2/tasks?completed=false` fetches incomplete tasks
- Tasklist GUIDs are stable; names can change
