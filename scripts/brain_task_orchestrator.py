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
import importlib.util
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
AUTORUN_ENV_FLAG = "HERMES_LOCAL_BRAIN_AUTORUN"
AUTORUN_STATE_DIR = Path(os.environ.get("HERMES_BRAIN_AUTORUN_STATE_DIR", str(Path.home() / ".hermes" / "state"))).expanduser()
AUTORUN_ALLOWLIST = AUTORUN_STATE_DIR / "auto_run_allowlist.json"
AUTORUN_POLICY = AUTORUN_STATE_DIR / "auto_run_policy.json"
AUTORUN_KILL_SWITCH = AUTORUN_STATE_DIR / "auto_run_kill_switch"
AUTORUN_PROOF_LOG = AUTORUN_STATE_DIR / "auto_run_proof.jsonl"
AUTORUN_HANDOFF_DIR = AUTORUN_STATE_DIR / "auto_run_handoffs"
HERMES_HOME = Path(os.environ.get("HERMES_HOME", str(Path.home() / ".hermes"))).expanduser()
AUTONOMY_WRITE_GUARD = HERMES_HOME / "scripts" / "autonomy-write-guard.py"
AUTONOMY_WRITE_ALLOWLIST = Path(
    os.environ.get("HERMES_AUTONOMY_WRITE_ALLOWLIST", str(HERMES_HOME / "config" / "autonomy-write-allowlist.json"))
).expanduser()
VALID_STATUSES = ["proposed", "pending", "claimed", "running", "retry", "review", "blocked", "done", "archived", "expired"]
STATUS_ALIASES = {"completed": "done"}  # legacy notes may use completed; normalize as terminal done.
ACTIVE_STATUSES = {"proposed", "pending", "claimed", "running", "retry", "review", "blocked"}
TERMINAL_STATUSES = {"done", "archived", "expired"}
PRIORITY_WEIGHT = {"P0": 400, "P1": 300, "P2": 200, "P3": 100}
STATUS_WEIGHT = {"retry": 60, "running": 50, "claimed": 45, "blocked": 40, "review": 35, "pending": 30, "proposed": 10, "done": -100, "archived": -120, "expired": -130}
VALID_LANES = ["work", "evolution", "advisory"]
LANE_SORT_WEIGHT = {"work": 0, "advisory": 1, "evolution": 2}
ARCHITECTURE_TARGETS = {
    "L0", "L1", "L2", "L3", "L4", "L5", "LX",
    "local-brain", "skill-graph", "provider-quota", "taskpool",
}
EVOLUTION_ALIGNMENT_FIELDS = ("architecture_target", "capability_delta", "anti_drift_check", "acceptance_evidence")
MISSION_ENVELOPE_REQUIRED_FIELDS = (
    "mission_schema_version",
    "mission_id",
    "mission_title",
    "mission_objective",
    "mission_constraints",
    "red_lines",
    "non_goals",
    "evidence_refs",
    "acceptance_criteria",
    "dag_nodes",
    "checkpoint_states",
    "permission_gates",
    "handoff_artifacts",
    "proof_artifacts",
    "rollback_signal",
    "certification_status",
    "ratification_artifact",
)
MISSION_ENVELOPE_LIST_FIELDS = {
    "mission_constraints",
    "red_lines",
    "non_goals",
    "evidence_refs",
    "acceptance_criteria",
    "dag_nodes",
    "checkpoint_states",
    "permission_gates",
    "handoff_artifacts",
    "proof_artifacts",
}
MISSION_STRUCTURED_REF_FIELDS = {"evidence_refs", "handoff_artifacts", "proof_artifacts", "ratification_artifact"}
MISSION_CERTIFICATION_STATUSES = {"advisory", "not_certified", "certified_with_minor_risks", "certified"}

# Formal lifecycle contract. Markdown task notes remain canonical; this graph is
# the local control-plane guardrail for agents, cron ticks, and multi-model
# planning outputs. Keep it small, explicit, and fail-closed for high-risk exits.
LIFECYCLE_TRANSITIONS: dict[str, list[str]] = {
    "proposed": ["pending", "blocked", "archived", "expired"],
    "pending": ["claimed", "blocked", "archived", "expired"],
    "claimed": ["running", "pending", "retry", "blocked", "archived", "expired"],
    "running": ["review", "retry", "blocked", "expired"],
    "review": ["done", "retry", "blocked", "pending", "archived", "expired"],
    "retry": ["pending", "claimed", "blocked", "archived", "expired"],
    "blocked": ["pending", "retry", "archived", "expired"],
    "done": ["archived"],
    "archived": [],
    "expired": ["archived"],
}
REASON_REQUIRED_TO = {"retry", "blocked"}
EVIDENCE_REQUIRED_TO = {"review", "done"}
CLAIM_BOUND_STATUSES = {"claimed", "running", "review"}
INITIAL_TASK_STATUSES = {"proposed", "pending"}
RECONCILE_STALE_CLAIM_STATUSES = {"pending", "blocked", "expired"}
RECONCILE_OVER_RETRY_STATUSES = {"blocked", "expired"}


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


def _load_autonomy_write_guard():
    spec = importlib.util.spec_from_file_location("autonomy_write_guard", AUTONOMY_WRITE_GUARD)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"autonomy write guard unavailable: {AUTONOMY_WRITE_GUARD}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def guard_autorun_claim_and_handoff(task_id: str, actor: str) -> dict[str, Any]:
    """Fail closed before local task-pool autorun mutates claim/handoff state."""
    guard = _load_autonomy_write_guard()
    evidence = guard.guard_or_raise("kanban-worker", "claim-and-handoff", "dispatch-hint", AUTONOMY_WRITE_ALLOWLIST)
    evidence.setdefault("caller", "brain_task_orchestrator.auto-claim-and-handoff")
    evidence.setdefault("task_id", task_id)
    evidence.setdefault("actor", actor)
    return evidence


def parse_guard_error(exc: BaseException) -> dict[str, Any]:
    try:
        data = json.loads(str(exc))
        if isinstance(data, dict):
            return data
    except Exception:
        pass
    return {"status": "FAIL_CLOSED", "ok": False, "error": str(exc)}


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
                items.append(lines[j][4:].strip().strip('"').strip("'"))
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
        return "[" + ", ".join(json.dumps(str(x), ensure_ascii=False) for x in v) + "]"
    s = str(v)
    if s == "":
        return ""
    if any(ch in s for ch in [": ", "#", "[", "]", "{", "}"]) and not s.startswith("[["):
        return json.dumps(s, ensure_ascii=False)
    return s


def render_frontmatter(fm: dict[str, Any]) -> str:
    preferred = [
        "type", "lane", "layer", "status", "priority", "created", "updated", "expires_at", "project",
        "architecture_target", "capability_delta", "anti_drift_check", "acceptance_evidence", "workflow_contract",
        "mission_schema_version", "mission_id", "mission_title", "mission_objective", "mission_constraints",
        "red_lines", "non_goals", "evidence_refs", "acceptance_criteria", "dag_nodes", "checkpoint_states",
        "permission_gates", "handoff_artifacts", "proof_artifacts", "rollback_signal", "certification_status",
        "ratification_artifact",
        "claimed_by", "claim_expires_at", "run_id", "retry_count", "next_attempt_at", "workspace", "parallel_boundary", "evidence", "concepts"
    ]
    keys = preferred + [k for k in fm.keys() if k not in preferred]
    out = ["---"]
    for k in keys:
        if k not in fm:
            continue
        v = fm[k]
        if isinstance(v, list) and k == "evidence" and v:
            out.append(f"{k}:")
            for item in v:
                out.append(f"  - {yaml_scalar(item)}")
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


def list_value(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(x).strip() for x in value if str(x).strip()]
    if value in (None, ""):
        return []
    return [x.strip() for x in str(value).split(",") if x.strip()]


def infer_lane(fm: dict[str, Any]) -> str:
    raw = str(fm.get("lane") or "").strip().lower()
    if raw in VALID_LANES:
        return raw
    concepts = " ".join(list_value(fm.get("concepts"))).lower()
    haystack = f"{fm.get('project') or ''} {concepts} {fm.get('type') or ''}".lower()
    if any(token in haystack for token in ("evolution", "self-improvement", "自进化", "skill-graph", "provider-quota")):
        return "evolution"
    if any(token in haystack for token in ("advisory", "research", "analysis", "分析")):
        return "advisory"
    return "work"


def architecture_alignment_missing(fm: dict[str, Any]) -> list[str]:
    if infer_lane(fm) != "evolution":
        return []
    missing = [field for field in EVOLUTION_ALIGNMENT_FIELDS if not str(fm.get(field) or "").strip()]
    target = str(fm.get("architecture_target") or "").strip()
    if target and target not in ARCHITECTURE_TARGETS:
        missing.append("architecture_target:known_target")
    return missing


def architecture_aligned(fm: dict[str, Any]) -> bool:
    return not architecture_alignment_missing(fm)


def is_mission_envelope_fm(fm: dict[str, Any]) -> bool:
    concepts = {x.lower() for x in list_value(fm.get("concepts"))}
    if "mission-envelope" in concepts:
        return True
    return any(str(fm.get(field) or "").strip() for field in MISSION_ENVELOPE_REQUIRED_FIELDS)


def mission_envelope_missing(fm: dict[str, Any]) -> list[str]:
    if not is_mission_envelope_fm(fm):
        return []
    missing: list[str] = []
    for field in MISSION_ENVELOPE_REQUIRED_FIELDS:
        value = fm.get(field)
        if field in MISSION_ENVELOPE_LIST_FIELDS:
            if not list_value(value):
                missing.append(field)
        elif not str(value or "").strip():
            missing.append(field)
    for field in MISSION_ENVELOPE_LIST_FIELDS:
        if field not in MISSION_STRUCTURED_REF_FIELDS:
            continue
        for item in list_value(fm.get(field)):
            if not evidence_is_structured(item):
                missing.append(f"{field}:structured_ref")
                break
    ratification = str(fm.get("ratification_artifact") or "").strip()
    if ratification and not evidence_is_structured(ratification):
        missing.append("ratification_artifact:structured_ref")
    certification = str(fm.get("certification_status") or "").strip()
    if certification and certification not in MISSION_CERTIFICATION_STATUSES:
        missing.append("certification_status:known_status")
    if certification == "certified" and not ratification.startswith(("file:", "artifact:", "url:", "proof:")):
        missing.append("certified_requires_ratification_artifact")
    return sorted(set(missing))


def mission_envelope_valid(fm: dict[str, Any]) -> bool:
    return not mission_envelope_missing(fm)


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

    @property
    def lane(self) -> str:
        return infer_lane(self.fm)

    @property
    def architecture_target(self) -> str:
        return str(self.fm.get("architecture_target") or "")

    def architecture_aligned(self) -> bool:
        return architecture_aligned(self.fm)

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
        return self.status in CLAIM_BOUND_STATUSES and self.claim_expires_at() is not None and self.claim_expires_at() < at

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
        if self.status not in {"pending", "retry"}:
            return False
        if any(self.fm.get(field) for field in ("claimed_by", "claim_expires_at", "run_id")):
            return False
        if self.status == "retry" and not self.is_retry_due(at):
            return False
        if self.lane == "evolution" and not self.architecture_aligned():
            return False
        if is_mission_envelope_fm(self.fm) and not mission_envelope_valid(self.fm):
            return False
        return True

    def row(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "status": self.status,
            "priority": self.priority,
            "score": self.score(),
            "lane": self.lane,
            "architecture_target": self.architecture_target,
            "architecture_aligned": self.architecture_aligned(),
            "mission_id": str(self.fm.get("mission_id") or ""),
            "mission_envelope": is_mission_envelope_fm(self.fm),
            "mission_envelope_valid": mission_envelope_valid(self.fm),
            "mission_envelope_missing": mission_envelope_missing(self.fm),
            "project": self.project,
            "claimed_by": self.fm.get("claimed_by") or "",
            "claim_expires_at": self.fm.get("claim_expires_at") or "",
            "retry_count": self.fm.get("retry_count") or 0,
            "next_attempt_at": self.fm.get("next_attempt_at") or "",
            "expires_at": self.fm.get("expires_at") or "",
            "parallel_boundary": self.fm.get("parallel_boundary") or task_parallel_boundary_key(self),
            "stale_claim": self.is_stale_claim(),
            "expired": self.is_expired(),
            "dispatchable": self.is_dispatchable(),
            "lifecycle_next": allowed_next_statuses(self.status),
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


def dispatch_sort_key(t: Task) -> tuple[int, int, datetime, str, str]:
    return (LANE_SORT_WEIGHT.get(t.lane, 1), -t.score(), t.expires_at() or datetime.max.replace(tzinfo=TZ), t.priority, t.id)


def dispatchable_tasks() -> list[Task]:
    rows = [t for t in iter_tasks() if t.is_dispatchable()]
    return sorted(rows, key=dispatch_sort_key)


def evidence_is_structured(e: str) -> bool:
    e = (e or "").strip()
    if not e:
        return False
    prefixes = ("command:", "file:", "search:", "brainctl:", "url:", "artifact:", "proof:")
    if e.startswith(prefixes):
        return True
    p = Path(os.path.expanduser(e))
    return p.is_absolute() and p.exists()


def canonical_json(data: dict[str, Any]) -> str:
    return json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def proof_payload_hash(event: dict[str, Any]) -> str:
    payload = {k: v for k, v in event.items() if k != "event_hash"}
    return "sha256:" + hashlib.sha256(canonical_json(payload).encode("utf-8")).hexdigest()


def read_autorun_proof_events() -> list[dict[str, Any]]:
    if not AUTORUN_PROOF_LOG.exists():
        return []
    events: list[dict[str, Any]] = []
    for line in AUTORUN_PROOF_LOG.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        events.append(json.loads(line))
    return events


def verify_autorun_proof_chain() -> tuple[bool, list[str]]:
    failures: list[str] = []
    prev = ""
    try:
        events = read_autorun_proof_events()
    except Exception as exc:
        return False, [f"autorun proof log unreadable: {exc}"]
    for i, event in enumerate(events, 1):
        if event.get("prev_hash", "") != prev:
            failures.append(f"autorun proof chain prev_hash mismatch at line {i}")
        expected = proof_payload_hash(event)
        if event.get("event_hash") != expected:
            failures.append(f"autorun proof chain hash mismatch at line {i}")
        prev = str(event.get("event_hash") or "")
    return not failures, failures


def verify_autorun_proof_hash(proof_hash: str) -> bool:
    if not proof_hash.startswith("sha256:"):
        return False
    ok, _failures = verify_autorun_proof_chain()
    if not ok:
        return False
    try:
        return any(event.get("event_hash") == proof_hash for event in read_autorun_proof_events())
    except Exception:
        return False


def append_autorun_proof_event(event: dict[str, Any]) -> str:
    AUTORUN_STATE_DIR.mkdir(parents=True, exist_ok=True)
    try:
        prior = read_autorun_proof_events()
    except Exception as exc:
        raise SystemExit(f"autorun proof log is not readable JSONL: {exc}")
    prev_hash = str(prior[-1].get("event_hash") or "") if prior else ""
    record = {
        "schema": "local_brain_autorun_proof_v1",
        "generated_at": iso(),
        "prev_hash": prev_hash,
        **event,
    }
    record["event_hash"] = proof_payload_hash(record)
    with AUTORUN_PROOF_LOG.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")
    return str(record["event_hash"])


def load_autorun_allowlist() -> list[Any]:
    try:
        data = json.loads(AUTORUN_ALLOWLIST.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return []
    except Exception:
        return []
    return data if isinstance(data, list) else []


def autorun_allowlist_matches(task: Task, allowlist: list[Any]) -> bool:
    for item in allowlist:
        if isinstance(item, str):
            token = item.strip()
            if token in {task.id, f"task:{task.id}", task.project, f"project:{task.project}", task.title}:
                return True
        elif isinstance(item, dict):
            task_id = str(item.get("task_id") or item.get("id") or "").strip()
            project = str(item.get("project") or "").strip()
            title = str(item.get("title") or "").strip()
            if (task_id and task_id == task.id) or (project and project == task.project) or (title and title == task.title):
                return True
    return False


def is_autorun_context(task: Task, actor: str) -> bool:
    return str(actor or "").startswith("hermes-autorun") or str(task.fm.get("run_id") or "").startswith("autorun-")


def task_has_autorun_audit(task: Task) -> bool:
    return "by `hermes-autorun" in task.body or any(str(e).startswith("proof:sha256:") for e in (task.fm.get("evidence") if isinstance(task.fm.get("evidence"), list) else []))


def validate_clean_text(label: str, value: str, *, allow_empty: bool = True) -> None:
    text = "" if value is None else str(value)
    if not allow_empty and not text.strip():
        raise SystemExit(f"{label} must not be empty")
    if any(ch in text for ch in ("\n", "\r")) or any(ord(ch) < 32 for ch in text):
        raise SystemExit(f"{label} must be a single-line printable value")
    if text.strip() == "---":
        raise SystemExit(f"{label} must not be a frontmatter delimiter")


def validate_clean_values(**values: Any) -> None:
    for label, value in values.items():
        if value is None:
            continue
        if isinstance(value, list):
            for i, item in enumerate(value):
                validate_clean_text(f"{label}[{i}]", str(item))
        else:
            validate_clean_text(label, str(value))


def allowed_next_statuses(status: str) -> list[str]:
    return list(LIFECYCLE_TRANSITIONS.get(STATUS_ALIASES.get(status, status), []))


def has_active_claim(task: Task, at: datetime | None = None) -> bool:
    at = at or now()
    lease = task.claim_expires_at()
    return bool(task.fm.get("claimed_by") and task.fm.get("run_id") and lease and lease >= at)


def lifecycle_gate(task: Task, to_status: str, actor: str, evidence: list[str] | None = None, reason: str = "", force: bool = False) -> tuple[list[str], list[str]]:
    """Return (failures, warnings) for a proposed lifecycle transition."""
    evidence = evidence or []
    reason = (reason or "").strip()
    validate_clean_values(actor=actor, reason=reason, evidence=evidence)
    failures: list[str] = []
    warnings: list[str] = []
    from_status = task.status
    to_status = STATUS_ALIASES.get(to_status, to_status)
    if to_status not in VALID_STATUSES:
        failures.append(f"invalid target status: {to_status}")
        return failures, warnings
    if from_status not in VALID_STATUSES:
        failures.append(f"invalid current status {from_status}: {task.id}")
        return failures, warnings
    missing_alignment = architecture_alignment_missing(task.fm)
    if missing_alignment and to_status in (CLAIM_BOUND_STATUSES | {"done"}) and not force:
        failures.append(f"evolution_architecture_alignment_missing: {missing_alignment}")
    missing_mission = mission_envelope_missing(task.fm)
    if missing_mission and to_status in (CLAIM_BOUND_STATUSES | {"done"}) and not force:
        failures.append(f"mission envelope missing {missing_mission}: {task.id}")
    if force and reason.lower() in {"", "not specified", "none"}:
        failures.append("--force requires --reason so manual overrides are auditable")
    if to_status == from_status:
        failures.append(f"no-op transition is not allowed: {from_status} -> {to_status}")
    elif to_status not in allowed_next_statuses(from_status) and not force:
        failures.append(f"illegal lifecycle transition: {from_status} -> {to_status}; allowed={allowed_next_statuses(from_status)}")

    owner = str(task.fm.get("claimed_by") or "")
    lease = task.claim_expires_at()
    active_claim = has_active_claim(task)
    if from_status in CLAIM_BOUND_STATUSES and not active_claim and not force:
        failures.append("claim-bound status requires claimed_by, run_id, and a valid non-expired claim_expires_at before transition")
    if from_status in CLAIM_BOUND_STATUSES and owner and owner != actor and not force:
        failures.append(f"task claim owned by {owner}; actor {actor} cannot transition without --force")
    if from_status in CLAIM_BOUND_STATUSES and owner and lease is not None and lease < now() and not force:
        failures.append("task claim is stale; reconcile or --force after manual review before lifecycle transition")
    if to_status in {"running", "review"} and not active_claim and not force:
        failures.append(f"transition to {to_status} requires an active claim first")
    if to_status == "running" and from_status != "claimed" and not force:
        failures.append("running must be entered from claimed so lease ownership is explicit")
    if to_status in REASON_REQUIRED_TO and reason.lower() in {"", "not specified", "none"}:
        failures.append(f"transition to {to_status} requires --reason")
    if to_status in EVIDENCE_REQUIRED_TO and not evidence:
        failures.append(f"transition to {to_status} requires structured --evidence")
    invalid_evidence = [e for e in evidence if not evidence_is_structured(str(e))]
    if invalid_evidence:
        failures.append(f"invalid evidence shape: {invalid_evidence}; use command:/file:/search:/brainctl:/artifact:/url:/proof: prefixes or an existing absolute path")
    if to_status == "done" and is_autorun_context(task, actor):
        proof_hashes = [str(e)[len("proof:") :] for e in evidence if str(e).startswith("proof:sha256:")]
        if not proof_hashes:
            failures.append("autorun closure requires proof:<sha256:...> evidence from the append-only autorun proof log")
        elif not any(verify_autorun_proof_hash(h) for h in proof_hashes):
            failures.append("autorun proof hash not found or chain verification failed")
    if to_status == "done" and from_status != "review" and not force:
        failures.append("done must be entered from review; use --force --reason only for audited manual closure")
    elif to_status == "done" and from_status != "review":
        warnings.append("forced done outside review; preferred path is running -> review -> done")
    return failures, warnings


def apply_lifecycle_status(task: Task, to_status: str, actor: str, *, evidence: list[str] | None = None, reason: str = "", ttl_minutes: int = 60, delay_minutes: int = 60, force: bool = False) -> None:
    stamp = now()
    evidence = evidence or []
    previous = task.status
    task.fm["status"] = to_status
    task.fm["updated"] = iso(stamp)
    if to_status in CLAIM_BOUND_STATUSES:
        if to_status == "claimed" or not task.fm.get("claimed_by"):
            task.fm["claimed_by"] = actor
        if to_status == "claimed" or not task.fm.get("run_id"):
            task.fm["run_id"] = f"{actor}-{stamp.strftime('%Y%m%d%H%M%S')}"
        if to_status == "claimed" or not task.fm.get("claim_expires_at"):
            task.fm["claim_expires_at"] = iso(stamp + timedelta(minutes=ttl_minutes))
    else:
        task.fm["claimed_by"] = ""
        task.fm["claim_expires_at"] = ""
        task.fm["run_id"] = ""
    if to_status == "retry":
        try:
            task.fm["retry_count"] = int(task.fm.get("retry_count") or 0) + 1
        except Exception:
            task.fm["retry_count"] = 1
        task.fm["next_attempt_at"] = iso(stamp + timedelta(minutes=delay_minutes))
    elif to_status != "blocked":
        task.fm["next_attempt_at"] = ""
    if evidence:
        current = task.fm.get("evidence") if isinstance(task.fm.get("evidence"), list) else []
        for e in evidence:
            if e not in current:
                current.append(e)
        task.fm["evidence"] = current
    reason_text = f" Reason: {reason}" if reason else ""
    evidence_text = f" Evidence: {', '.join(evidence)}" if evidence else ""
    force_text = " Force: true." if force else ""
    task.body += f"\n- {iso(stamp)}: Lifecycle transition `{previous}` -> `{to_status}` by `{actor}`.{force_text}{reason_text}{evidence_text}\n"


def body_has_legacy_proof(body: str) -> bool:
    proof_markers = ["## Proof Log", "## Final verification bundle", "## Final Verification", "## Evidence Boundary"]
    evidence_markers = ["`python", "`brainctl", "exit 0", "passed=true", "tests OK", "OK.", "status `certified`"]
    return any(m in body for m in proof_markers) and any(m in body for m in evidence_markers)


def command_list(args: argparse.Namespace) -> dict[str, Any]:
    rows = [t.row() for t in sorted_tasks(include_done=args.include_done)]
    return {"status": "OK", "generated_at": iso(), "task_count": len(rows), "rows": rows}


def command_add(args: argparse.Namespace) -> dict[str, Any]:
    title = args.title.strip()
    if args.status not in INITIAL_TASK_STATUSES:
        raise SystemExit(f"add can only create initial statuses {sorted(INITIAL_TASK_STATUSES)}; use transition/reconcile for lifecycle changes")
    lane_arg = (getattr(args, "lane", "auto") or "auto").strip().lower()
    if lane_arg != "auto" and lane_arg not in VALID_LANES:
        raise SystemExit(f"lane must be one of {['auto', *VALID_LANES]}")
    validate_clean_values(title=title, layer=args.layer, status=args.status, priority=args.priority, project=args.project, workflow_contract=args.workflow_contract, workspace=args.workspace or "", parallel_boundary=getattr(args, "parallel_boundary", "") or "", concepts=args.concepts or "task", lane=lane_arg, architecture_target=getattr(args, "architecture_target", ""), capability_delta=getattr(args, "capability_delta", ""), anti_drift_check=getattr(args, "anti_drift_check", ""), acceptance_evidence=getattr(args, "acceptance_evidence", ""))
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
    preliminary = {"lane": "" if lane_arg == "auto" else lane_arg, "project": args.project, "concepts": concepts, "type": "task"}
    lane = infer_lane(preliminary)
    fm = {
        "type": "task",
        "lane": lane,
        "layer": args.layer,
        "status": args.status,
        "priority": args.priority,
        "created": iso(created),
        "updated": iso(created),
        "expires_at": iso(expires) if expires else "",
        "project": args.project,
        "architecture_target": getattr(args, "architecture_target", "") or "",
        "capability_delta": getattr(args, "capability_delta", "") or "",
        "anti_drift_check": getattr(args, "anti_drift_check", "") or "",
        "acceptance_evidence": getattr(args, "acceptance_evidence", "") or "",
        "workflow_contract": args.workflow_contract,
        "claimed_by": "",
        "claim_expires_at": "",
        "run_id": "",
        "retry_count": 0,
        "next_attempt_at": "",
        "workspace": args.workspace or "",
        "parallel_boundary": getattr(args, "parallel_boundary", "") or "",
        "evidence": [],
        "concepts": concepts,
    }
    missing_alignment = architecture_alignment_missing(fm)
    if missing_alignment:
        raise SystemExit(f"evolution tasks require architecture alignment fields; missing/invalid={missing_alignment}")
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
        if k in {"priority", "project", "concepts", "expires_at", "objective", "lane", "architecture_target", "capability_delta", "anti_drift_check", "acceptance_evidence", "parallel_boundary"}:
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
            lane=meta.get("lane", "auto"), architecture_target=meta.get("architecture_target", ""), capability_delta=meta.get("capability_delta", ""), anti_drift_check=meta.get("anti_drift_check", ""), acceptance_evidence=meta.get("acceptance_evidence", ""), parallel_boundary=meta.get("parallel_boundary", ""),
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
    active_claim = has_active_claim(t)
    if active_claim and not args.force:
        raise SystemExit(f"task already claimed by {t.fm.get('claimed_by')} until {t.fm.get('claim_expires_at')}; use --force only after manual review")
    run_id = args.run_id or ""
    validate_clean_values(run_id=run_id)
    failures, warnings = lifecycle_gate(t, "claimed", args.actor, reason=args.reason, force=args.force)
    if failures:
        raise SystemExit("; ".join(failures))
    apply_lifecycle_status(t, "claimed", args.actor, reason=args.reason, ttl_minutes=args.ttl_minutes, force=args.force)
    if run_id:
        t.fm["run_id"] = run_id
    save_task(t)
    return {"status": "OK", "task": t.id, "claimed_by": args.actor, "claim_expires_at": t.fm["claim_expires_at"], "warnings": warnings, "path": str(t.path)}


def command_release(args: argparse.Namespace) -> dict[str, Any]:
    t = find_task(args.task)
    owner = t.fm.get("claimed_by") or ""
    if owner and owner != args.actor and not args.force:
        raise SystemExit(f"task claimed by {owner}; {args.actor} cannot release without --force")
    failures, warnings = lifecycle_gate(t, args.to_status, args.actor, reason=args.reason, force=args.force)
    if failures:
        raise SystemExit("; ".join(failures))
    apply_lifecycle_status(t, args.to_status, args.actor, reason=args.reason, force=args.force)
    save_task(t)
    return {"status": "OK", "task": t.id, "to_status": args.to_status, "warnings": warnings, "path": str(t.path)}


def command_done(args: argparse.Namespace) -> dict[str, Any]:
    t = find_task(args.task)
    if not args.evidence:
        raise SystemExit("done requires at least one structured --evidence entry, e.g. 'command: pytest PASS' or 'file:/path/to/proof.md'")
    failures, warnings = lifecycle_gate(t, "done", args.actor, args.evidence, args.reason, args.force)
    if failures:
        raise SystemExit("; ".join(failures))
    apply_lifecycle_status(t, "done", args.actor, evidence=args.evidence, reason=args.reason, force=args.force)
    save_task(t)
    evidence = t.fm.get("evidence") if isinstance(t.fm.get("evidence"), list) else []
    return {"status": "OK", "task": t.id, "path": str(t.path), "evidence_count": len(evidence), "warnings": warnings}


def command_retry(args: argparse.Namespace) -> dict[str, Any]:
    t = find_task(args.task)
    failures, warnings = lifecycle_gate(t, "retry", args.actor, reason=args.reason)
    if failures:
        raise SystemExit("; ".join(failures))
    apply_lifecycle_status(t, "retry", args.actor, reason=args.reason, delay_minutes=args.delay_minutes)
    save_task(t)
    return {"status": "OK", "task": t.id, "retry_count": t.fm.get("retry_count") or 0, "next_attempt_at": t.fm["next_attempt_at"], "warnings": warnings, "path": str(t.path)}


def command_lifecycle(args: argparse.Namespace) -> dict[str, Any]:
    tasks = iter_tasks()
    invalid: list[dict[str, Any]] = []
    missing_graph_states = sorted(set(VALID_STATUSES) - set(LIFECYCLE_TRANSITIONS))
    for state in missing_graph_states:
        invalid.append({"task": "__schema__", "status": state, "reason": "status_missing_from_lifecycle_graph"})
    for state, targets in LIFECYCLE_TRANSITIONS.items():
        for target in targets:
            if target not in VALID_STATUSES:
                invalid.append({"task": "__schema__", "status": state, "target": target, "reason": "transition_target_invalid_status"})
    for t in tasks:
        missing_alignment = architecture_alignment_missing(t.fm)
        if missing_alignment:
            invalid.append({"task": t.id, "status": t.status, "fields": missing_alignment, "reason": "evolution_architecture_alignment_missing"})
        missing_mission = mission_envelope_missing(t.fm)
        if missing_mission:
            invalid.append({"task": t.id, "status": t.status, "fields": missing_mission, "reason": "mission_envelope_missing"})
        if t.status not in LIFECYCLE_TRANSITIONS:
            invalid.append({"task": t.id, "status": t.status, "reason": "status_not_in_lifecycle_graph"})
        claim_fields = [k for k in ("claimed_by", "claim_expires_at", "run_id") if t.fm.get(k)]
        if t.status in CLAIM_BOUND_STATUSES and not t.fm.get("claimed_by"):
            invalid.append({"task": t.id, "status": t.status, "reason": "claim_bound_status_missing_claimed_by"})
        if t.status in CLAIM_BOUND_STATUSES and not t.fm.get("claim_expires_at"):
            invalid.append({"task": t.id, "status": t.status, "reason": "claim_bound_status_missing_lease"})
        if t.status in CLAIM_BOUND_STATUSES and not t.fm.get("run_id"):
            invalid.append({"task": t.id, "status": t.status, "reason": "claim_bound_status_missing_run_id"})
        if t.status in CLAIM_BOUND_STATUSES and t.fm.get("claimed_by") and t.claim_expires_at() is None:
            invalid.append({"task": t.id, "status": t.status, "reason": "claim_bound_status_invalid_lease"})
        if t.status in CLAIM_BOUND_STATUSES and t.is_stale_claim():
            invalid.append({"task": t.id, "status": t.status, "reason": "claim_bound_status_stale_lease"})
        if t.status not in CLAIM_BOUND_STATUSES and claim_fields:
            invalid.append({"task": t.id, "status": t.status, "fields": claim_fields, "reason": "non_claim_bound_status_has_claim_metadata"})
        if t.status in EVIDENCE_REQUIRED_TO:
            evidence = t.fm.get("evidence") if isinstance(t.fm.get("evidence"), list) else []
            if not evidence and not (t.status == "done" and body_has_legacy_proof(t.body)):
                invalid.append({"task": t.id, "status": t.status, "reason": f"{t.status}_missing_structured_or_legacy_proof"})
            for e in evidence:
                if not evidence_is_structured(str(e)):
                    invalid.append({"task": t.id, "status": t.status, "evidence": str(e), "reason": "evidence_not_structured"})
        for line in t.body.splitlines():
            m = re.search(r"Lifecycle transition `([^`]+)` -> `([^`]+)`", line)
            if not m:
                continue
            from_status = STATUS_ALIASES.get(m.group(1), m.group(1))
            to_status = STATUS_ALIASES.get(m.group(2), m.group(2))
            forced = "Force: true" in line
            if to_status not in allowed_next_statuses(from_status) and not forced:
                invalid.append({"task": t.id, "from_status": from_status, "to_status": to_status, "reason": "illegal_recorded_lifecycle_transition"})
            if to_status == "done" and from_status != "review" and not forced:
                invalid.append({"task": t.id, "from_status": from_status, "to_status": to_status, "reason": "done_recorded_outside_review_without_force"})
    status = "PASS" if not invalid else "FAIL"
    return {
        "status": status,
        "schema": "local_brain_task_lifecycle_v1",
        "generated_at": iso(),
        "states": VALID_STATUSES,
        "transitions": LIFECYCLE_TRANSITIONS,
        "reason_required_to": sorted(REASON_REQUIRED_TO),
        "evidence_required_to": sorted(EVIDENCE_REQUIRED_TO),
        "claim_bound_statuses": sorted(CLAIM_BOUND_STATUSES),
        "task_count": len(tasks),
        "invalid_count": len(invalid),
        "invalid": invalid,
    }


def command_transition(args: argparse.Namespace) -> dict[str, Any]:
    t = find_task(args.task)
    from_status = t.status
    to_status = STATUS_ALIASES.get(args.to_status, args.to_status)
    failures, warnings = lifecycle_gate(t, to_status, args.actor, args.evidence, args.reason, args.force)
    if failures:
        raise SystemExit("; ".join(failures))
    apply_lifecycle_status(t, to_status, args.actor, evidence=args.evidence, reason=args.reason, ttl_minutes=args.ttl_minutes, delay_minutes=args.delay_minutes, force=args.force)
    save_task(t)
    return {
        "status": "OK",
        "task": t.id,
        "from_status": from_status,
        "to_status": to_status,
        "warnings": warnings,
        "path": str(t.path),
        "next_allowed": allowed_next_statuses(to_status),
    }


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
    table = ["| Rank | Score | Lane | Architecture | Priority | Status | Task | Project | Lease / Due |", "|---:|---:|---|---|---|---|---|---|---|"]
    for i, t in enumerate(top_rows, 1):
        due = t.fm.get("expires_at") or ""
        lease = t.fm.get("claim_expires_at") or ""
        marker = "stale lease" if t.is_stale_claim() else ("expired" if t.is_expired() else "")
        arch = t.architecture_target or ("aligned" if t.architecture_aligned() else "missing")
        table.append(f"| {i} | {t.score()} | {t.lane} | {arch} | {t.priority} | {t.status} | {obsidian_link(t.path)} | {t.project} | {marker or lease or due} |")
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
  "lifecycle_transitions": {json.dumps(LIFECYCLE_TRANSITIONS, ensure_ascii=False)},
  "must_reconcile_before_dispatch": true,
  "must_transition_via_graph": true,
  "safe_dispatch_tick": "python3 ~/.hermes/scripts/brain_task_dispatch_tick.py",
  "boundary_check": "python3 ~/.hermes/scripts/brain_task_orchestrator.py boundary-check --json",
  "parallel_dispatch_dry_run": "python3 ~/.hermes/scripts/brain_task_orchestrator.py parallel-dispatch-dry-run --max-agents 3 --json",
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

# 检查任务池边界：lane、架构对齐、并行冲突、kill switch
python3 ~/.hermes/scripts/brain_task_orchestrator.py boundary-check --json

# 生成多 Agent 并行派发 dry-run；按 work 优先、parallel_boundary/workspace/project 隔离
python3 ~/.hermes/scripts/brain_task_orchestrator.py parallel-dispatch-dry-run --max-agents 3 --json

# 安全 tick：收件箱 ingest + reconcile + dashboard + dispatch hint
python3 ~/.hermes/scripts/brain_task_dispatch_tick.py --print-always

# 认领任务，生成 lease
python3 ~/.hermes/scripts/brain_task_orchestrator.py claim TASK_ID --actor hermes --ttl-minutes 60

# 释放任务
python3 ~/.hermes/scripts/brain_task_orchestrator.py release TASK_ID --actor hermes --to-status pending

# 查看生命周期契约与审计当前任务
python3 ~/.hermes/scripts/brain_task_orchestrator.py lifecycle --json

# 严格状态流转（走状态机 + 审计日志）
python3 ~/.hermes/scripts/brain_task_orchestrator.py transition TASK_ID --actor hermes --to running
python3 ~/.hermes/scripts/brain_task_orchestrator.py transition TASK_ID --actor hermes --to review --evidence "command:验证命令 PASS"
python3 ~/.hermes/scripts/brain_task_orchestrator.py transition TASK_ID --actor hermes --to done --evidence "file:/path/to/proof.md"

# 标记完成：必须给结构化 evidence（legacy convenience；优先用 transition review -> done）
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
- dispatch lane order: `work` → `advisory` → `evolution`；自进化不能抢占 work 交付。
- `parallel_boundary` / `workspace` / `project` 定义多 Agent 并行隔离边界；同边界同一 dry-run 只派发一个任务。
- `lane: evolution` 必须带 `architecture_target` / `capability_delta` / `anti_drift_check` / `acceptance_evidence`，否则 fail-closed 不派发。

## 5. 安全边界

- Markdown task note 是事实源。
- Dashboard / sorted pool 是 derived view。
- Workflow contract 中的 hooks 默认 inert；没有 allowlisted runner 不执行。
- 自动执行任务前必须先 claim，结束必须 release/done/retry 并写 proof。
- 长期闭环必须经过 [[07-仪表盘/Agent技能树路由矩阵]] 选择 skills，不能凭感觉调度。
"""


def command_reconcile(args: argparse.Namespace) -> dict[str, Any]:
    validate_clean_values(actor=args.actor)
    if args.stale_claim_status not in RECONCILE_STALE_CLAIM_STATUSES:
        raise SystemExit(f"--stale-claim-status must be one of {sorted(RECONCILE_STALE_CLAIM_STATUSES)}")
    if args.over_retry_status not in RECONCILE_OVER_RETRY_STATUSES:
        raise SystemExit(f"--over-retry-status must be one of {sorted(RECONCILE_OVER_RETRY_STATUSES)}")
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
        elif t.status not in CLAIM_BOUND_STATUSES and any(t.fm.get(k) for k in ("claimed_by", "claim_expires_at", "run_id")):
            t.fm.update({"claimed_by": "", "claim_expires_at": "", "run_id": "", "updated": iso(stamp)})
            action = "orphan_claim_metadata_cleared"
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
        missing_mission = mission_envelope_missing(t.fm)
        if missing_mission:
            failures.append(f"mission envelope missing {missing_mission}: {t.id}")
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
        if t.status == "done" and task_has_autorun_audit(t) and not any(str(e).startswith("proof:sha256:") for e in evidence):
            failures.append(f"autorun done task missing proof evidence: {t.id}")
        for e in evidence:
            if not evidence_is_structured(str(e)):
                failures.append(f"unstructured evidence in {t.id}: {e}")
            if str(e).startswith("proof:sha256:") and not verify_autorun_proof_hash(str(e)[len("proof:") :]):
                failures.append(f"invalid autorun proof hash in {t.id}: {e}")
        if "## Proof Log" not in t.body and "## Final verification bundle" not in t.body:
            warnings.append(f"missing Proof Log section: {t.id}")
        if "## Final Handoff" not in t.body and not body_has_legacy_proof(t.body):
            warnings.append(f"missing Final Handoff section: {t.id}")
    status = "PASS" if not failures else "FAIL"
    return {"status": status, "checked_count": checked, "failures": failures, "warnings": warnings, "legacy_body_evidence": legacy_body_evidence}


def task_parallel_boundary_key(task: Task) -> str:
    explicit = str(task.fm.get("parallel_boundary") or "").strip()
    if explicit:
        return f"boundary:{explicit}"
    workspace = str(task.fm.get("workspace") or "").strip()
    if workspace:
        return f"workspace:{workspace}"
    if task.lane == "evolution" and task.architecture_target:
        return f"evolution:{task.architecture_target}"
    project = str(task.project or "").strip()
    if project:
        return f"project:{project}"
    return f"task:{task.id}"


def dispatch_prompt_for_row(row: dict[str, Any]) -> str:
    return (
        "Execute this local-brain task only after claiming it. "
        "Treat the task note as canonical workpad; reconcile first; verify; record proof; release/done/retry. "
        f"Task: {row['link']} ({row['id']}) priority={row['priority']} status={row['status']} "
        f"lane={row['lane']} project={row['project']}"
    )


def command_boundary_check(args: argparse.Namespace) -> dict[str, Any]:
    tasks = iter_tasks()
    dispatchable = dispatchable_tasks()
    invalid: list[dict[str, Any]] = []
    warnings: list[dict[str, Any]] = []
    dispatchable_by_lane = {lane: 0 for lane in VALID_LANES}
    for t in dispatchable:
        dispatchable_by_lane[t.lane] = dispatchable_by_lane.get(t.lane, 0) + 1
    for t in tasks:
        missing_alignment = architecture_alignment_missing(t.fm)
        if missing_alignment:
            invalid.append({"task": t.id, "path": str(t.path), "fields": missing_alignment, "reason": "evolution_architecture_alignment_missing"})
        missing_mission = mission_envelope_missing(t.fm)
        if missing_mission:
            invalid.append({"task": t.id, "path": str(t.path), "fields": missing_mission, "reason": "mission_envelope_missing"})
        if t.lane not in VALID_LANES:
            invalid.append({"task": t.id, "path": str(t.path), "lane": t.lane, "reason": "invalid_lane"})
        if t.status in CLAIM_BOUND_STATUSES and not (t.fm.get("claimed_by") and t.fm.get("claim_expires_at") and t.fm.get("run_id")):
            invalid.append({"task": t.id, "path": str(t.path), "status": t.status, "reason": "claim_bound_status_missing_lease_metadata"})
    boundary_index: dict[str, list[str]] = {}
    for t in dispatchable:
        boundary_index.setdefault(task_parallel_boundary_key(t), []).append(t.id)
    for key, ids in sorted(boundary_index.items()):
        if len(ids) > 1:
            warnings.append({"boundary_key": key, "tasks": ids, "reason": "parallel_boundary_conflict"})
    gates = {
        "work_lane_available": dispatchable_by_lane.get("work", 0) > 0,
        "autorun_enabled": os.environ.get(AUTORUN_ENV_FLAG) == "1",
        "kill_switch_env_set": os.environ.get("HERMES_LOCAL_BRAIN_AUTORUN_KILL") == "1",
        "kill_switch_file_present": AUTORUN_KILL_SWITCH.exists(),
        "evolution_preempted_by_work": dispatchable_by_lane.get("work", 0) > 0 and dispatchable_by_lane.get("evolution", 0) > 0,
    }
    status = "PASS" if not invalid else "FAIL"
    return {
        "status": status,
        "schema": "local_brain_task_boundary_v1",
        "generated_at": iso(),
        "task_count": len(tasks),
        "dispatchable_count": len(dispatchable),
        "dispatchable_by_lane": dispatchable_by_lane,
        "gates": gates,
        "invalid_count": len(invalid),
        "invalid": invalid,
        "warnings": warnings,
        "safety": "fail-closed invariants for taskpool boundaries and parallel dry-run selection",
    }


def select_parallel_dispatch(max_agents: int) -> tuple[list[Task], list[dict[str, Any]]]:
    candidates = dispatchable_tasks()
    work_available = any(t.lane == "work" for t in candidates)
    selected: list[Task] = []
    skipped: list[dict[str, Any]] = []
    used_boundaries: dict[str, str] = {}
    for t in candidates:
        if work_available and t.lane != "work":
            skipped.append({"id": t.id, "lane": t.lane, "reason": "lane_preempted_by_work", "path": str(t.path)})
            continue
        boundary_key = task_parallel_boundary_key(t)
        if boundary_key in used_boundaries:
            skipped.append({"id": t.id, "lane": t.lane, "reason": "parallel_boundary_conflict", "boundary_key": boundary_key, "conflicts_with": used_boundaries[boundary_key], "path": str(t.path)})
            continue
        if len(selected) >= max_agents:
            skipped.append({"id": t.id, "lane": t.lane, "reason": "capacity_exceeded", "boundary_key": boundary_key, "path": str(t.path)})
            continue
        selected.append(t)
        used_boundaries[boundary_key] = t.id
    return selected, skipped


def command_parallel_dispatch_dry_run(args: argparse.Namespace) -> dict[str, Any]:
    max_agents = int(getattr(args, "max_agents", 3) or 3)
    if max_agents < 1:
        raise SystemExit("--max-agents must be >= 1")
    boundary = command_boundary_check(args)
    if boundary.get("status") != "PASS":
        return {"status": "FAIL", "dry_run": True, "dispatchable": False, "reason": "boundary_check_failed", "boundary": boundary, "safety": "dry-run only; no claim or execution"}
    selected, skipped = select_parallel_dispatch(max_agents)
    dispatch_plan = []
    for t in selected:
        row = t.row()
        dispatch_plan.append({
            "id": t.id,
            "boundary_key": task_parallel_boundary_key(t),
            "claim_command": f"python3 ~/.hermes/scripts/brain_task_orchestrator.py claim {t.id} --actor hermes --ttl-minutes 60",
            "execution_prompt": dispatch_prompt_for_row(row),
        })
    return {
        "status": "OK",
        "dry_run": True,
        "dispatchable": bool(selected),
        "max_agents": max_agents,
        "selected_count": len(selected),
        "selected": [t.row() for t in selected],
        "skipped": skipped,
        "dispatch_plan": dispatch_plan,
        "boundary": boundary,
        "safety": "dry-run only; does not claim, execute, or mark tasks done",
    }


def command_next(args: argparse.Namespace) -> dict[str, Any]:
    reconcile_result = None
    if not getattr(args, "no_reconcile", False):
        reconcile_result = command_reconcile(argparse.Namespace(write=bool(getattr(args, "reconcile", False)), actor="next", max_retries=3, retry_delay_minutes=60, stale_claim_status="pending", over_retry_status="blocked", promote_due_retry=True))
        if reconcile_result.get("action_count") and not getattr(args, "reconcile", False):
            return {"status": "OK", "next": None, "message": "Reconcile is required before dispatch. Re-run with --reconcile to write canonical task-note fixes, or run reconcile --write explicitly.", "reconcile": reconcile_result}
    rows = dispatchable_tasks()
    if not rows:
        return {"status": "OK", "next": None, "message": "No dispatchable local-brain tasks in canonical task notes.", "reconcile": reconcile_result}
    t = rows[0]
    return {"status": "OK", "next": t.row(), "claim_command": f"python3 ~/.hermes/scripts/brain_task_orchestrator.py claim {t.id} --actor hermes --ttl-minutes 60", "dashboard_command": "python3 ~/.hermes/scripts/brain_task_orchestrator.py dashboard --write", "reconcile": reconcile_result}


def command_dispatch_dry_run(args: argparse.Namespace) -> dict[str, Any]:
    nxt = command_next(args)
    if not nxt.get("next"):
        return {"status": "OK", "dry_run": True, "dispatchable": False, "message": nxt["message"]}
    row = nxt["next"]
    prompt = dispatch_prompt_for_row(row)
    return {"status": "OK", "dry_run": True, "dispatchable": True, "next": row, "claim_command": nxt["claim_command"], "execution_prompt": prompt, "safety": "dry-run only; does not claim or execute"}


def command_eligibility_check(args: argparse.Namespace) -> dict[str, Any]:
    validate_clean_values(actor=getattr(args, "actor", "hermes-autorun"))
    reasons: list[str] = []
    warnings: list[str] = []
    task: Task | None = None
    if getattr(args, "task", ""):
        task = find_task(args.task)
    else:
        nxt = command_next(argparse.Namespace(reconcile=False, no_reconcile=bool(getattr(args, "no_reconcile", False)), json=True))
        if nxt.get("next"):
            task = find_task(nxt["next"]["id"])
        elif (nxt.get("reconcile") or {}).get("action_count"):
            reasons.append("reconcile_required")
        else:
            reasons.append("no_dispatchable_task")
    allowlist = load_autorun_allowlist()
    allowlist_hit = bool(task and autorun_allowlist_matches(task, allowlist))
    if os.environ.get(AUTORUN_ENV_FLAG) != "1":
        reasons.append("autorun_disabled")
    if os.environ.get("HERMES_LOCAL_BRAIN_AUTORUN_KILL") == "1":
        reasons.append("kill_switch_env_set")
    if AUTORUN_KILL_SWITCH.exists():
        reasons.append("kill_switch_file_present")
    if task and task.lane != "work" and any(t.lane == "work" and t.id != task.id for t in dispatchable_tasks()):
        reasons.append("work_lane_available")
    if not allowlist:
        reasons.append("allowlist_empty")
    elif not allowlist_hit:
        reasons.append("allowlist_miss")
    if task and not task.is_dispatchable():
        reasons.append("task_not_dispatchable")
    proof_ok, proof_failures = verify_autorun_proof_chain()
    if not proof_ok:
        reasons.append("proof_chain_invalid")
        warnings.extend(proof_failures)
    selfcheck = command_selfcheck(argparse.Namespace(json=True))
    if selfcheck.get("status") != "PASS":
        reasons.append("selfcheck_failed")
        warnings.extend(str(x) for x in selfcheck.get("failures", []))
    eligible = bool(task and not reasons)
    row = task.row() if task else None
    return {
        "status": "PASS",
        "eligible": eligible,
        "mode": "allow" if eligible else "deny",
        "reasons": sorted(set(reasons)),
        "warnings": warnings,
        "task_id": task.id if task else "",
        "task": row,
        "allowlist": str(AUTORUN_ALLOWLIST),
        "policy": str(AUTORUN_POLICY),
        "allowlist_hit": allowlist_hit,
        "kill_switch": bool(os.environ.get(AUTORUN_ENV_FLAG) != "1" or os.environ.get("HERMES_LOCAL_BRAIN_AUTORUN_KILL") == "1" or AUTORUN_KILL_SWITCH.exists()),
        "required_proof": ["proof:<sha256:...> required before autorun-originated done"],
        "budget_ceiling": None,
    }


def render_autorun_handoff(task: Task, claim: dict[str, Any], proof_hash: str, actor: str) -> str:
    return f"""# Auto-Claim Handoff — {task.title}

- task_id: `{task.id}`
- task_link: {obsidian_link(task.path)}
- actor: `{actor}`
- run_id: `{task.fm.get('run_id') or ''}`
- claim_expires_at: `{task.fm.get('claim_expires_at') or ''}`
- proof_evidence: `proof:{proof_hash}`

## Safety Contract

- Do not execute Markdown task body as a script.
- Do not run arbitrary hooks from task notes.
- Do not mark the task done from this handoff.
- Runner must perform bounded execution, write concrete evidence, transition `running -> review`, and only then use proof-gated `review -> done`.
- If any gate fails, release/retry/block; never force close.

## Suggested Runner Prompt

Claim has already been acquired. Work only within the task's stated workspace/contract, verify with deterministic commands, append proof, and close through lifecycle gates.

## Claim Result

```json
{json.dumps(claim, ensure_ascii=False, indent=2)}
```
"""


def command_auto_claim_and_handoff(args: argparse.Namespace) -> dict[str, Any]:
    eligibility = command_eligibility_check(args)
    if not eligibility.get("eligible"):
        return {
            "status": "PASS",
            "claimed": False,
            "eligible": False,
            "reasons": eligibility.get("reasons", []),
            "warnings": eligibility.get("warnings", []),
            "task_id": eligibility.get("task_id", ""),
            "safety": "fail-closed; no claim and no execution",
        }
    task = find_task(str(eligibility["task_id"]))
    if not task.is_dispatchable():
        return {"status": "PASS", "claimed": False, "eligible": False, "reasons": ["task_not_dispatchable_after_eligibility"], "task_id": task.id, "safety": "fail-closed; no execution"}
    try:
        write_guard = guard_autorun_claim_and_handoff(task.id, args.actor)
    except PermissionError as exc:
        return {
            "status": "FAIL_CLOSED",
            "claimed": False,
            "eligible": True,
            "task_id": task.id,
            "reasons": ["autonomy_write_guard_failed"],
            "write_guard": parse_guard_error(exc),
            "safety": "fail-closed; no claim, no handoff, no execution",
        }
    except Exception as exc:
        return {
            "status": "FAIL_CLOSED",
            "claimed": False,
            "eligible": True,
            "task_id": task.id,
            "reasons": ["autonomy_write_guard_unavailable"],
            "write_guard": parse_guard_error(exc),
            "safety": "fail-closed; no claim, no handoff, no execution",
        }
    stamp = now()
    run_id = f"autorun-{stamp.strftime('%Y%m%d%H%M%S')}-{task.id[:24]}"
    claim = command_claim(argparse.Namespace(task=task.id, actor=args.actor, ttl_minutes=args.ttl_minutes, run_id=run_id, reason="auto-claim-and-handoff", force=False, json=True))
    claimed_task = find_task(task.id)
    readback_failures = []
    if claimed_task.status != "claimed":
        readback_failures.append(f"status read-back mismatch: {claimed_task.status}")
    if str(claimed_task.fm.get("claimed_by") or "") != args.actor:
        readback_failures.append(f"claimed_by read-back mismatch: {claimed_task.fm.get('claimed_by')}")
    if str(claimed_task.fm.get("run_id") or "") != run_id:
        readback_failures.append(f"run_id read-back mismatch: {claimed_task.fm.get('run_id')}")
    if not claimed_task.fm.get("claim_expires_at"):
        readback_failures.append("claim_expires_at missing after claim")
    if readback_failures:
        try:
            command_release(argparse.Namespace(task=task.id, actor=args.actor, to_status="pending", reason="autorun read-back mismatch; fail-closed release", force=True, json=True))
        except Exception:
            pass
        return {"status": "ERROR", "claimed": False, "eligible": False, "task_id": task.id, "reasons": ["claim_readback_mismatch"], "warnings": readback_failures, "safety": "fail-closed; released if possible; no execution"}
    AUTORUN_HANDOFF_DIR.mkdir(parents=True, exist_ok=True)
    handoff_path = AUTORUN_HANDOFF_DIR / f"{run_id}.md"
    try:
        proof_hash = append_autorun_proof_event({
            "event": "handoff_created",
            "task": task.id,
            "actor": args.actor,
            "run_id": run_id,
            "handoff": str(handoff_path),
            "safety": "claimed-and-handoff-only; no execution; no done",
        })
        atomic_write(handoff_path, render_autorun_handoff(claimed_task, claim, proof_hash, args.actor))
    except Exception as exc:
        try:
            command_release(argparse.Namespace(task=task.id, actor=args.actor, to_status="pending", reason="autorun handoff/proof write failed; fail-closed release", force=True, json=True))
        except Exception:
            pass
        return {"status": "ERROR", "claimed": False, "eligible": False, "task_id": task.id, "reasons": ["handoff_or_proof_write_failed"], "warnings": [str(exc)], "safety": "fail-closed; released if possible; no execution"}
    return {
        "status": "OK",
        "claimed": True,
        "eligible": True,
        "task": task.id,
        "claimed_by": args.actor,
        "run_id": run_id,
        "claim_expires_at": claim.get("claim_expires_at"),
        "handoff": str(handoff_path),
        "proof_hash": proof_hash,
        "proof_log": str(AUTORUN_PROOF_LOG),
        "write_guard": write_guard,
        "safety": "claimed-and-handoff-only; does not execute task body or mark done",
    }


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
        missing_alignment = architecture_alignment_missing(t.fm)
        if missing_alignment:
            failures.append(f"evolution architecture alignment missing {missing_alignment}: {t.path}")
        if t.status not in VALID_STATUSES:
            failures.append(f"invalid status {t.status}: {t.path}")
        if t.status not in LIFECYCLE_TRANSITIONS:
            failures.append(f"status missing lifecycle transition contract {t.status}: {t.path}")
        if t.priority not in PRIORITY_WEIGHT:
            warnings.append(f"unknown priority {t.priority}: {t.path}")
        if t.status in {"claimed", "running", "review"} and not t.fm.get("claimed_by"):
            failures.append(f"claim-bound status missing claimed_by: {t.path}")
        if t.status in {"claimed", "running", "review"} and not t.fm.get("claim_expires_at"):
            failures.append(f"claim-bound status missing claim_expires_at: {t.path}")
        if t.status in {"claimed", "running", "review"} and not t.fm.get("run_id"):
            failures.append(f"claim-bound status missing run_id: {t.path}")
        if t.status not in TERMINAL_STATUSES and not t.fm.get("expires_at"):
            warnings.append(f"active task missing expires_at: {t.path}")
    missing_graph_states = sorted(set(VALID_STATUSES) - set(LIFECYCLE_TRANSITIONS))
    if missing_graph_states:
        failures.append(f"lifecycle graph missing statuses: {missing_graph_states}")
    proof_ok, proof_failures = verify_autorun_proof_chain()
    if not proof_ok:
        failures.extend(proof_failures)
    boundary = command_boundary_check(argparse.Namespace(json=True))
    if boundary.get("status") != "PASS":
        for item in boundary.get("invalid", []):
            failures.append(f"task boundary violation {item.get('reason')}: {item.get('task')}")
    if AUTORUN_HANDOFF_DIR.exists():
        try:
            handoff_count = sum(1 for _ in AUTORUN_HANDOFF_DIR.glob("*.md"))
            if handoff_count > 100:
                warnings.append(f"autorun handoff directory has {handoff_count} handoffs; consider archival/cleanup")
        except Exception as exc:
            warnings.append(f"autorun handoff directory count unavailable: {exc}")
    if DASHBOARD.exists() and "DERIVED VIEW — NOT SOURCE OF TRUTH" not in DASHBOARD.read_text(encoding="utf-8"):
        failures.append("dashboard missing derived-view warning")
    if CONTROL_CENTER.exists() and "处理本地大脑任务收件箱" not in CONTROL_CENTER.read_text(encoding="utf-8"):
        failures.append("control center missing natural-language trigger")
    status = "PASS" if not failures else "FAIL"
    return {"status": status, "task_count": len(iter_tasks()), "failures": failures, "warnings": warnings, "boundary": boundary, "paths": {"dashboard": str(DASHBOARD), "control_center": str(CONTROL_CENTER), "sorted_pool": str(SORTED_POOL), "inbox": str(INBOX)}}


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
    ap.add_argument("--lane", default="auto", choices=["auto", *VALID_LANES])
    ap.add_argument("--architecture-target", default="", choices=["", *sorted(ARCHITECTURE_TARGETS)])
    ap.add_argument("--capability-delta", default="")
    ap.add_argument("--anti-drift-check", default="")
    ap.add_argument("--acceptance-evidence", default="")
    ap.add_argument("--layer", default="L3")
    ap.add_argument("--workflow-contract", default=DEFAULT_WORKFLOW)
    ap.add_argument("--workspace", default="")
    ap.add_argument("--parallel-boundary", default="")
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
    recp.add_argument("--stale-claim-status", default="pending", choices=sorted(RECONCILE_STALE_CLAIM_STATUSES))
    recp.add_argument("--over-retry-status", default="blocked", choices=sorted(RECONCILE_OVER_RETRY_STATUSES))
    recp.add_argument("--promote-due-retry", action="store_true")
    recp.add_argument("--json", action="store_true")

    cp = sub.add_parser("claim")
    cp.add_argument("task")
    cp.add_argument("--actor", default="hermes")
    cp.add_argument("--ttl-minutes", type=int, default=60)
    cp.add_argument("--run-id", default="")
    cp.add_argument("--reason", default="")
    cp.add_argument("--force", action="store_true")
    cp.add_argument("--json", action="store_true")

    rp = sub.add_parser("release")
    rp.add_argument("task")
    rp.add_argument("--actor", default="hermes")
    rp.add_argument("--to-status", default="pending", choices=VALID_STATUSES)
    rp.add_argument("--reason", default="")
    rp.add_argument("--force", action="store_true")
    rp.add_argument("--json", action="store_true")

    dp = sub.add_parser("done")
    dp.add_argument("task")
    dp.add_argument("--actor", default="hermes")
    dp.add_argument("--evidence", action="append", default=[])
    dp.add_argument("--reason", default="")
    dp.add_argument("--force", action="store_true")
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

    lcp = sub.add_parser("lifecycle")
    lcp.add_argument("--json", action="store_true")

    trp = sub.add_parser("transition")
    trp.add_argument("task")
    trp.add_argument("--to", dest="to_status", required=True, choices=VALID_STATUSES)
    trp.add_argument("--actor", default="hermes")
    trp.add_argument("--reason", default="")
    trp.add_argument("--evidence", action="append", default=[])
    trp.add_argument("--ttl-minutes", type=int, default=60)
    trp.add_argument("--delay-minutes", type=int, default=60)
    trp.add_argument("--force", action="store_true")
    trp.add_argument("--json", action="store_true")

    gp = sub.add_parser("dashboard")
    gp.add_argument("--write", action="store_true")
    gp.add_argument("--json", action="store_true")

    np = sub.add_parser("next")
    np.add_argument("--reconcile", action="store_true", help="write required reconcile fixes before selecting next")
    np.add_argument("--no-reconcile", action="store_true", help="skip reconcile preflight")
    np.add_argument("--json", action="store_true")

    ddp = sub.add_parser("dispatch-dry-run")
    ddp.add_argument("--json", action="store_true")

    bcp = sub.add_parser("boundary-check")
    bcp.add_argument("--json", action="store_true")

    pdp = sub.add_parser("parallel-dispatch-dry-run")
    pdp.add_argument("--max-agents", type=int, default=3)
    pdp.add_argument("--json", action="store_true")

    ecp = sub.add_parser("eligibility-check")
    ecp.add_argument("--task", default="")
    ecp.add_argument("--actor", default="hermes-autorun")
    ecp.add_argument("--no-reconcile", action="store_true", help="skip reconcile preflight")
    ecp.add_argument("--json", action="store_true")

    ahp = sub.add_parser("auto-claim-and-handoff")
    ahp.add_argument("--task", default="")
    ahp.add_argument("--actor", default="hermes-autorun")
    ahp.add_argument("--ttl-minutes", type=int, default=60)
    ahp.add_argument("--no-reconcile", action="store_true", help="skip reconcile preflight")
    ahp.add_argument("--json", action="store_true")

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
    if args.cmd == "lifecycle":
        return print_result(command_lifecycle(args), args.json)
    if args.cmd == "transition":
        return print_result(command_transition(args), args.json)
    if args.cmd == "dashboard":
        return print_result(command_dashboard(args), args.json)
    if args.cmd == "next":
        return print_result(command_next(args), args.json)
    if args.cmd == "dispatch-dry-run":
        return print_result(command_dispatch_dry_run(args), args.json)
    if args.cmd == "boundary-check":
        return print_result(command_boundary_check(args), args.json)
    if args.cmd == "parallel-dispatch-dry-run":
        return print_result(command_parallel_dispatch_dry_run(args), args.json)
    if args.cmd == "eligibility-check":
        return print_result(command_eligibility_check(args), args.json)
    if args.cmd == "auto-claim-and-handoff":
        return print_result(command_auto_claim_and_handoff(args), args.json)
    if args.cmd == "selfcheck":
        return print_result(command_selfcheck(args), args.json)
    raise SystemExit(2)


if __name__ == "__main__":
    sys.exit(main())
