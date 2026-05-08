#!/usr/bin/env python3
"""Local-brain task orchestrator.

Hermes/Obsidian-native task control plane for ~/Documents/brain.
Markdown task notes are canonical. Dashboards and queue views are derived.
No network, no LLM, no arbitrary hooks.
"""
from __future__ import annotations

import argparse
import dataclasses
import hashlib
import json
import os
import re
import shutil
import sys
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

TZ = timezone(timedelta(hours=8))
VAULT = Path(os.environ.get("HERMES_BRAIN_VAULT", os.environ.get("OBSIDIAN_VAULT_PATH", str(Path.home() / "Documents" / "brain")))).expanduser()
TASKS_DIR = VAULT / "05-实践与项目" / "tasks"
DASHBOARD = VAULT / "07-仪表盘" / "待完成任务运行态.md"
CONTROL_CENTER = VAULT / "07-仪表盘" / "待完成任务控制台.md"
SORTED_POOL = TASKS_DIR / "任务池-排序.md"
INBOX = TASKS_DIR / "任务收件箱.md"
DEFAULT_WORKFLOW = "[[08-模板/task-workflow-contract-template]]"
VALID_STATUSES = ["proposed", "pending", "claimed", "running", "retry", "review", "blocked", "done", "archived", "expired"]
STATUS_ALIASES = {"completed": "done"}  # legacy notes may use completed; normalize as terminal done.
ACTIVE_STATUSES = {"proposed", "pending", "claimed", "running", "retry", "review", "blocked"}
TERMINAL_STATUSES = {"done", "archived", "expired"}
PRIORITY_WEIGHT = {"P0": 400, "P1": 300, "P2": 200, "P3": 100}
STATUS_WEIGHT = {"retry": 60, "running": 50, "claimed": 45, "blocked": 40, "review": 35, "pending": 30, "proposed": 10, "done": -100, "archived": -120, "expired": -130}


def now() -> datetime:
    return datetime.now(TZ).replace(microsecond=0)


def iso(dt: datetime | None = None) -> str:
    return (dt or now()).isoformat()


def parse_dt(value: Any) -> datetime | None:
    if value in (None, "", [], {}):
        return None
    s = str(value).strip().strip('"').strip("'")
    if not s:
        return None
    if s.endswith("Z"):
        s = s[:-1] + "+00:00"
    try:
        if re.fullmatch(r"\d{4}-\d{2}-\d{2}", s):
            return datetime.fromisoformat(s + "T00:00:00+08:00")
        dt = datetime.fromisoformat(s)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=TZ)
        return dt.astimezone(TZ)
    except Exception:
        return None


def slugify(text: str) -> str:
    s = text.strip().lower()
    s = re.sub(r"[`*_~<>\[\](){}:;,'\"!?/\\|]+", " ", s)
    s = re.sub(r"\s+", "-", s).strip("-")
    s = re.sub(r"[^a-z0-9\-\u4e00-\u9fff]+", "", s)
    return s[:80] or "task"


def split_frontmatter(text: str) -> tuple[dict[str, Any], str]:
    if not text.startswith("---\n"):
        return {}, text
    end = text.find("\n---", 4)
    if end < 0:
        return {}, text
    raw = text[4:end]
    body = text[text.find("\n", end + 1) + 1 :]
    return parse_yamlish(raw), body


def parse_yamlish(raw: str) -> dict[str, Any]:
    data: dict[str, Any] = {}
    lines = raw.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i]
        if not line.strip() or line.lstrip().startswith("#"):
            i += 1
            continue
        if ":" not in line or line.startswith(" "):
            i += 1
            continue
        key, val = line.split(":", 1)
        key = key.strip()
        val = val.strip()
        if val == "":
            items: list[str] = []
            j = i + 1
            while j < len(lines) and lines[j].startswith("  - "):
                items.append(lines[j][4:].strip())
                j += 1
            if items:
                data[key] = items
                i = j
                continue
            data[key] = ""
        elif val.startswith("[") and val.endswith("]"):
            inside = val[1:-1].strip()
            data[key] = [] if not inside else [x.strip().strip('"').strip("'") for x in inside.split(",")]
        else:
            data[key] = val.split(" #", 1)[0].strip().strip('"').strip("'")
        i += 1
    return data


def yaml_scalar(v: Any) -> str:
    if v is None:
        return ""
    if isinstance(v, list):
        return "[" + ", ".join(str(x) for x in v) + "]"
    s = str(v)
    if s == "":
        return ""
    if any(ch in s for ch in [": ", "#", "[", "]", "{", "}"]) and not s.startswith("[["):
        return json.dumps(s, ensure_ascii=False)
    return s


def render_frontmatter(fm: dict[str, Any]) -> str:
    preferred = ["type", "layer", "status", "priority", "created", "updated", "expires_at", "project", "workflow_contract", "claimed_by", "claim_expires_at", "run_id", "retry_count", "next_attempt_at", "workspace", "evidence", "concepts"]
    keys = preferred + [k for k in fm.keys() if k not in preferred]
    out = ["---"]
    for k in keys:
        if k not in fm:
            continue
        v = fm[k]
        if isinstance(v, list) and k == "evidence" and v:
            out.append(f"{k}:")
            for item in v:
                out.append(f"  - {item}")
        else:
            out.append(f"{k}: {yaml_scalar(v)}")
    out.append("---")
    return "\n".join(out) + "\n"


def atomic_write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=path.name + ".", dir=str(path.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(text)
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


@dataclasses.dataclass
class Task:
    path: Path
    fm: dict[str, Any]
    body: str

    @property
    def id(self) -> str:
        return self.path.stem

    @property
    def title(self) -> str:
        m = re.search(r"^#\s+(.+)$", self.body, re.M)
        return m.group(1).strip() if m else self.path.stem

    @property
    def status(self) -> str:
        raw = str(self.fm.get("status") or "pending")
        return STATUS_ALIASES.get(raw, raw)

    @property
    def priority(self) -> str:
        return str(self.fm.get("priority") or "P2")

    @property
    def project(self) -> str:
        return str(self.fm.get("project") or "")

    def expires_at(self) -> datetime | None:
        return parse_dt(self.fm.get("expires_at"))

    def claim_expires_at(self) -> datetime | None:
        return parse_dt(self.fm.get("claim_expires_at"))

    def next_attempt_at(self) -> datetime | None:
        return parse_dt(self.fm.get("next_attempt_at"))

    def retry_count(self) -> int:
        try:
            return int(self.fm.get("retry_count") or 0)
        except Exception:
            return 0

    def is_retry_due(self, at: datetime | None = None) -> bool:
        at = at or now()
        nxt = self.next_attempt_at()
        return nxt is None or nxt <= at

    def is_stale_claim(self, at: datetime | None = None) -> bool:
        at = at or now()
        return self.status in {"claimed", "running"} and self.claim_expires_at() is not None and self.claim_expires_at() < at

    def is_expired(self, at: datetime | None = None) -> bool:
        at = at or now()
        return self.status not in TERMINAL_STATUSES and self.expires_at() is not None and self.expires_at() < at

    def score(self, at: datetime | None = None) -> int:
        at = at or now()
        score = PRIORITY_WEIGHT.get(self.priority, 150) + STATUS_WEIGHT.get(self.status, 0)
        exp = self.expires_at()
        if exp:
            days = (exp - at).total_seconds() / 86400
            if days < 0:
                score += 90
            elif days <= 1:
                score += 70
            elif days <= 7:
                score += 40
            elif days <= 30:
                score += 10
        try:
            score += min(int(self.fm.get("retry_count") or 0), 5) * 5
        except Exception:
            pass
        if self.is_stale_claim(at):
            score += 55
        if self.status in TERMINAL_STATUSES:
            score -= 1000
        return score

    def is_dispatchable(self, at: datetime | None = None) -> bool:
        at = at or now()
        if self.status in TERMINAL_STATUSES:
            return False
        if self.is_expired(at):
            return False
        if self.status not in {"proposed", "pending", "retry"}:
            return False
        if self.fm.get("claimed_by") and not self.is_stale_claim(at):
            return False
        if self.status == "retry" and not self.is_retry_due(at):
            return False
        return True

    def row(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "status": self.status,
            "priority": self.priority,
            "score": self.score(),
            "project": self.project,
            "claimed_by": self.fm.get("claimed_by") or "",
            "claim_expires_at": self.fm.get("claim_expires_at") or "",
            "retry_count": self.fm.get("retry_count") or 0,
            "next_attempt_at": self.fm.get("next_attempt_at") or "",
            "expires_at": self.fm.get("expires_at") or "",
            "stale_claim": self.is_stale_claim(),
            "expired": self.is_expired(),
            "dispatchable": self.is_dispatchable(),
            "path": str(self.path),
            "link": obsidian_link(self.path),
        }


def obsidian_link(path: Path) -> str:
    rel = path.relative_to(VAULT).with_suffix("")
    return "[[" + str(rel) + "]]"


def iter_tasks(include_generated: bool = False) -> list[Task]:
    tasks: list[Task] = []
    if not TASKS_DIR.exists():
        return tasks
    skip = {"00-tasks索引.md", "任务收件箱.md", "任务池-排序.md"}
    for path in sorted(TASKS_DIR.glob("*.md")):
        if not include_generated and path.name in skip:
            continue
        text = path.read_text(encoding="utf-8")
        fm, body = split_frontmatter(text)
        if fm.get("type") == "task":
            tasks.append(Task(path, fm, body))
    return tasks


def find_task(task_id: str) -> Task:
    candidates = []
    for t in iter_tasks():
        if t.id == task_id or t.path.name == task_id or str(t.path).endswith(task_id):
            candidates.append(t)
    if not candidates:
        raise SystemExit(f"task not found: {task_id}")
    if len(candidates) > 1:
        raise SystemExit(f"ambiguous task id {task_id}: {[t.id for t in candidates]}")
    return candidates[0]


def save_task(task: Task) -> None:
    atomic_write(task.path, render_frontmatter(task.fm) + "\n" + task.body.lstrip("\n"))


def sorted_tasks(include_done: bool = False) -> list[Task]:
    rows = [t for t in iter_tasks() if include_done or t.status not in TERMINAL_STATUSES]
    return sorted(rows, key=lambda t: (-t.score(), t.expires_at() or datetime.max.replace(tzinfo=TZ), t.priority, t.id))


def dispatchable_tasks() -> list[Task]:
    rows = [t for t in iter_tasks() if t.is_dispatchable()]
    return sorted(rows, key=lambda t: (-t.score(), t.expires_at() or datetime.max.replace(tzinfo=TZ), t.priority, t.id))


def evidence_is_structured(e: str) -> bool:
    e = (e or "").strip()
    if not e:
        return False
    if e.startswith(("command:", "file:", "search:", "brainctl:", "url:", "artifact:")):
        return True
    if e.startswith("/") or e.startswith("~"):
        return Path(e).expanduser().exists()
    return False


def body_has_legacy_proof(body: str) -> bool:
    proof_markers = ["## Proof Log", "## Final verification bundle", "## Final Verification", "## Evidence Boundary"]
    evidence_markers = ["`python", "`brainctl", "exit 0", "passed=true", "tests OK", "OK.", "status `certified`"]
    return any(m in body for m in proof_markers) and any(m in body for m in evidence_markers)


def command_list(args: argparse.Namespace) -> dict[str, Any]:
    rows = [t.row() for t in sorted_tasks(include_done=args.include_done)]
    return {"status": "OK", "generated_at": iso(), "task_count": len(rows), "rows": rows}


def command_add(args: argparse.Namespace) -> dict[str, Any]:
    title = args.title.strip()
    created = now()
    expires = parse_dt(args.expires_at) if args.expires_at else created + timedelta(days=args.expires_days)
    slug = slugify(title)
    base = TASKS_DIR / f"{created.date().isoformat()}-{slug}.md"
    path = base
    i = 2
    while path.exists():
        path = TASKS_DIR / f"{created.date().isoformat()}-{slug}-{i}.md"
        i += 1
    concepts = [x.strip() for x in (args.concepts or "task").split(",") if x.strip()]
    fm = {
        "type": "task",
        "layer": args.layer,
        "status": args.status,
        "priority": args.priority,
        "created": iso(created),
        "updated": iso(created),
        "expires_at": iso(expires) if expires else "",
        "project": args.project,
        "workflow_contract": args.workflow_contract,
        "claimed_by": "",
        "claim_expires_at": "",
        "run_id": "",
        "retry_count": 0,
        "next_attempt_at": "",
        "workspace": args.workspace or "",
        "evidence": [],
        "concepts": concepts,
    }
    body = f"# Task - {title}\n\n## Objective\n\n{args.objective or title}\n\n## Acceptance Criteria\n\n- [ ] {args.accept or 'Observable result is recorded in Proof Log.'}\n\n## Plan / Workpad\n\n- [ ] Reconcile current state before execution.\n- [ ] Execute the smallest verifiable slice.\n- [ ] Record proof and update status.\n\n## Validation\n\n| Command / Check | Status | Evidence |\n|---|---|---|\n| brain_task_orchestrator list | pending | |\n\n## Proof Log\n\n- {iso(created)}: Task created from local-brain control point.\n\n## Blockers / Confusions\n\n- None.\n\n## Final Handoff\n\n- Status:\n- Evidence:\n- Residual risk:\n"
    atomic_write(path, render_frontmatter(fm) + "\n" + body)
    return {"status": "OK", "created": str(path), "id": path.stem, "link": obsidian_link(path)}


def parse_inbox_line(line: str) -> dict[str, Any] | None:
    m = re.match(r"^\s*- \[ \]\s+(.+?)\s*$", line)
    if not m:
        return None
    raw = m.group(1).strip()
    if "<!-- ingested:" in raw:
        return None
    parts = [p.strip() for p in raw.split("|")]
    title = parts[0]
    meta = {"title": title, "priority": "P2", "project": "inbox", "concepts": "task,inbox", "expires_at": "", "objective": title}
    for p in parts[1:]:
        if ":" not in p:
            continue
        k, v = p.split(":", 1)
        k = k.strip().lower()
        v = v.strip()
        if k in {"priority", "project", "concepts", "expires_at", "objective"}:
            meta[k] = v
        elif k in {"expires", "due"}:
            meta["expires_at"] = v
    return meta


def ensure_inbox() -> None:
    if INBOX.exists():
        return
    text = f"""---
type: task_inbox
status: active
derived: false
created: {iso()}
concepts: [task-inbox, obsidian-trigger, local-brain-ui]
---

# 任务收件箱

在 Obsidian 本地大脑界面直接追加下面这种 unchecked bullet，然后让 Hermes 执行“处理本地大脑任务收件箱”，或在终端运行：

```bash
python3 ~/.hermes/scripts/brain_task_orchestrator.py ingest-inbox --write
python3 ~/.hermes/scripts/brain_task_orchestrator.py dashboard --write
```

格式：

```markdown
- [ ] 任务标题 | priority:P1 | project:project-slug | due:2026-05-20 | concepts:task,tag
```

## Inbox Drafts

<!-- Add real unchecked task bullets here. Example syntax only:
- [ ] 整理本周本地大脑任务 | priority:P2 | project:local-brain | due:2099-01-01 | concepts:task,inbox-example
-->

## Ingested Log

"""
    atomic_write(INBOX, text)


def command_ingest_inbox(args: argparse.Namespace) -> dict[str, Any]:
    ensure_inbox()
    lines = INBOX.read_text(encoding="utf-8").splitlines()
    created = []
    new_lines = []
    in_drafts = False
    in_fence = False
    in_html_comment = False
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("<!--"):
            in_html_comment = True
            new_lines.append(line)
            if "-->" in stripped:
                in_html_comment = False
            continue
        if in_html_comment:
            new_lines.append(line)
            if "-->" in stripped:
                in_html_comment = False
            continue
        if stripped.startswith("```"):
            in_fence = not in_fence
            new_lines.append(line)
            continue
        if stripped.startswith("## "):
            in_drafts = stripped == "## Inbox Drafts"
            new_lines.append(line)
            continue
        if not in_drafts or in_fence:
            new_lines.append(line)
            continue
        meta = parse_inbox_line(line)
        if not meta:
            new_lines.append(line)
            continue
        ns = argparse.Namespace(
            title=meta["title"], priority=meta.get("priority", "P2"), project=meta.get("project", "inbox"), status="pending",
            expires_at=meta.get("expires_at") or "", expires_days=args.expires_days, concepts=meta.get("concepts", "task,inbox"),
            layer="L3", workflow_contract=DEFAULT_WORKFLOW, workspace="", objective=meta.get("objective") or meta["title"], accept="Task has proof log and terminal status."
        )
        result = command_add(ns) if args.write else {"id": slugify(meta["title"]), "link": "dry-run"}
        created.append(result)
        suffix = f" <!-- ingested: {result.get('link', result.get('id'))} -->"
        new_lines.append(line.replace("- [ ]", "- [x]", 1) + suffix if args.write else line)
    if args.write and created:
        atomic_write(INBOX, "\n".join(new_lines) + "\n")
    return {"status": "OK", "write": bool(args.write), "created_count": len(created), "created": created, "inbox": str(INBOX)}


def command_claim(args: argparse.Namespace) -> dict[str, Any]:
    t = find_task(args.task)
    if t.status in TERMINAL_STATUSES:
        raise SystemExit(f"cannot claim terminal task: {t.id} status={t.status}")
    active_claim = t.fm.get("claimed_by") and not t.is_stale_claim()
    if active_claim and not args.force:
        raise SystemExit(f"task already claimed by {t.fm.get('claimed_by')} until {t.fm.get('claim_expires_at')}; use --force only after manual review")
    stamp = now()
    t.fm["status"] = "claimed"
    t.fm["claimed_by"] = args.actor
    t.fm["claim_expires_at"] = iso(stamp + timedelta(minutes=args.ttl_minutes))
    t.fm["run_id"] = args.run_id or f"{args.actor}-{stamp.strftime('%Y%m%d%H%M%S')}"
    t.fm["updated"] = iso(stamp)
    t.body += f"\n- {iso(stamp)}: Claimed by `{args.actor}` until `{t.fm['claim_expires_at']}`.\n"
    save_task(t)
    return {"status": "OK", "task": t.id, "claimed_by": args.actor, "claim_expires_at": t.fm["claim_expires_at"], "path": str(t.path)}


def command_release(args: argparse.Namespace) -> dict[str, Any]:
    t = find_task(args.task)
    owner = t.fm.get("claimed_by") or ""
    if owner and owner != args.actor and not args.force:
        raise SystemExit(f"task claimed by {owner}; {args.actor} cannot release without --force")
    stamp = now()
    t.fm["status"] = args.to_status
    t.fm["claimed_by"] = ""
    t.fm["claim_expires_at"] = ""
    t.fm["run_id"] = ""
    t.fm["updated"] = iso(stamp)
    t.body += f"\n- {iso(stamp)}: Released by `{args.actor}` to `{args.to_status}`.\n"
    save_task(t)
    return {"status": "OK", "task": t.id, "to_status": args.to_status, "path": str(t.path)}


def command_done(args: argparse.Namespace) -> dict[str, Any]:
    t = find_task(args.task)
    if not args.evidence:
        raise SystemExit("done requires at least one structured --evidence entry, e.g. 'command: pytest PASS' or 'file:/path/to/proof.md'")
    invalid = [e for e in args.evidence if not evidence_is_structured(e)]
    if invalid:
        raise SystemExit(f"invalid evidence shape: {invalid}; use command:/file:/search:/brainctl:/artifact:/url: prefixes or an existing absolute path")
    stamp = now()
    evidence = t.fm.get("evidence") if isinstance(t.fm.get("evidence"), list) else []
    for e in args.evidence or []:
        if e not in evidence:
            evidence.append(e)
    t.fm.update({"status": "done", "claimed_by": "", "claim_expires_at": "", "run_id": "", "updated": iso(stamp), "evidence": evidence})
    t.body += f"\n- {iso(stamp)}: Marked done by `{args.actor}`. Evidence: {', '.join(args.evidence)}.\n"
    save_task(t)
    return {"status": "OK", "task": t.id, "path": str(t.path), "evidence_count": len(evidence)}


def command_retry(args: argparse.Namespace) -> dict[str, Any]:
    t = find_task(args.task)
    stamp = now()
    try:
        retry_count = int(t.fm.get("retry_count") or 0) + 1
    except Exception:
        retry_count = 1
    t.fm.update({
        "status": "retry",
        "claimed_by": "",
        "claim_expires_at": "",
        "run_id": "",
        "retry_count": retry_count,
        "next_attempt_at": iso(stamp + timedelta(minutes=args.delay_minutes)),
        "updated": iso(stamp),
    })
    t.body += f"\n- {iso(stamp)}: Retry scheduled by `{args.actor}` at `{t.fm['next_attempt_at']}`. Reason: {args.reason}\n"
    save_task(t)
    return {"status": "OK", "task": t.id, "retry_count": retry_count, "next_attempt_at": t.fm["next_attempt_at"], "path": str(t.path)}


def counts(rows: list[Task]) -> dict[str, int]:
    out = {s: 0 for s in VALID_STATUSES}
    for t in rows:
        out[t.status] = out.get(t.status, 0) + 1
    return out


def render_dashboard() -> tuple[str, str]:
    tasks = sorted_tasks(include_done=False)
    all_tasks = iter_tasks()
    c = counts(all_tasks)
    stamp = iso()
    top_rows = tasks[:25]
    table = ["| Rank | Score | Priority | Status | Task | Project | Lease / Due |", "|---:|---:|---|---|---|---|---|"]
    for i, t in enumerate(top_rows, 1):
        due = t.fm.get("expires_at") or ""
        lease = t.fm.get("claim_expires_at") or ""
        marker = "stale lease" if t.is_stale_claim() else ("expired" if t.is_expired() else "")
        table.append(f"| {i} | {t.score()} | {t.priority} | {t.status} | {obsidian_link(t.path)} | {t.project} | {marker or lease or due} |")
    table_text = "\n".join(table)
    dashboard = f"""---
type: dashboard
status: active
derived: true
generated_by: brain_task_orchestrator.py
generated_at: {stamp}
concepts: [task-runtime-dashboard, derived-view, not-source-of-truth]
---

# 待完成任务运行态

DERIVED VIEW — NOT SOURCE OF TRUTH.

事实源：`~/Documents/brain/05-实践与项目/tasks/*.md` frontmatter。此页由 `brain_task_orchestrator.py dashboard --write` 重建，人工编辑不改变任务真实状态。

## Contract

```json
{{
  "dashboard": "local-brain-task-runtime",
  "source_of_truth": "05-实践与项目/tasks/*.md",
  "derived": true,
  "regenerate_command": "python3 ~/.hermes/scripts/brain_task_orchestrator.py dashboard --write",
  "states": {json.dumps(VALID_STATUSES, ensure_ascii=False)},
  "must_reconcile_before_dispatch": true,
  "safe_dispatch_tick": "python3 ~/.hermes/scripts/brain_task_dispatch_tick.py",
  "skill_route_matrix": "[[07-仪表盘/Agent技能树路由矩阵]]"
}}
```

## Interaction Trigger Points

- 打开控制台：[[07-仪表盘/待完成任务控制台]]
- 在 Obsidian 添加任务草稿：[[05-实践与项目/tasks/任务收件箱]]
- 处理收件箱：对 Hermes 说“处理本地大脑任务收件箱”，或运行 `python3 ~/.hermes/scripts/brain_task_orchestrator.py ingest-inbox --write && python3 ~/.hermes/scripts/brain_task_orchestrator.py dashboard --write`
- 直接创建任务：`python3 ~/.hermes/scripts/brain_task_orchestrator.py add "任务标题" --priority P1 --project local-brain`
- 技能路由入口：[[07-仪表盘/Agent技能树路由矩阵]]
- 安全派发 tick：`python3 ~/.hermes/scripts/brain_task_dispatch_tick.py --print-always`

## Counts

| Status | Count |
|---|---:|
"""
    for s in VALID_STATUSES:
        dashboard += f"| {s} | {c.get(s, 0)} |\n"
    dashboard += f"""

## Sorted Active Task Pool

{table_text}

## Safety Invariants

- Markdown task notes are canonical.
- This dashboard and `任务池-排序.md` are derived views.
- Claim before work; release/archive after proof.
- Reconcile stale leases before dispatch.
- `done` requires structured evidence (`command:`, `file:`, `search:`, `brainctl:`, `artifact:`, `url:`).
- No arbitrary shell hooks from Markdown.

## Search Aliases

待完成任务运行态 本地大脑任务队列 派生视图 not source of truth derived dashboard claim lease retry stale reconcile before dispatch task inbox trigger point
"""
    pool = f"""---
type: derived_task_pool
status: active
derived: true
generated_by: brain_task_orchestrator.py
generated_at: {stamp}
concepts: [task-pool, sorted-queue, derived-view]
---

# 任务池-排序

DERIVED VIEW — NOT SOURCE OF TRUTH. Edit task notes, not this sorted pool.

{table_text}
"""
    return dashboard, pool


def render_control_center() -> str:
    stamp = iso()
    return f"""---
type: dashboard
status: active
derived: false
created: {stamp}
updated: {stamp}
concepts: [local-brain-task-console, obsidian-trigger, task-inbox]
---

# 待完成任务控制台

这是用户在本地大脑界面交互的入口。它不是任务事实源；任务事实源仍是 `05-实践与项目/tasks/*.md` 的 frontmatter。

## 1. 添加任务：Obsidian UI 触发点

打开 [[05-实践与项目/tasks/任务收件箱]]，在 `Inbox Drafts` 下添加一行：

```markdown
- [ ] 任务标题 | priority:P1 | project:project-slug | due:2026-05-20 | concepts:task,tag
```

然后任选一种触发方式：

1. 对 Hermes 说：`处理本地大脑任务收件箱`。
2. 终端运行：

```bash
python3 ~/.hermes/scripts/brain_task_orchestrator.py ingest-inbox --write
python3 ~/.hermes/scripts/brain_task_orchestrator.py dashboard --write
python3 ~/.hermes/scripts/brainctl.py --json sync
python3 ~/.hermes/scripts/brainctl.py --json reindex
```

## 2. 查看任务池

- 运行态 Dashboard：[[07-仪表盘/待完成任务运行态]]
- 排序任务池：[[05-实践与项目/tasks/任务池-排序]]
- JSON 队列：

```bash
python3 ~/.hermes/scripts/brain_task_orchestrator.py list --json
```

## 3. 状态操作触发点

```bash
# 创建任务
python3 ~/.hermes/scripts/brain_task_orchestrator.py add "任务标题" --priority P1 --project local-brain

# 对 stale lease / expired / due retry 做调和
python3 ~/.hermes/scripts/brain_task_orchestrator.py reconcile --write --json

# 查看下一项可派发任务，不改文件
python3 ~/.hermes/scripts/brain_task_orchestrator.py next --json

# 生成安全派发 dry-run，不认领、不执行
python3 ~/.hermes/scripts/brain_task_orchestrator.py dispatch-dry-run --json

# 安全 tick：收件箱 ingest + reconcile + dashboard + dispatch hint
python3 ~/.hermes/scripts/brain_task_dispatch_tick.py --print-always

# 认领任务，生成 lease
python3 ~/.hermes/scripts/brain_task_orchestrator.py claim TASK_ID --actor hermes --ttl-minutes 60

# 释放任务
python3 ~/.hermes/scripts/brain_task_orchestrator.py release TASK_ID --actor hermes --to-status pending

# 标记完成：必须给结构化 evidence
python3 ~/.hermes/scripts/brain_task_orchestrator.py done TASK_ID --actor hermes --evidence "command:验证命令 PASS" --evidence "file:/path/to/proof.md"

# 检查 done 任务是否有结构化 proof
python3 ~/.hermes/scripts/brain_task_orchestrator.py proof-check --json

# 进入 retry
python3 ~/.hermes/scripts/brain_task_orchestrator.py retry TASK_ID --actor hermes --reason "失败原因" --delay-minutes 60
```

## 4. 多模型分解触发点

当任务过大、跨层级、影响事实源或需要排序取舍时，对 Hermes 说：

- `多模型分解本地大脑任务池并排序`
- `pua-loop 多模型思考推进本地大脑任务池`
- `处理本地大脑任务收件箱，然后多模型拆解 P0/P1/P2`

多模型只做分解、质疑、排序、认证；事实更新仍落回 Markdown task note / review / dashboard。

## 5. 排序规则

排序分数 = priority 权重 + status 权重 + 到期紧迫度 + retry 次数 + stale lease 补偿。

- P0 > P1 > P2 > P3
- retry/running/claimed/pending 优先于 proposed
- 临近 `expires_at` 或 stale `claim_expires_at` 自动上浮
- terminal 状态不进入默认 active pool

## 5. 安全边界

- Markdown task note 是事实源。
- Dashboard / sorted pool 是 derived view。
- Workflow contract 中的 hooks 默认 inert；没有 allowlisted runner 不执行。
- 自动执行任务前必须先 claim，结束必须 release/done/retry 并写 proof。
- 长期闭环必须经过 [[07-仪表盘/Agent技能树路由矩阵]] 选择 skills，不能凭感觉调度。
"""


def command_reconcile(args: argparse.Namespace) -> dict[str, Any]:
    stamp = now()
    actions: list[dict[str, Any]] = []
    for t in iter_tasks():
        before = dict(t.fm)
        action = None
        if t.is_expired(stamp):
            t.fm.update({"status": "expired", "claimed_by": "", "claim_expires_at": "", "run_id": "", "updated": iso(stamp)})
            action = "expired"
        elif t.is_stale_claim(stamp):
            if t.status == "running":
                retry_count = t.retry_count() + 1
                if retry_count > args.max_retries:
                    t.fm.update({"status": args.over_retry_status, "claimed_by": "", "claim_expires_at": "", "run_id": "", "updated": iso(stamp), "retry_count": retry_count})
                    action = "stale_running_over_retry"
                else:
                    t.fm.update({"status": "retry", "claimed_by": "", "claim_expires_at": "", "run_id": "", "next_attempt_at": iso(stamp + timedelta(minutes=args.retry_delay_minutes)), "updated": iso(stamp), "retry_count": retry_count})
                    action = "stale_running_retry"
            else:
                t.fm.update({"status": args.stale_claim_status, "claimed_by": "", "claim_expires_at": "", "run_id": "", "updated": iso(stamp)})
                action = "stale_claim_released"
        elif t.status == "retry" and t.is_retry_due(stamp) and args.promote_due_retry:
            t.fm.update({"status": "pending", "next_attempt_at": "", "updated": iso(stamp)})
            action = "retry_due_promoted"
        if action:
            t.body += f"\n- {iso(stamp)}: Reconcile action `{action}` by `{args.actor}`. Previous status `{before.get('status')}`.\n"
            if args.write:
                save_task(t)
            actions.append({"task": t.id, "action": action, "write": bool(args.write), "path": str(t.path)})
    return {"status": "OK", "write": bool(args.write), "action_count": len(actions), "actions": actions}


def command_proof_check(args: argparse.Namespace) -> dict[str, Any]:
    failures: list[str] = []
    warnings: list[str] = []
    checked = 0
    legacy_body_evidence: list[str] = []
    for t in iter_tasks():
        if t.status != "done" and not args.include_active:
            continue
        checked += 1
        evidence = t.fm.get("evidence") if isinstance(t.fm.get("evidence"), list) else []
        has_evidence = bool(evidence)
        if not has_evidence and body_has_legacy_proof(t.body):
            has_evidence = True
            legacy_body_evidence.append(t.id)
            warnings.append(f"legacy body-only evidence accepted: {t.id}")
        if t.status == "done" and not has_evidence:
            failures.append(f"done task missing evidence: {t.id}")
        for e in evidence:
            if not evidence_is_structured(str(e)):
                failures.append(f"unstructured evidence in {t.id}: {e}")
        if "## Proof Log" not in t.body and "## Final verification bundle" not in t.body:
            warnings.append(f"missing Proof Log section: {t.id}")
        if "## Final Handoff" not in t.body and not body_has_legacy_proof(t.body):
            warnings.append(f"missing Final Handoff section: {t.id}")
    status = "PASS" if not failures else "FAIL"
    return {"status": status, "checked_count": checked, "failures": failures, "warnings": warnings, "legacy_body_evidence": legacy_body_evidence}


def command_next(args: argparse.Namespace) -> dict[str, Any]:
    if getattr(args, "reconcile", False):
        command_reconcile(argparse.Namespace(write=True, actor="next", max_retries=3, retry_delay_minutes=60, stale_claim_status="pending", over_retry_status="blocked", promote_due_retry=True))
    rows = dispatchable_tasks()
    if not rows:
        return {"status": "OK", "next": None, "message": "No dispatchable local-brain tasks in canonical task notes."}
    t = rows[0]
    return {"status": "OK", "next": t.row(), "claim_command": f"python3 ~/.hermes/scripts/brain_task_orchestrator.py claim {t.id} --actor hermes --ttl-minutes 60", "dashboard_command": "python3 ~/.hermes/scripts/brain_task_orchestrator.py dashboard --write"}


def command_dispatch_dry_run(args: argparse.Namespace) -> dict[str, Any]:
    nxt = command_next(args)
    if not nxt.get("next"):
        return {"status": "OK", "dry_run": True, "dispatchable": False, "message": nxt["message"]}
    row = nxt["next"]
    prompt = (
        "Execute this local-brain task only after claiming it. "
        "Treat the task note as canonical workpad; reconcile first; verify; record proof; release/done/retry. "
        f"Task: {row['link']} ({row['id']}) priority={row['priority']} status={row['status']} project={row['project']}"
    )
    return {"status": "OK", "dry_run": True, "dispatchable": True, "next": row, "claim_command": nxt["claim_command"], "execution_prompt": prompt, "safety": "dry-run only; does not claim or execute"}


def command_dashboard(args: argparse.Namespace) -> dict[str, Any]:
    ensure_inbox()
    dashboard, pool = render_dashboard()
    control = render_control_center()
    if args.write:
        atomic_write(DASHBOARD, dashboard)
        atomic_write(SORTED_POOL, pool)
        atomic_write(CONTROL_CENTER, control)
    return {"status": "OK", "write": bool(args.write), "dashboard": str(DASHBOARD), "sorted_pool": str(SORTED_POOL), "control_center": str(CONTROL_CENTER), "active_count": len(sorted_tasks())}


def command_selfcheck(args: argparse.Namespace) -> dict[str, Any]:
    failures = []
    warnings = []
    required = [TASKS_DIR, DASHBOARD, CONTROL_CENTER, SORTED_POOL, INBOX]
    for p in required:
        if not p.exists():
            failures.append(f"missing required path: {p}")
    for t in iter_tasks():
        if t.status not in VALID_STATUSES:
            failures.append(f"invalid status {t.status}: {t.path}")
        if t.priority not in PRIORITY_WEIGHT:
            warnings.append(f"unknown priority {t.priority}: {t.path}")
        if t.status in {"claimed", "running"} and not t.fm.get("claim_expires_at"):
            failures.append(f"active claim missing claim_expires_at: {t.path}")
        if t.status not in TERMINAL_STATUSES and not t.fm.get("expires_at"):
            warnings.append(f"active task missing expires_at: {t.path}")
    if DASHBOARD.exists() and "DERIVED VIEW — NOT SOURCE OF TRUTH" not in DASHBOARD.read_text(encoding="utf-8"):
        failures.append("dashboard missing derived-view warning")
    if CONTROL_CENTER.exists() and "处理本地大脑任务收件箱" not in CONTROL_CENTER.read_text(encoding="utf-8"):
        failures.append("control center missing natural-language trigger")
    status = "PASS" if not failures else "FAIL"
    return {"status": status, "task_count": len(iter_tasks()), "failures": failures, "warnings": warnings, "paths": {"dashboard": str(DASHBOARD), "control_center": str(CONTROL_CENTER), "sorted_pool": str(SORTED_POOL), "inbox": str(INBOX)}}


def print_result(result: dict[str, Any], as_json: bool) -> int:
    if as_json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(result.get("status", "OK"))
        for k, v in result.items():
            if k != "status":
                print(f"{k}: {v}")
    return 0 if result.get("status") in {"OK", "PASS"} else 2


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Local-brain Markdown task orchestrator")
    sub = p.add_subparsers(dest="cmd", required=True)
    lp = sub.add_parser("list")
    lp.add_argument("--include-done", action="store_true")
    lp.add_argument("--json", action="store_true")

    ap = sub.add_parser("add")
    ap.add_argument("title")
    ap.add_argument("--priority", default="P2", choices=list(PRIORITY_WEIGHT))
    ap.add_argument("--project", default="inbox")
    ap.add_argument("--status", default="pending", choices=VALID_STATUSES)
    ap.add_argument("--expires-at", default="")
    ap.add_argument("--expires-days", type=int, default=30)
    ap.add_argument("--concepts", default="task")
    ap.add_argument("--layer", default="L3")
    ap.add_argument("--workflow-contract", default=DEFAULT_WORKFLOW)
    ap.add_argument("--workspace", default="")
    ap.add_argument("--objective", default="")
    ap.add_argument("--accept", default="")
    ap.add_argument("--json", action="store_true")

    ip = sub.add_parser("ingest-inbox")
    ip.add_argument("--write", action="store_true")
    ip.add_argument("--expires-days", type=int, default=30)
    ip.add_argument("--json", action="store_true")

    recp = sub.add_parser("reconcile")
    recp.add_argument("--write", action="store_true")
    recp.add_argument("--actor", default="hermes-reconcile")
    recp.add_argument("--max-retries", type=int, default=3)
    recp.add_argument("--retry-delay-minutes", type=int, default=60)
    recp.add_argument("--stale-claim-status", default="pending", choices=VALID_STATUSES)
    recp.add_argument("--over-retry-status", default="blocked", choices=VALID_STATUSES)
    recp.add_argument("--promote-due-retry", action="store_true")
    recp.add_argument("--json", action="store_true")

    cp = sub.add_parser("claim")
    cp.add_argument("task")
    cp.add_argument("--actor", default="hermes")
    cp.add_argument("--ttl-minutes", type=int, default=60)
    cp.add_argument("--run-id", default="")
    cp.add_argument("--force", action="store_true")
    cp.add_argument("--json", action="store_true")

    rp = sub.add_parser("release")
    rp.add_argument("task")
    rp.add_argument("--actor", default="hermes")
    rp.add_argument("--to-status", default="pending", choices=VALID_STATUSES)
    rp.add_argument("--force", action="store_true")
    rp.add_argument("--json", action="store_true")

    dp = sub.add_parser("done")
    dp.add_argument("task")
    dp.add_argument("--actor", default="hermes")
    dp.add_argument("--evidence", action="append", default=[])
    dp.add_argument("--json", action="store_true")

    pcp = sub.add_parser("proof-check")
    pcp.add_argument("--include-active", action="store_true")
    pcp.add_argument("--json", action="store_true")

    rtp = sub.add_parser("retry")
    rtp.add_argument("task")
    rtp.add_argument("--actor", default="hermes")
    rtp.add_argument("--reason", default="not specified")
    rtp.add_argument("--delay-minutes", type=int, default=60)
    rtp.add_argument("--json", action="store_true")

    gp = sub.add_parser("dashboard")
    gp.add_argument("--write", action="store_true")
    gp.add_argument("--json", action="store_true")

    np = sub.add_parser("next")
    np.add_argument("--reconcile", action="store_true")
    np.add_argument("--json", action="store_true")

    ddp = sub.add_parser("dispatch-dry-run")
    ddp.add_argument("--json", action="store_true")

    sp = sub.add_parser("selfcheck")
    sp.add_argument("--json", action="store_true")
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.cmd == "list":
        return print_result(command_list(args), args.json)
    if args.cmd == "add":
        return print_result(command_add(args), args.json)
    if args.cmd == "ingest-inbox":
        return print_result(command_ingest_inbox(args), args.json)
    if args.cmd == "reconcile":
        return print_result(command_reconcile(args), args.json)
    if args.cmd == "claim":
        return print_result(command_claim(args), args.json)
    if args.cmd == "release":
        return print_result(command_release(args), args.json)
    if args.cmd == "done":
        return print_result(command_done(args), args.json)
    if args.cmd == "proof-check":
        return print_result(command_proof_check(args), args.json)
    if args.cmd == "retry":
        return print_result(command_retry(args), args.json)
    if args.cmd == "dashboard":
        return print_result(command_dashboard(args), args.json)
    if args.cmd == "next":
        return print_result(command_next(args), args.json)
    if args.cmd == "dispatch-dry-run":
        return print_result(command_dispatch_dry_run(args), args.json)
    if args.cmd == "selfcheck":
        return print_result(command_selfcheck(args), args.json)
    raise SystemExit(2)


if __name__ == "__main__":
    sys.exit(main())
