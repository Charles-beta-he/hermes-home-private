# Lark Task API v2 — Task Update and Batch Closeout

## Updating task description (PATCH)

The Lark Task API v2 uses `PATCH /task/v2/tasks/{guid}` with a **wrapped** `task` object:

```python
body = json.dumps({
    "task": {"description": "evidence text here"},
    "update_fields": ["description"]
}).encode("utf-8")

url = f"https://open.larksuite.com/open-apis/task/v2/tasks/{guid}"
req = urllib.request.Request(url, data=body, method="PATCH")
req.add_header("Authorization", f"Bearer {token}")
req.add_header("Content-Type", "application/json")
```

**Critical**: the `task` wrapper is required. Sending `{"description": "...", "update_fields": [...]}` without the wrapper returns `400: Invalid Param 'task', must not be empty`.

## Comments API — Larksuite international shape

For Larksuite international, `POST /task/v2/tasks/{task_id}/comments` returns **404 Not Found**.

Use the flat comments endpoint instead with a user access token that includes `task:comment:write`:

```python
body = json.dumps({
    "resource_id": guid,
    "resource_type": "task",
    "content": evidence_text,
}).encode("utf-8")

req = urllib.request.Request(
    "https://open.larksuite.com/open-apis/task/v2/comments",
    data=body,
    method="POST",
)
req.add_header("Authorization", f"Bearer {user_token}")
req.add_header("Content-Type", "application/json")
```

Readback uses `GET /task/v2/comments?resource_id={guid}&resource_type=task&page_size=50`.

Rendering and evidence pitfalls found in Lark Task closeout:
- Do not treat local paths such as `/tmp/...` as evidence for Lark reviewers; upload evidence into Lark or provide a shared Drive/Doc link.
- If screenshots exist, prefer Task attachments: `POST /task/v2/attachments/upload?user_id_type=open_id` with `multipart/form-data`, fields `resource_type=task`, `resource_id=<task_guid>`, and one or more repeated `file` parts. One request supports up to 5 files, each <=50MB.
- Attachment upload requires user OAuth scope `task:attachment:write` (or `task:attachment:upload` where available) plus edit permission on the task. If the current user token lacks it, force re-OAuth; merely having `task:comment:write` is insufficient.
- Upload attachments by task relevance, not by dumping the whole regression directory onto every task. Map each task summary/page/feature to the minimal relevant screenshot set, delete irrelevant prior attachments if needed, then upload only that task's evidence.
- Verify with `GET /task/v2/attachments?resource_id=<guid>&resource_type=task&page_size=100`; expected task-specific screenshot filenames must be present and unrelated screenshots should be absent.
- Lark Task UI may render API-written `\n` as a dense paragraph. Keep the closeout comment concise and rely on uploaded task-specific attachments for visual evidence.
- If bad dense/local-path comments were already written, delete or patch them before adding the corrected closeout comment and attachments; otherwise the UI looks duplicated and noisy.

Fallback: if comment write is unavailable, use the `description` field for evidence. This is visible in the task detail page and persists across sessions, but it requires `task:task:write` and user identity permission on the task.

## Batch closeout pattern

```python
#!/usr/bin/env python3
"""Batch update Lark task descriptions with evidence."""
import sys, json, urllib.request
sys.path.insert(0, "/Users/charles/.hermes/scripts")
from lark_task_reader import get_token, LarkClient

token = get_token()
client = LarkClient()

CLOSED_TASKS = {
    "guid-prefix-8": "✅ 已完成 | evidence summary | commit hash | test results",
    # ... more tasks
}

data = client.get("/task/v2/tasks", token, {"page_size": "50"})
items = data.get("data", {}).get("items", [])

for item in items:
    guid = item.get("guid", "")
    for guid_prefix, evidence in CLOSED_TASKS.items():
        if guid_prefix in guid:
            body = json.dumps({
                "task": {"description": evidence},
                "update_fields": ["description"]
            }).encode("utf-8")
            url = f"https://open.larksuite.com/open-apis/task/v2/tasks/{guid}"
            req = urllib.request.Request(url, data=body, method="PATCH")
            req.add_header("Authorization", f"Bearer {token}")
            req.add_header("Content-Type", "application/json")
            with urllib.request.urlopen(req, timeout=20) as resp:
                result = json.loads(resp.read())
                print(f"{'✅' if result.get('code')==0 else '❌'} {guid_prefix}")
            break
```

## Task fields available

Each task from `/task/v2/tasks` contains:
- `guid`: UUID — used for PATCH URL
- `task_id`: e.g. `t103374` — internal ID
- `summary`: task title
- `description`: task body (updatable via PATCH)
- `status`: `todo` | `done` etc.
- `completed_at`: timestamp or `"0"` if not completed
- `tasklists[]`: `{tasklist_guid, section_guid}`
- `members[]`: `{id, role, type}`
- `url`: deep link to task in Lark app

## Skipping already-updated tasks

Before batch-updating, check if `description` already contains evidence markers (`✅` or `🔶`). Skip those to avoid overwriting previous closeout evidence.
