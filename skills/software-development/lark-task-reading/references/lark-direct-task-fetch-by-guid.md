# Lark Direct Task Fetch by GUID

When `lark_task_reader.py --summary` or `fetch_tasks(token)` times out or the target task
is not in the paginated incomplete-task list (e.g., task is completed, or pagination is
too slow for 100+ tasks), use a direct single-task API call instead.

## Pattern

```python
import sys, json, os, requests
sys.path.insert(0, os.path.expanduser("~/.hermes/scripts"))

GUID = "<task-guid-here>"

from lark_task_reader import get_token
token = get_token()

API = "https://open.larksuite.com/open-apis"
headers = {"Authorization": f"Bearer {token}"}

r = requests.get(
    f"{API}/task/v2/tasks/{GUID}",
    headers=headers,
    params={"user_id_type": "open_id"}
)
if r.status_code == 200:
    task = r.json().get("data", {}).get("task", {})
    print(json.dumps(task, ensure_ascii=False, indent=2))
```

## When to use

- `lark_task_reader.py --summary` hangs/times out (common with 150+ tasks)
- You have a specific GUID from a Lark URL or taskpool note
- Task may be completed (the paginated reader defaults to `completed=false`)
- You need the full task object including `attachments`, `members`, `tasklists`

## Key details

- Single-task fetch returns immediately (~1-2s) vs paginated read (30-60s for 170+ tasks)
- Response structure: `data.task` (not `data.items[]`)
- The `task_id` field in the response is the `t104016`-style suite entity ID
- `attachments[].guid` (NOT `file_token`) is the key for downloading task attachments (see below)
- `tasklists[].section_guid` and `tasklist_guid` are available for scope matching
- The `members` array includes `role` (follower/assignee) and `id` (open_id)

## Fallback: search in paginated results

If the direct fetch fails (e.g., permission denied), fall back to the full paginated
fetch and search the list. Use `execute_code` with `requests` directly for pagination
control, since `fetch_tasks()` doesn't expose `page_token` or include completed tasks.

## Attachment download (two-step)

Downloading task-native attachments is a **two-step** process. The first API call returns metadata (JSON), not the file itself.

### Step 1: Get attachment metadata

```python
r = requests.get(f"{API}/task/v2/attachments/{att_guid}", headers=headers)
data = r.json().get("data", {}).get("attachment", {})
download_url = data.get("url", "")
```

The endpoint is `GET /task/v2/attachments/{guid}` where `{guid}` is the attachment's `guid` field from the task payload — NOT the `file_token`. Using `file_token` returns 400: `Invalid Param 'attachment_guid'`.

### Step 2: Download the file from the URL

```python
r2 = requests.get(download_url, headers=headers, stream=True)
# r2.content is the actual file bytes (image/jpeg, etc.)
```

### Pitfall

`GET /task/v2/attachments/{guid}` returns `content-type: application/json` with a JSON body containing a `url` field. Do NOT assume the first response is the file — always check content-type and parse the JSON to extract the download URL.

## Gotcha

`lark_task_reader.py` has no `--task-guid` flag. The standard CLI only supports
`--scope-mode`, `--summary`, and `--download-images`. For single-task fetch, write
a small Python script using the pattern above.
