#!/usr/bin/env python3
"""Minimal Rokid Lingzhu custom-agent SSE bridge for Hermes.

Run:
  source .venv/bin/activate
  uvicorn app:app --host 127.0.0.1 --port 8787

Rokid SSE endpoint:
  POST /rokid/sse
"""
from __future__ import annotations

import asyncio
import hashlib
import json
import os
import re
import shlex
import subprocess
import sys
import time
import urllib.request
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, AsyncIterator, Dict, List, Optional

import httpx
from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel, Field

from access_brain import build_access_layer_text, build_capability_text, handle_access_layer_query
from l0_routes import (
    BRAIN_STATS_PATTERNS,
    CAPABILITY_QUERY_PATTERNS,
    DAILY_BRIEF_PATTERNS,
    MANUFACTURING_STATUS_PATTERNS,
    ROKID_DEVELOPER_RESOURCE_PATTERNS,
    L0_TEXT_ROUTE_REGISTRY,
    match_text_route,
)
from brain_stats import build_brain_stats_text_from_snapshot
from daily_brief import build_daily_brief_text_from_cache
from manufacturing_status import build_manufacturing_status_text_from_cache
from lingzhu_plugins import (
    build_plugin_receipted_answer,
    build_plugin_unavailable_answer,
    can_execute_plugin,
    extract_lingzhu_plugin_context,
    match_lingzhu_plugin,
)
from route_dispatch import dispatch_runtime_route
from route_runtime import RUNTIME_ROUTE_CHAIN, RouteContext, RouteResult
from rokid_bridge.action_guard import (
    UNSAFE_EXECUTION_CLAIMS,
    has_pending_confirmation,
    is_bare_confirmation_intent,
    orphan_confirmation_answer,
    pending_action_snapshot,
    rewrite_unsafe_execution_claim,
)
from rokid_bridge.context import extract_device_context, safe_session_key
from rokid_bridge.sensor_context import (
    build_sensor_context,
    create_image_analysis_job,
    create_whisper_review_job,
    summarize_sensor_context_for_voice,
)
from rokid_bridge.sensor_worker import process_sensor_queue, summarize_latest_sensor_result
from rokid_dev_review import dev_review_enabled, schedule_dev_review


APP_NAME = "hermes-rokid-bridge"


def load_env_file(path: str) -> None:
    """Load simple KEY=VALUE env files without overriding existing env."""
    try:
        with open(os.path.expanduser(path), "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, value = line.split("=", 1)
                os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))
    except FileNotFoundError:
        return


load_env_file("~/.hermes/.env")
load_env_file(str(Path(__file__).with_name(".env")))

ROKID_AGENT_ID = os.getenv("ROKID_AGENT_ID", "hermes-rokid")
ROKID_AGENT_AK = os.getenv("ROKID_AGENT_AK", "")
HERMES_BIN = os.getenv("HERMES_BIN", "hermes")
HERMES_MODEL = os.getenv("HERMES_MODEL", "")
HERMES_PROVIDER = os.getenv("HERMES_PROVIDER", "")
HERMES_TIMEOUT_SECONDS = int(os.getenv("HERMES_TIMEOUT_SECONDS", "90"))
MAX_PROMPT_CHARS = int(os.getenv("MAX_PROMPT_CHARS", "6000"))
ROKID_RESPONSE_MODE = os.getenv("ROKID_RESPONSE_MODE", "direct_xiaomi")
ROKID_FAST_MODEL = os.getenv("ROKID_FAST_MODEL", "mimo-v2.5-pro")
ROKID_FAST_TIMEOUT_SECONDS = int(os.getenv("ROKID_FAST_TIMEOUT_SECONDS", "12"))
# Production Rokid traffic in China regularly spends 4-8s in provider/network latency.
# Keep this lower in tests via monkey-patching, but default to a network-aware budget
# so normal conversation does not degrade into repeated timeout fallbacks.
ROKID_MODEL_BUDGET_SECONDS = float(os.getenv("ROKID_MODEL_BUDGET_SECONDS", "8.5"))
ROKID_FAST_MAX_TOKENS = int(os.getenv("ROKID_FAST_MAX_TOKENS", "300"))
ROKID_ENABLE_HERMES_FALLBACK = os.getenv("ROKID_ENABLE_HERMES_FALLBACK", "false").lower() in {"1", "true", "yes"}
ROKID_BRAIN_FILE = os.getenv("ROKID_BRAIN_FILE", "~/.hermes/brains/rokid-glasses/ENTRY_BRAIN.md")
ROKID_UPGRADE_QUEUE_PATH = os.getenv("ROKID_UPGRADE_QUEUE_PATH", "~/.hermes/brains/rokid-glasses/pending_upgrades.jsonl")
ROKID_BRAIN_STATS_CACHE = os.getenv("ROKID_BRAIN_STATS_CACHE", "~/.hermes/brains/rokid-glasses/local_brain_stats.json")
ROKID_DAILY_BRIEF_CACHE = os.getenv("ROKID_DAILY_BRIEF_CACHE", "~/.hermes/brains/rokid-glasses/daily_brief_cache.json")
ROKID_MANUFACTURING_STATUS_CACHE = os.getenv("ROKID_MANUFACTURING_STATUS_CACHE", "~/.hermes/brains/rokid-glasses/manufacturing_status_cache.json")
ROKID_DEVELOPER_RESOURCE_ENTRY = os.getenv("ROKID_DEVELOPER_RESOURCE_ENTRY", "~/.hermes/brains/rokid-glasses/entrypoints/developer-resource-nav-cn.md")
ROKID_PRINT_INTENT_DIR = os.getenv("ROKID_PRINT_INTENT_DIR", "~/.hermes/brains/rokid-glasses/print_intents")
LOCAL_BRAIN_ROOT = os.getenv("LOCAL_BRAIN_ROOT", "/Users/charles/Documents/brain")
HERMES_BRAINS_ROOT = os.getenv("HERMES_BRAINS_ROOT", "/Users/charles/.hermes/brains")
XIAOMI_BASE_URL = os.getenv("XIAOMI_BASE_URL", "").rstrip("/")
XIAOMI_API_KEY = os.getenv("XIAOMI_API_KEY", "")
ROKID_ACK_TEXT = os.getenv("ROKID_ACK_TEXT", "收到，我在处理。")
ROKID_PROVIDER_COOLDOWN_SECONDS = int(os.getenv("ROKID_PROVIDER_COOLDOWN_SECONDS", "20"))


def load_text_file(path: str, max_chars: int = 4000) -> str:
    try:
        with open(os.path.expanduser(path), "r", encoding="utf-8") as f:
            return f.read()[:max_chars].strip()
    except FileNotFoundError:
        return ""


ROKID_BRAIN_TEXT = load_text_file(ROKID_BRAIN_FILE)

# In-memory L1 glasses task drafts. This is intentionally lightweight and
# side-effect free: it never writes Hermes memory, taskpool, files, calendar, or
# outbound messages. Confirmed drafts only return an upgrade/background message;
# a later L2 worker can consume that event asynchronously.
TASK_SESSIONS: Dict[str, Dict[str, Any]] = {}
BACKGROUND_CONTROL_SESSIONS: Dict[str, Dict[str, Any]] = {}
ROKID_METRICS: Dict[str, Any] = {
    "requests": 0,
    "ack_sent": 0,
    "l0_hits": 0,
    "model_ok": 0,
    "model_error": 0,
    "last_model_error_at": 0.0,
    "last_model_error": "",
    "dev_reviews_recorded": 0,
    "dev_review_errors": 0,
}
_HTTP_CLIENT: Optional[httpx.AsyncClient] = None

app = FastAPI(title=APP_NAME, version="0.1.0")


class Message(BaseModel):
    role: str = "user"
    type: str = "text"
    text: Optional[str] = None
    image_url: Optional[str] = None


class RokidRequest(BaseModel):
    message_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    agent_id: str = ROKID_AGENT_ID
    message: List[Message]
    user_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None



TASK_START_PATTERNS = (
    "创建任务",
    "创建一个任务",
    "创建个任务",
    "建个任务",
    "新建任务",
    "添加任务",
    "添加后台任务",
    "后台任务",
    "变成任务",
    "作为任务",
    "帮我做",
    "帮我整理",
    "帮我规划",
    "帮我研究",
    "后台处理",
    "记一下",
    "提醒我",
    "安排一下",
)
TASK_CANCEL_PATTERNS = ("算了", "取消", "不用了", "别管", "撤销", "清空")
TASK_CONFIRM_PATTERNS = ("确认执行", "确认", "就这样", "提交", "开始处理", "去做", "执行")
TASK_MODIFY_PATTERNS = ("不对", "改成", "换成", "还是", "补充", "加上", "改一下", "修改", "等等")
TASK_ADDITIVE_PATTERNS = ("补充", "加上", "再加", "再补", "另外", "还有")
TASK_REPLACE_PATTERNS = ("不对", "改成", "换成", "还是", "不是")
TASK_STATUS_PATTERNS = (
    "是否添加成功",
    "添加成功",
    "有没有添加",
    "是否创建成功",
    "创建成功",
    "后台任务是否",
    "任务是否",
)
BACKGROUND_UPGRADE_PATTERNS = (
    "后台处理",
    "后台分析",
    "后台研究",
    "转后台",
    "长任务",
    "慢慢处理",
    "深入分析",
    "多模型分析",
    "多模型思考",
    "整理成方案",
    "发 Telegram",
    "发到 Telegram",
)
READONLY_QUERY_PATTERNS = (
    "什么",
    "多少",
    "如何",
    "怎么",
    "为什么",
    "吗",
    "有没有",
    "查一下",
    "查询",
    "状态",
    "进度",
    "日报",
    "报告",
    "新闻",
    "摘要",
    "今天",
    "最近",
    "现在",
    "当前",
)
WRITE_ACTION_PATTERNS = TASK_START_PATTERNS + BACKGROUND_UPGRADE_PATTERNS + (
    "保存",
    "入池",
    "派 worker",
    "执行一下",
    "安排",
    "创建日程",
    "发给",
    "发送",
)
ROKID_KANBAN_PATTERNS = (
    "草稿状态",
    "当前草稿",
    "我的草稿",
    "眼镜任务状态",
    "眼镜后台进度",
    "后台进度",
    "后台队列",
    "任务进度",
    "刚才的任务",
    "我刚才的任务",
)
BACKGROUND_TASK_QUERY_PATTERNS = (
    "后台任务有什么",
    "后台任务有哪些",
    "有什么后台任务",
    "当前后台任务",
    "目前的后台任务",
    "目前后台任务",
    "正在运行的后台任务",
)
BACKGROUND_TASK_CANCEL_PATTERNS = (
    "取消所有后台任务",
    "取消全部后台任务",
    "取消后台任务",
    "取消所有任务",
    "两个任务都取消",
    "两个都取消",
    "这两个任务取消",
    "都取消",
    "取消语音助手",
    "取消导航任务",
    "取消是否成功",
)
LOCATION_STATUS_PATTERNS = (
    "我在哪",
    "我在哪里",
    "现在在哪",
    "现在位置",
    "当前位置",
    "我的位置",
    "本地位置",
    "获取位置",
    "获取本地位置",
    "位置状态",
    "定位状态",
    "定位一下",
    "经纬度",
)
DEVICE_STATUS_PATTERNS = (
    "眼镜状态",
    "设备状态",
    "当前状态",
    "状态怎么样",
    "电量",
    "电池",
    "网络",
    "联网",
    "上下文",
    "收到什么上下文",
    "你收到什么",
)

CAMERA_VIEW_PATTERNS = (
    "眼前",
    "当前画面",
    "实时画面",
    "摄像头",
    "你能看到什么",
    "现在能看到什么",
    "看一下",
    "看一看",
)
SENSOR_ANALYSIS_PATTERNS = (
    "后台分析图片",
    "分析图片",
    "看图分析",
    "视觉分析",
    "复核语音",
    "语音识别复核",
    "ASR复核",
    "asr复核",
    "Whisper",
    "whisper",
)
ASR_REVIEW_PATTERNS = (
    "复核语音",
    "语音识别复核",
    "ASR复核",
    "asr复核",
    "Whisper",
    "whisper",
)
SENSOR_RESULT_STATUS_PATTERNS = (
    "传感器复核结果",
    "传感器结果",
    "视觉分析结果",
    "图片分析结果",
    "语音复核结果",
    "Whisper结果",
    "whisper结果",
)
MODEL_PROCESS_STATUS_PATTERNS = (
    "多模型进程",
    "多模型状态",
    "多模型系统状态",
    "模型进程状态",
    "模型状态",
)

def extract_user_text(payload: RokidRequest) -> str:
    parts: List[str] = []
    for msg in payload.message:
        if msg.role != "user":
            continue
        if msg.type == "text" and msg.text:
            parts.append(msg.text)
    return "\n".join(parts).strip()


def extract_image_urls(payload: RokidRequest) -> List[str]:
    return [msg.image_url for msg in payload.message if msg.role == "user" and msg.type == "image" and msg.image_url]


def session_key_for(payload: RokidRequest) -> str:
    return safe_session_key(payload, default_agent_id=ROKID_AGENT_ID)


def _contains_any(text: str, patterns: tuple[str, ...]) -> bool:
    return any(p in text for p in patterns)


def _count_markdown_files(path: Path) -> int:
    try:
        if not path.exists():
            return 0
        return sum(1 for p in path.rglob("*.md") if p.is_file())
    except OSError:
        return 0


def _intent_store_root() -> Path:
    return Path(os.path.expanduser(ROKID_UPGRADE_QUEUE_PATH)).parent


def _json_dumps(data: Dict[str, Any]) -> str:
    return json.dumps(data, ensure_ascii=False, sort_keys=True)


def _write_json_atomic(path: Path, data: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    tmp.replace(path)


def _hash_id(prefix: str, *parts: Any) -> str:
    h = hashlib.sha256()
    for part in parts:
        h.update(str(part).encode("utf-8"))
        h.update(b"\0")
    return f"{prefix}_{h.hexdigest()[:24]}"


def _extract_3mf_path_from_text(text: str) -> str:
    match = re.search(r"(/[^\s，。；;]+\.3mf)", text or "")
    return match.group(1) if match else ""


def _is_x2d_print_intent(text: str) -> bool:
    compact = re.sub(r"\s+", "", text or "")
    if not compact:
        return False
    has_print = any(p in compact for p in ("派发打印", "开始打印", "自动打印", "打印这个", "打印文件", "让打印机打印", "X2D打印", "拓竹打印"))
    has_device = any(p.lower() in compact.lower() for p in ("x2d", "拓竹", "bambu", "打印机"))
    return has_print and (has_device or ".3mf" in compact.lower())


def _enqueue_x2d_print_intent(payload: RokidRequest, user_text: str, session_key: str) -> tuple[bool, str]:
    if not _is_x2d_print_intent(user_text):
        return False, ""
    metadata = payload.metadata or {}
    three_mf = str(metadata.get("three_mf") or metadata.get("local_3mf") or _extract_3mf_path_from_text(user_text) or "")
    intent_id = _hash_id("x2dprint", session_key, user_text, time.time())
    root = Path(os.path.expanduser(ROKID_PRINT_INTENT_DIR))
    intent_path = root / "queue" / f"{intent_id}.json"
    run_dir = root / "runs" / intent_id
    autonomy = "auto" if any(p in user_text for p in ("自动打印", "自动执行", "直接打印", "无需确认")) else "confirm"
    risk_tier = "P0" if any(p in user_text for p in ("校准块", "测试块", "重复打印", "已验证")) else "auto"
    intent = {
        "schema": "hermes_rokid_x2d_print_intent_v1",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "intent_id": intent_id,
        "session_key": session_key,
        "source": "rokid",
        "user_text": user_text,
        "three_mf": three_mf,
        "autonomy": autonomy,
        "risk_tier": risk_tier,
        "requested_material": metadata.get("requested_material") or "PLA Matte",
        "requested_color": metadata.get("requested_color"),
        "status": "queued",
    }
    _write_json_atomic(intent_path, intent)
    if not three_mf:
        return True, "已进入 X2D 打印意图队列，但我还缺少 sliced 3MF 文件路径。请说：打印文件 /完整路径/job.3mf。"

    cmd = [
        sys.executable,
        str(Path.home() / ".hermes" / "scripts" / "x2d_print_intent_worker.py"),
        "--intent-json",
        str(intent_path),
        "--run-dir",
        str(run_dir),
        "--source",
        "rokid",
        "--dry-run-only",
    ]
    if autonomy == "auto":
        cmd.remove("--dry-run-only")
        cmd.append("--allow-autostart")
    try:
        subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)
    except Exception as exc:
        intent["status"] = "worker_start_failed"
        intent["error"] = type(exc).__name__
        _write_json_atomic(intent_path, intent)
        return True, "X2D 打印意图已记录，但后台 worker 启动失败，需要回到主机检查。"
    if autonomy == "auto":
        return True, "收到，已交给 X2D 自动派发 worker。它只会在 P0、材料匹配、打印机空闲、3MF 通过守卫时自动开打，否则会自动停在需要确认。"
    return True, "收到，已交给 X2D 派发 worker 做安全检查。通过后会停在确认阶段，不会直接开打。"


def _event_to_l2_status(event: Dict[str, Any]) -> str:
    status = str(event.get("status") or "")
    if status == "queued":
        return "pending_l2_upgrade"
    return status


def _read_commit_events_from_store(root: Path) -> List[Dict[str, Any]]:
    events: List[Dict[str, Any]] = []
    queue_dir = root / "queue"
    if not queue_dir.exists():
        return events
    paths = sorted({*queue_dir.glob("commit_*.json"), *queue_dir.glob("commit_*.*.json")})
    for path in paths:
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if not isinstance(data, dict):
            continue
        event_obj = data.get("source_event")
        event: Dict[str, Any] = event_obj if isinstance(event_obj, dict) else {}
        suffix_match = re.search(r"\.([a-z_]+)\.json$", path.name)
        suffix_status = suffix_match.group(1) if suffix_match else ""
        merged: Dict[str, Any] = dict(event)
        merged.update({
            "type": event.get("type") or "rokid_commit_request",
            "session_key": data.get("session_key") or event.get("session_key"),
            "title": data.get("title") or event.get("title"),
            "status": data.get("status") or _event_to_l2_status(data) or suffix_status,
            "commit_id": data.get("commit_id"),
            "output_path": data.get("output_path") or event.get("output_path"),
            "artifact_sha256": data.get("artifact_sha256") or event.get("artifact_sha256"),
            "error": data.get("error") or event.get("error"),
            "processed_at": data.get("processed_at") or event.get("processed_at"),
        })
        if suffix_status and merged.get("status") in {"queued", ""}:
            merged["status"] = _event_to_l2_status({"status": suffix_status})
        events.append(merged)
    return events


def _count_pending_l2_upgrades(path: Path) -> int:
    count = 0
    try:
        root = path.parent
        count += sum(1 for e in _read_commit_events_from_store(root) if e.get("status") == "pending_l2_upgrade")
        if path.exists():
            with path.open("r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        event = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    if event.get("status") == "pending_l2_upgrade" and not event.get("commit_id"):
                        count += 1
    except OSError:
        return 0
    return count


def _load_brain_stats_cache() -> Dict[str, Any]:
    path = Path(os.path.expanduser(ROKID_BRAIN_STATS_CACHE))
    try:
        if not path.exists():
            return {}
        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else {}
    except (OSError, json.JSONDecodeError):
        return {}


def build_brain_stats_text() -> str:
    """Return a short, read-only local-brain status for glasses voice UX."""
    local_root = Path(os.path.expanduser(LOCAL_BRAIN_ROOT))
    overlay_root = Path(os.path.expanduser(HERMES_BRAINS_ROOT))
    task_dir = local_root / "05-实践与项目" / "tasks"
    dashboard_dir = local_root / "07-仪表盘"
    queue_path = Path(os.path.expanduser(ROKID_UPGRADE_QUEUE_PATH))

    task_count = _count_markdown_files(task_dir)
    dashboard_count = _count_markdown_files(dashboard_dir)
    overlay_count = 0
    try:
        if overlay_root.exists():
            overlay_count = sum(1 for p in overlay_root.iterdir() if p.is_dir())
    except OSError:
        overlay_count = 0
    pending_count = _count_pending_l2_upgrades(queue_path)

    # macOS launchd services may not have TCC permission to read ~/Documents.
    # If direct reads are blocked, fall back to a precomputed cache stored under
    # ~/.hermes, which is safe and fast for the glasses bridge to read.
    if task_count == 0 and dashboard_count == 0:
        cache = _load_brain_stats_cache()
        task_count = int(cache.get("task_count") or task_count)
        dashboard_count = int(cache.get("dashboard_count") or dashboard_count)
        overlay_count = int(cache.get("overlay_count") or overlay_count)
    else:
        cache = _load_brain_stats_cache()

    snapshot = {
        "task_count": task_count,
        "today_task_count": int(cache.get("today_task_count") or 0) if cache else 0,
        "dashboard_count": dashboard_count,
        "overlay_count": overlay_count,
        "pending_count": pending_count,
        "recent_tasks": cache.get("recent_tasks") if cache else [],
    }
    return build_brain_stats_text_from_snapshot(snapshot)


def _read_l2_events() -> List[Dict[str, Any]]:
    path = Path(os.path.expanduser(ROKID_UPGRADE_QUEUE_PATH))
    events: List[Dict[str, Any]] = []
    seen_commit_ids = set()
    try:
        for event in _read_commit_events_from_store(path.parent):
            commit_id = event.get("commit_id")
            if commit_id:
                seen_commit_ids.add(commit_id)
            events.append(event)
        if not path.exists():
            return events
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(event, dict):
                if event.get("commit_id") and event.get("commit_id") in seen_commit_ids:
                    continue
                events.append(event)
    except OSError:
        return []
    return events


def build_rokid_kanban_text(session_key: str) -> str:
    """Return a voice-friendly mini-kanban view for this Rokid session."""
    draft = TASK_SESSIONS.get(session_key)
    events = [e for e in _read_l2_events() if (e.get("session_key") or "") == session_key]
    queued = sum(1 for e in events if e.get("status") in {"pending_l2_upgrade", "queued"})
    committing = sum(1 for e in events if e.get("status") == "committing")
    retry = sum(1 for e in events if e.get("status") == "retry")
    done = sum(1 for e in events if e.get("status") == "done")
    failed = sum(1 for e in events if e.get("status") == "failed")
    draft_text = "没有草稿"
    if draft:
        draft_text = f"草稿 v{int(draft.get('revision') or 1)}：{draft.get('title') or '未命名任务'}"
    done_events = [e for e in events if e.get("status") == "done"]
    failed_events = [e for e in events if e.get("status") == "failed"]
    extras: List[str] = []
    if done_events:
        latest = done_events[-1]
        done_text = f"最近完成：{latest.get('title') or '未命名任务'}"
        if latest.get("output_path"):
            done_text += f"，回执：{latest.get('output_path')}"
        extras.append(done_text)
    if failed_events:
        latest = failed_events[-1]
        failed_text = f"最近失败：{latest.get('title') or '未命名任务'}"
        if latest.get("error"):
            failed_text += f"，原因：{latest.get('error')}"
        extras.append(failed_text)
    extra_text = "。" + "。".join(extras) if extras else ""
    return f"眼镜任务看板：{draft_text}。队列 {queued}，执行中 {committing}，重试 {retry}，完成 {done}，失败 {failed}{extra_text}。"


def handle_rokid_kanban_query(user_text: str, session_key: str) -> tuple[bool, str]:
    text = user_text.strip()
    if not text or not _contains_any(text, ROKID_KANBAN_PATTERNS):
        return False, ""
    return True, build_rokid_kanban_text(session_key)


def _active_background_task_files(session_key: str) -> List[tuple[Path, Dict[str, Any]]]:
    root = _intent_store_root()
    queue_dir = root / "queue"
    tasks: List[tuple[Path, Dict[str, Any]]] = []
    if not queue_dir.exists():
        return tasks
    for suffix in ("queued", "committing", "retry"):
        for path in sorted(queue_dir.glob(f"commit_*.{suffix}.json")):
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                continue
            if not isinstance(data, dict):
                continue
            if (data.get("session_key") or "") != session_key:
                continue
            data.setdefault("status", suffix)
            tasks.append((path, data))
    return tasks


def build_background_task_list_text(session_key: str) -> str:
    tasks = _active_background_task_files(session_key)
    BACKGROUND_CONTROL_SESSIONS[session_key] = {
        "last_query_at": int(time.time()),
        "last_listed": [t.get("title") or "未命名任务" for _, t in tasks],
    }
    if not tasks:
        return "目前没有正在排队或执行的眼镜后台任务。不会取消模型编造的任务。"
    parts = []
    for idx, (_, task) in enumerate(tasks[:5], 1):
        title = str(task.get("title") or "未命名任务")
        status = str(task.get("status") or "queued")
        parts.append(f"{idx}. {title}（{status}）")
    more = f"另有 {len(tasks) - 5} 个。" if len(tasks) > 5 else ""
    return "当前真实后台任务：" + "；".join(parts) + "。" + more


def _matches_cancel_request(text: str, title: str) -> bool:
    compact_text = re.sub(r"\s+", "", text)
    compact_title = re.sub(r"\s+", "", title)
    if "所有" in compact_text or "全部" in compact_text or "都取消" in compact_text:
        return True
    if compact_title and compact_title in compact_text:
        return True
    for token in re.split(r"[，,。；;、\s]+", compact_title):
        if len(token) >= 4 and token in compact_text:
            return True
    return False


def cancel_background_tasks(session_key: str, user_text: str) -> tuple[int, List[str]]:
    canceled = 0
    titles: List[str] = []
    for path, task in _active_background_task_files(session_key):
        title = str(task.get("title") or "未命名任务")
        if not _matches_cancel_request(user_text, title):
            continue
        task["status"] = "canceled"
        task["canceled_at"] = int(time.time())
        canceled_path = path.with_name(re.sub(r"\.(queued|committing|retry)\.json$", ".canceled.json", path.name))
        _write_json_atomic(canceled_path, task)
        try:
            path.unlink()
        except FileNotFoundError:
            pass
        canceled += 1
        titles.append(title)
    BACKGROUND_CONTROL_SESSIONS[session_key] = {
        "last_cancel_at": int(time.time()),
        "last_cancel_count": canceled,
        "last_cancel_titles": titles,
    }
    return canceled, titles


def handle_background_task_control(user_text: str, session_key: str) -> tuple[bool, str]:
    text = user_text.strip()
    if not text:
        return False, ""
    # If the user is asking whether a just-created draft was added, let the
    # task-draft state machine answer from the active draft instead of treating
    # it as a durable background queue query.
    if TASK_SESSIONS.get(session_key) and _contains_any(text, TASK_STATUS_PATTERNS):
        return False, ""
    if "取消是否成功" in text or "取消成功" in text:
        last = BACKGROUND_CONTROL_SESSIONS.get(session_key) or {}
        count = int(last.get("last_cancel_count") or 0)
        titles_obj = last.get("last_cancel_titles")
        titles = titles_obj if isinstance(titles_obj, list) else []
        if count:
            title_text = "；".join(str(x) for x in titles[:3])
            return True, f"刚才已取消 {count} 个后台任务：{title_text}。"
        return True, "没有找到刚才已取消的真实后台任务记录。"
    if _contains_any(text, BACKGROUND_TASK_CANCEL_PATTERNS):
        count, titles = cancel_background_tasks(session_key, text)
        if count:
            return True, f"已取消 {count} 个真实后台任务：{'；'.join(titles[:3])}。"
        return True, "没有找到可取消的真实后台任务。我不会取消模型刚才编造的任务。"
    if _contains_any(text, BACKGROUND_TASK_QUERY_PATTERNS):
        return True, build_background_task_list_text(session_key)
    return False, ""


def handle_local_brain_query(user_text: str) -> tuple[bool, str]:
    text = user_text.strip()
    if not text or not _contains_any(text, BRAIN_STATS_PATTERNS):
        return False, ""
    return True, build_brain_stats_text()


def _load_daily_brief_cache() -> Dict[str, Any]:
    path = Path(os.path.expanduser(ROKID_DAILY_BRIEF_CACHE))
    try:
        if not path.exists():
            return {}
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except (OSError, json.JSONDecodeError):
        return {}


PHOTO_PRINT_ACTION_PATTERNS = (
    "打印",
    "直接打印",
    "开始打印",
    "拍照打印",
    "照片打印",
    "3D打印",
    "三维打印",
    "拓竹",
    "Bambu",
    "X2D",
)

HIGH_IMPACT_ACTION_PATTERNS = (
    "发 Telegram",
    "发到 Telegram",
    "发消息",
    "发送",
    "发给",
    "创建日程",
    "添加日程",
    "提醒我",
    "导航到",
    "开始导航",
    "控制设备",
) + PHOTO_PRINT_ACTION_PATTERNS

def handle_photo_print_request(payload: RokidRequest, user_text: str) -> tuple[bool, str]:
    text = user_text.strip()
    if _is_x2d_print_intent(text):
        return False, ""
    if not text or not _contains_any(text, PHOTO_PRINT_ACTION_PATTERNS):
        return False, ""
    has_image = bool(extract_image_urls(payload))
    if has_image:
        return True, "眼镜可以触发拍照打印流程，但不能直接开打。我会先生成模型/切片/预检草稿；请确认模型和切片预览后，再说确认打印。"
    return True, "打印属于高影响物理动作，不能直接执行。请先指定已确认的本地模型和切片预览；确认后才能进入外控打印门。"


def handle_image_placeholder(payload: RokidRequest, user_text: str) -> tuple[bool, str]:
    images = extract_image_urls(payload)
    if not images:
        return False, ""
    if _contains_any(user_text, BACKGROUND_UPGRADE_PATTERNS + ("后台分析图片", "分析图片", "看图分析")):
        return False, ""
    return True, "我收到了图片，但当前还没启用可靠视觉识别。请补充文字，或说“后台分析图片”。"


def handle_sensor_analysis_request(payload: RokidRequest, user_text: str) -> tuple[bool, str]:
    """Create background-only sensor jobs for image analysis or Whisper ASR review."""
    text = user_text.strip()
    if not text or _contains_any(text, SENSOR_RESULT_STATUS_PATTERNS) or not _contains_any(text, SENSOR_ANALYSIS_PATTERNS):
        return False, ""
    sensor_context = build_sensor_context(payload)
    pieces = []
    images = sensor_context.get("image", {}) if isinstance(sensor_context.get("image"), dict) else {}
    audio = sensor_context.get("audio", {}) if isinstance(sensor_context.get("audio"), dict) else {}
    if images.get("count") and _contains_any(text, ("图片", "看图", "视觉", "后台分析", "分析")):
        job_path = create_image_analysis_job(sensor_context, question=text)
        pieces.append(f"后台视觉分析已排队：{job_path.name}。会使用 supervision/OpenCV 能力状态做结构化分析；当前不阻塞眼镜快答，也不会编造画面。")
    if _contains_any(text, ASR_REVIEW_PATTERNS):
        job_path = create_whisper_review_job(sensor_context)
        if audio.get("available"):
            pieces.append(f"Whisper 语音复核已排队：{job_path.name}。")
        else:
            pieces.append(f"已记录 Whisper 语音复核请求：{job_path.name}，但本次 payload 没有音频，只能 fail-soft 等待眼镜端提供音频。")
    if pieces:
        return True, " ".join(pieces)
    if _contains_any(text, ("图片", "看图", "视觉")):
        return True, "本次没有图片输入，不能做视觉分析。请先用眼镜拍照并发送，再说“后台分析图片”。"
    return False, ""


def handle_sensor_result_status_query(user_text: str) -> tuple[bool, str]:
    if not _contains_any(user_text, SENSOR_RESULT_STATUS_PATTERNS):
        return False, ""
    processed = process_sensor_queue(limit=20)
    summary = summarize_latest_sensor_result()
    if processed:
        return True, f"已处理 {len(processed)} 个传感器后台任务。{summary}"
    return True, summary


def handle_high_impact_action_request(user_text: str) -> tuple[bool, str]:
    text = user_text.strip()
    if not text or not _contains_any(text, HIGH_IMPACT_ACTION_PATTERNS):
        return False, ""
    action = _normalize_task_title(text)
    return True, f"这是高影响动作，我先生成确认草稿：{action}。要执行请说“确认执行”。"


def _first_scalar_from_context(payload: RokidRequest, *keys: str) -> str:
    ctx = extract_device_context(payload, default_agent_id=ROKID_AGENT_ID).device_context
    for key in keys:
        value = ctx.get(key) if isinstance(ctx, dict) else None
        if value is None:
            continue
        if isinstance(value, (dict, list)):
            continue
        text = str(value).strip()
        if text:
            return text
    return ""


def build_weather_status_text(payload: RokidRequest) -> str:
    """Return a short weather answer from Rokid-supplied read-only context."""
    weather = _first_scalar_from_context(payload, "weather", "current_weather", "weather_text", "condition")
    temperature = _first_scalar_from_context(payload, "temperature", "temp", "current_temperature")
    city = _first_scalar_from_context(payload, "city", "district", "address", "location")
    update_time = _first_scalar_from_context(payload, "weather_time", "current_time", "timestamp", "time")
    parts = []
    if city:
        parts.append(f"位置：{city}")
    if weather:
        parts.append(f"天气：{weather}")
    if temperature and temperature not in weather:
        parts.append(f"温度：{temperature}")
    if update_time:
        parts.append(f"时间：{update_time}")
    if not parts:
        return "这次请求没有带天气插件结果或天气上下文；我不会编造实时天气。请确认灵珠天气权限/插件已启用后再问一次。"
    return "；".join(parts[:4]) + "。来自本次眼镜请求的只读天气上下文，未写入后台。"


def _safe_calculate_expression(user_text: str) -> str:
    """Evaluate a tiny arithmetic subset for low-risk calculator fallback."""
    import ast
    import operator

    text = str(user_text or "")
    expr = text
    for marker in ("帮我算", "算一下", "算下", "算算", "计算", "计算器", "等于多少"):
        expr = expr.replace(marker, "")
    expr = expr.replace("×", "*").replace("÷", "/").replace("＋", "+").replace("－", "-")
    expr = re.sub(r"[^0-9+\-*/().% ]", "", expr).strip()
    if not expr or not re.search(r"\d", expr):
        return "计算器可用。请说出具体算式，例如：帮我算 23 乘以 19 加 7。"

    operators = {
        ast.Add: operator.add,
        ast.Sub: operator.sub,
        ast.Mult: operator.mul,
        ast.Div: operator.truediv,
        ast.Mod: operator.mod,
        ast.USub: operator.neg,
        ast.UAdd: operator.pos,
    }

    def eval_node(node: ast.AST) -> float:
        if isinstance(node, ast.Expression):
            return eval_node(node.body)
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
            return float(node.value)
        if isinstance(node, ast.UnaryOp) and type(node.op) in operators:
            return operators[type(node.op)](eval_node(node.operand))
        if isinstance(node, ast.BinOp) and type(node.op) in operators:
            return operators[type(node.op)](eval_node(node.left), eval_node(node.right))
        raise ValueError("unsupported")

    try:
        result = eval_node(ast.parse(expr, mode="eval"))
    except Exception:
        return "这个算式我没有安全解析出来；请只说数字和加减乘除。"
    if abs(result - int(result)) < 1e-9:
        result_text = str(int(result))
    else:
        result_text = f"{result:.6g}"
    return f"计算结果：{expr} = {result_text}。这是 Hermes 本地安全计算兜底。"


def _extract_navigation_destination(user_text: str) -> str:
    text = str(user_text or "").strip()
    for marker in ("导航到", "路线到", "带我去", "去哪里怎么走"):
        if marker in text:
            dest = text.split(marker, 1)[1].strip(" ，。！？?：:")
            if dest:
                return dest[:40]
    return "你说的目的地"


def build_photo_degraded_answer(payload: RokidRequest) -> str:
    images = extract_image_urls(payload)
    if images:
        return "拍照插件没有返回平台回执；我降级为图片接收模式：本次请求已经带有图片，我可以继续做后台视觉分析、打印预检或文字说明，但不会声称眼镜拍照动作由 Hermes 完成。"
    return "拍照插件没有返回平台回执；我降级为拍照引导模式：请用眼镜系统拍照并发送图片。收到图片后，我可以继续做后台视觉分析、打印预检或文字说明，但不会声称已经替你完成拍照。"


def build_navigation_degraded_answer(user_text: str) -> str:
    destination = _extract_navigation_destination(user_text)
    return f"导航插件没有返回平台回执；我降级为路线准备模式：目的地是{destination}。请在灵珠或地图端确认目的地后发起导航；我不能在没有平台回执时声称导航已经启动。"


def build_local_plugin_fallback_answer(payload: RokidRequest, user_text: str, capability: str) -> str | None:
    """Keep safe Lingzhu plugin intents usable even when no platform receipt arrives."""
    if capability == "weather":
        return build_weather_status_text(payload)
    if capability == "device_info":
        return build_device_status_text(payload)
    if capability == "location":
        return build_location_status_text(payload)
    if capability == "calculator":
        return _safe_calculate_expression(user_text)
    if capability == "photo":
        return build_photo_degraded_answer(payload)
    if capability == "navigation":
        return build_navigation_degraded_answer(user_text)
    return None


def handle_lingzhu_plugin_request(payload: RokidRequest, user_text: str) -> tuple[bool, str]:
    """Recognize Lingzhu native-plugin capabilities before model fallback.

    Hermes does not execute high-risk platform plugins through SSE. If Lingzhu
    supplies an explicit plugin receipt, use it. For low-risk/read-only
    capabilities, keep the glasses usable by answering from the current request
    context or deterministic local fallback instead of stopping at "no receipt".
    """
    plugin = match_lingzhu_plugin(user_text)
    if plugin is None:
        return False, ""
    plugin_context = extract_lingzhu_plugin_context(payload.metadata)
    if can_execute_plugin(plugin, plugin_context):
        return True, build_plugin_receipted_answer(plugin, plugin_context)
    local_answer = build_local_plugin_fallback_answer(payload, user_text, plugin.capability)
    if local_answer:
        return True, local_answer
    return True, build_plugin_unavailable_answer(plugin, user_text)


def handle_orphan_action_confirmation(user_text: str, session_key: str) -> tuple[bool, str]:
    """Reject bare confirmation/execution utterances with no pending local draft."""
    if not is_bare_confirmation_intent(user_text):
        return False, ""
    if has_pending_confirmation(session_key, task_sessions=TASK_SESSIONS):
        return False, ""
    return True, orphan_confirmation_answer()


def make_voice_safe_answer(answer: str) -> str:
    """Post-guard model output for glasses: short, no tables, no fake execution."""
    text = str(answer or "").strip()
    if not text:
        return "我在，但刚才没有生成有效回复，请再说一遍。"
    if _contains_any(text, UNSAFE_EXECUTION_CLAIMS):
        return rewrite_unsafe_execution_claim(text)
    # Tables and long markdown are hostile to voice playback. Keep a concise summary
    # and explicitly offer the background path for long form content.
    has_table = "|" in text or "\n#" in text or text.startswith("#")
    if len(text) > 220 or has_table:
        flat = re.sub(r"[#*_`|>-]+", "", text)
        flat = re.sub(r"\s+", " ", flat).strip()
        return f"简要说：{flat[:120]}。需要长内容，可以说“后台处理”。"
    return text


def build_daily_brief_text() -> str:
    return build_daily_brief_text_from_cache(_load_daily_brief_cache())


def _extract_resource_url(resource_text: str, label: str, fallback: str) -> str:
    for line in resource_text.splitlines():
        if label in line and "http" in line:
            match = re.search(r"https?://[^\s｜|]+", line)
            if match:
                return match.group(0).rstrip("。。，,")
    return fallback


def build_rokid_developer_resource_text() -> str:
    """Return a short read-only developer-resource entry answer for glasses."""
    text = load_text_file(ROKID_DEVELOPER_RESOURCE_ENTRY, max_chars=8000)
    open_platform = _extract_resource_url(text, "Rokid开放平台", "https://open.rokid.com/")
    sprite = _extract_resource_url(text, "YodaOS-Sprite", "https://open.rokid.com/sprite?lang=zh")
    sdk = _extract_resource_url(text, "SDK开放文档", "https://open.rokid.com/sdk?lang=zh")
    agent = _extract_resource_url(text, "灵珠Agent", "https://rizon.rokid.com/space/home")
    return f"Rokid开发入口：Rokid开放平台 {open_platform}；YodaOS-Sprite {sprite}；SDK文档 {sdk}；灵珠Agent {agent}。只读导航，未写后台。"


def handle_rokid_developer_resource_query(user_text: str) -> tuple[bool, str]:
    text = user_text.strip()
    if not text or not _contains_any(text, ROKID_DEVELOPER_RESOURCE_PATTERNS):
        return False, ""
    return True, build_rokid_developer_resource_text()


def _load_manufacturing_status_cache() -> Dict[str, Any]:
    path = Path(os.path.expanduser(ROKID_MANUFACTURING_STATUS_CACHE))
    try:
        if not path.exists():
            return {}
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except (OSError, json.JSONDecodeError):
        return {}


def build_manufacturing_status_text() -> str:
    """Return a short, read-only manufacturing/Bambu status from local cache only."""
    return build_manufacturing_status_text_from_cache(_load_manufacturing_status_cache())


def handle_manufacturing_status_query(user_text: str) -> tuple[bool, str]:
    text = user_text.strip()
    if not text or not _contains_any(text, MANUFACTURING_STATUS_PATTERNS):
        return False, ""
    return True, build_manufacturing_status_text()


def build_location_status_text(payload: RokidRequest) -> str:
    """Return a short, read-only location self-report from Rokid metadata."""
    ctx = extract_device_context(payload, default_agent_id=ROKID_AGENT_ID)
    status = ctx.get_location_status()
    if not status.get("is_read_only"):
        return "定位信息不可用；我不会写入后台任务。"
    if not status.get("has_location"):
        return "这次请求没有带定位信息。我不会猜位置，也不会写入后台任务。"
    parts = []
    location = str(status.get("location") or "").strip()
    if location and location != "unknown":
        parts.append(f"位置：{location}")
    if status.get("has_coordinates"):
        parts.append(f"经纬度：{status.get('latitude')}，{status.get('longitude')}")
    if status.get("accuracy") is not None:
        parts.append(f"精度约 {status.get('accuracy')}")
    if status.get("timestamp") is not None:
        parts.append(f"时间 {status.get('timestamp')}")
    if not parts:
        return "这次请求没有可播报的定位信息。我不会猜位置，也不会写入后台任务。"
    return "；".join(parts[:4]) + "。仅本次只读播报，未写入后台。"


def handle_location_status_query(payload: RokidRequest, user_text: str) -> tuple[bool, str]:
    text = user_text.strip()
    if not text or not _contains_any(text, LOCATION_STATUS_PATTERNS):
        return False, ""
    return True, build_location_status_text(payload)


def build_device_status_text(payload: RokidRequest) -> str:
    """Return a short, read-only device/context self-report from Rokid metadata."""
    ctx = extract_device_context(payload, default_agent_id=ROKID_AGENT_ID)
    status = ctx.get_device_status()
    battery = str(status.get("battery") or "unknown")
    network = str(status.get("network") or "unknown")
    device = str(status.get("device") or "unknown")
    image_count = int(status.get("image_count") or 0)
    keys = [str(k) for k in (status.get("context_keys") or [])]

    parts = []
    parts.append(f"电量：{battery}" if battery != "unknown" else "电量未知")
    parts.append(f"网络：{network}" if network != "unknown" else "网络未知")
    if device != "unknown":
        parts.append(f"设备：{device}")
    if keys:
        parts.append("上下文字段：" + "、".join(keys[:6]))
    else:
        parts.append("上下文为空")
    if image_count:
        parts.append(f"图片 {image_count} 张，只记录数量不读取内容")
    suffix = "仅本次只读，未写入后台。"
    if battery == "unknown" or network == "unknown":
        suffix = "缺失字段不会猜测；" + suffix
    return "；".join(parts[:5]) + "。" + suffix


def handle_device_status_query(payload: RokidRequest, user_text: str) -> tuple[bool, str]:
    text = user_text.strip()
    if not text or not _contains_any(text, DEVICE_STATUS_PATTERNS):
        return False, ""
    return True, build_device_status_text(payload)


def handle_camera_view_query(payload: RokidRequest, user_text: str) -> tuple[bool, str]:
    text = user_text.strip()
    if not text or not _contains_any(text, CAMERA_VIEW_PATTERNS):
        return False, ""
    images = extract_image_urls(payload)
    if images:
        return True, f"这次请求带了 {len(images)} 张图片，但眼镜端当前只确认收到图片，不在快答里编造画面内容。要可靠识别，请说“后台分析图片”。"
    return True, "我目前没有收到图片，也没有开启实时摄像头画面；不能看见眼前环境。请先用眼镜拍照保存并发送，或说“后台分析图片”。"


def build_model_process_status_text() -> str:
    ok = int(ROKID_METRICS.get("model_ok") or 0)
    err = int(ROKID_METRICS.get("model_error") or 0)
    last = str(ROKID_METRICS.get("last_model_error") or "无")
    cooldown = "冷却中" if _provider_in_cooldown() else "可尝试"
    return f"眼镜快答模型：成功 {ok} 次，失败 {err} 次，最近错误：{last}，当前{cooldown}。多模型认证属于后台长任务；要详细状态请说“后台处理多模型状态”。"


def handle_model_process_status_query(user_text: str) -> tuple[bool, str]:
    text = user_text.strip()
    if not text or not _contains_any(text, MODEL_PROCESS_STATUS_PATTERNS):
        return False, ""
    return True, build_model_process_status_text()


def handle_l0_query(user_text: str) -> tuple[bool, str]:
    text = user_text.strip()
    if not text:
        return False, ""
    route = match_text_route(text, L0_TEXT_ROUTE_REGISTRY)
    if route is None:
        return False, ""
    if route.route_id == "access_layer":
        return True, build_access_layer_text()
    if route.route_id == "capability":
        return True, build_capability_text()
    if route.route_id == "manufacturing_status":
        return True, build_manufacturing_status_text()
    if route.route_id == "daily_brief":
        return True, build_daily_brief_text()
    if route.route_id == "rokid_developer_resources":
        return True, build_rokid_developer_resource_text()
    if route.route_id == "local_brain_stats":
        return True, build_brain_stats_text()
    return False, ""


def _normalize_task_title(text: str) -> str:
    title = text.strip()
    title = re.sub(r"^(后台[。\.，,:：\s]*)?(添加后台任务|添加任务|后台任务)[，,:：\s]*", "", title)
    title = re.sub(r"^(帮我|请|麻烦你)?(创建|新建|建个|做个)?(一个|个)?任务[，,:：\s]*", "", title)
    title = re.sub(r"^(帮我|请|麻烦你)?(把|将)?", "", title)
    title = title.replace("变成任务", "")
    title = title.replace("作为任务", "")
    for marker in ("不对", "改成", "换成", "还是", "补充", "加上", "改一下", "等等"):
        title = title.replace(marker, "")
    title = re.sub(r"^(再|另外|还有)[，,:：\s]*", "", title)
    title = re.sub(r"[，,。；;\s]+", " ", title).strip()
    return title or "未命名任务"


def _is_additive_modification(text: str) -> bool:
    # Glasses voice input often arrives as clipped follow-up fragments
    # (e.g. “常规需求”, “多模型思考，拍照对话”). Unless the user explicitly says
    # “不对/改成/换成/还是/不是”, preserve previous draft context and append.
    return not _contains_any(text, TASK_REPLACE_PATTERNS)


def classify_l2_upgrade_intent(user_text: str) -> str:
    """Classify whether model failure may be persisted as background work.

    This is intentionally conservative: glasses voice input is noisy, so only
    explicit write/background/task intents may become L2 work. Read-only
    questions such as “今天日报有什么” must fail soft instead of polluting the
    durable queue.
    """
    text = user_text.strip()
    if not text:
        return "chitchat"
    if _contains_any(text, BACKGROUND_UPGRADE_PATTERNS):
        return "background"
    if _contains_any(text, TASK_START_PATTERNS):
        return "task"
    if _contains_any(text, READONLY_QUERY_PATTERNS):
        return "query"
    if _contains_any(text, WRITE_ACTION_PATTERNS):
        return "write_action"
    return "chitchat"


def should_enqueue_l2_on_model_failure(user_text: str) -> bool:
    return classify_l2_upgrade_intent(user_text) in {"background", "task", "write_action"}


def fallback_answer_for_model_failure(user_text: str, reason: str) -> str:
    intent = classify_l2_upgrade_intent(user_text)
    if intent == "query":
        if "日报" in (user_text or ""):
            return "网络有点慢，日报需要联网读取。你可以再问一次，或说“后台查日报”让我查完发 Telegram。"
        return "网络有点慢，我还在。你可以直接继续问；如果要长内容，说“后台处理”。"
    if intent == "chitchat":
        return "我在，刚才网络慢没接上。你继续说，我会尽量短答。"
    return "网络有点慢，刚才没生成出来。你可以再说一遍，或明确说“后台处理”。"


def _intent_ledger_event_from_upgrade(event: Dict[str, Any]) -> tuple[Dict[str, Any], Dict[str, Any], Dict[str, Any], Dict[str, Any]]:
    now = int(time.time())
    title = str(event.get("title") or "未命名任务")
    history_obj = event.get("history")
    history: List[Any] = history_obj if isinstance(history_obj, list) else []
    raw_transcript = "\n".join(str(x) for x in history) or str(event.get("prompt") or title)
    session_key = str(event.get("session_key") or "")
    created_at = int(event.get("created_at") or now)
    event_id = str(event.get("event_id") or _hash_id("evt", session_key, raw_transcript, created_at))
    candidate_id = str(event.get("candidate_id") or _hash_id("cand", event_id, title))
    confirmation_id = str(event.get("confirmation_id") or _hash_id("cfm", candidate_id, event.get("confirmed_at") or created_at))
    idempotency_key = str(event.get("idempotency_key") or _hash_id("idem", session_key, title, raw_transcript))
    commit_id = str(event.get("commit_id") or _hash_id("commit", idempotency_key))
    capture_event = {
        "event_id": event_id,
        "session_key": session_key,
        "source": "rokid-glasses",
        "input_mode": "voice",
        "raw_transcript": raw_transcript,
        "transcript_hash": hashlib.sha256(raw_transcript.encode("utf-8")).hexdigest(),
        "created_at": created_at,
        "privacy_level": "normal",
    }
    candidate = {
        "candidate_id": candidate_id,
        "event_id": event_id,
        "intent_type": event.get("intent") or event.get("type") or "brain_task",
        "title_draft": title,
        "body_draft": raw_transcript,
        "confidence": 1.0,
        "risk_level": "medium",
        "duplicate_candidates": [],
        "status": "needs_confirm" if event.get("type") != "rokid_task_confirmed" else "confirmed",
        "created_at": created_at,
    }
    confirmation = {
        "confirmation_id": confirmation_id,
        "candidate_id": candidate_id,
        "confirmation_token": _hash_id("tok", confirmation_id, idempotency_key),
        "prompt_text": f"创建后台任务：{title}",
        "user_response": "confirmed" if event.get("type") == "rokid_task_confirmed" else "implicit_background_upgrade",
        "confirmed_text": title,
        "confirmed_at": int(event.get("confirmed_at") or created_at),
        "status": "confirmed",
    }
    source_event = dict(event)
    source_event.update({
        "event_id": event_id,
        "candidate_id": candidate_id,
        "confirmation_id": confirmation_id,
        "commit_id": commit_id,
        "idempotency_key": idempotency_key,
    })
    commit = {
        "commit_id": commit_id,
        "candidate_id": candidate_id,
        "confirmation_id": confirmation_id,
        "idempotency_key": idempotency_key,
        "target_system": "local_brain_task",
        "session_key": session_key,
        "title": title,
        "status": "queued",
        "retry_count": int(event.get("retry_count") or 0),
        "created_at": now,
        "source_event": source_event,
    }
    return capture_event, candidate, confirmation, commit


def record_l2_upgrade_event(event: Dict[str, Any]) -> None:
    root = _intent_store_root()
    now = int(time.time())
    event.setdefault("status", "pending_l2_upgrade")
    event.setdefault("created_at", now)
    capture_event, candidate, confirmation, commit = _intent_ledger_event_from_upgrade(event)

    ledger_path = root / "ledger" / "events.jsonl"
    ledger_path.parent.mkdir(parents=True, exist_ok=True)
    with ledger_path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(capture_event, ensure_ascii=False) + "\n")
    _write_json_atomic(root / "candidates" / f"{candidate['candidate_id']}.json", candidate)
    _write_json_atomic(root / "confirmations" / f"{confirmation['confirmation_id']}.json", confirmation)
    queued_path = root / "queue" / f"{commit['commit_id']}.queued.json"
    if not any((root / "queue" / f"{commit['commit_id']}.{suffix}.json").exists() for suffix in ("queued", "committing", "done", "failed")):
        _write_json_atomic(queued_path, commit)

    # Legacy JSONL mirror for backwards compatibility with older tools/tests.
    path = os.path.expanduser(ROKID_UPGRADE_QUEUE_PATH)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    legacy_event = dict(event)
    legacy_event.update(commit["source_event"])
    legacy_event["status"] = "pending_l2_upgrade"
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(legacy_event, ensure_ascii=False) + "\n")


def record_upgrade_event(session_key: str, draft: Dict[str, Any]) -> None:
    event = {
        "type": "rokid_task_confirmed",
        "session_key": session_key,
        "title": draft.get("title") or "未命名任务",
        "revision": draft.get("revision", 1),
        "history": draft.get("history", []),
        "created_at": draft.get("created_at"),
        "confirmed_at": int(time.time()),
        "status": "pending_l2_upgrade",
    }
    record_l2_upgrade_event(event)


def handle_task_dialogue(user_text: str, session_key: str) -> tuple[bool, str]:
    """L1 task-draft state machine for glasses multi-turn interruptions.

    Returns (handled, answer). When handled is True, the answer is final for the
    current SSE request and no model/tool path should run. Drafts may be modified
    indefinitely; no side effects happen until a future L2 upgrade consumes a
    confirmed event.
    """
    text = user_text.strip()
    if not text:
        return False, ""

    pending = TASK_SESSIONS.get(session_key)

    if pending and _contains_any(text, TASK_CANCEL_PATTERNS):
        TASK_SESSIONS.pop(session_key, None)
        return True, "已取消这个任务草稿。"

    if pending and _contains_any(text, TASK_CONFIRM_PATTERNS):
        title = str(pending.get("title") or "未命名任务")
        record_upgrade_event(session_key, pending)
        TASK_SESSIONS.pop(session_key, None)
        return True, f"已确认，我会后台处理：{title}。长结果回 Telegram。"

    if pending and _contains_any(text, TASK_STATUS_PATTERNS):
        title = str(pending.get("title") or "未命名任务")
        revision = int(pending.get("revision") or 1)
        return True, f"已添加为任务草稿 v{revision}：{title}。还没正式入后台；要执行请说“确认执行”。"

    starts_task = _contains_any(text, TASK_START_PATTERNS)
    modifies_task = pending is not None and (_contains_any(text, TASK_MODIFY_PATTERNS) or bool(text))

    if not starts_task and not modifies_task:
        return False, ""

    title = _normalize_task_title(text)
    now = int(time.time())

    if pending:
        if _is_additive_modification(text):
            previous_title = str(pending.get("title") or "").strip()
            if previous_title and title not in previous_title:
                title = f"{previous_title}；{title}"
        pending["title"] = title
        pending["revision"] = int(pending.get("revision", 1)) + 1
        pending["updated_at"] = now
        history = pending.setdefault("history", [])
        history.append(text)
        return True, f"已更新任务草稿 v{pending['revision']}：{title}。继续修改，或说“确认执行”。"

    TASK_SESSIONS[session_key] = {
        "status": "drafting",
        "title": title,
        "revision": 1,
        "created_at": now,
        "updated_at": now,
        "history": [text],
        "executed": False,
    }
    return True, f"已生成任务草稿 v1：{title}。你可以继续修改，或说“确认执行”。"

def check_auth(authorization: Optional[str]) -> None:
    if not ROKID_AGENT_AK:
        # Fail closed. Do not expose Hermes if token is not configured.
        raise HTTPException(status_code=500, detail="ROKID_AGENT_AK is not configured")
    expected = f"Bearer {ROKID_AGENT_AK}"
    if authorization != expected:
        raise HTTPException(status_code=401, detail="invalid bearer token")


def extract_user_prompt(payload: RokidRequest) -> str:
    ctx = extract_device_context(payload, default_agent_id=ROKID_AGENT_ID)
    user_text = ctx.user_text or ("[用户发送了一张图片]" if ctx.images else "你好")

    context = ctx.device_context
    context_lines = []
    for key in ["location", "latitude", "longitude", "weather", "battery"]:
        if context.get(key) is not None:
            context_lines.append(f"- {key}: {context.get(key)}")

    system_hint = (
        "你正在通过 Rokid 智能眼镜和用户对话。请优先给出适合眼镜/语音场景的短回答。"
        "如果问题复杂，先给结论和最重要的下一步，不要输出长 Markdown 表格。"
        "涉及写入记忆、发消息、控制设备、创建任务等高影响操作时，先明确确认。"
    )
    prompt = f"{system_hint}\n\n"
    if context_lines:
        prompt += "设备上下文:\n" + "\n".join(context_lines) + "\n\n"
    if ctx.images:
        prompt += f"图片输入：收到 {len(ctx.images)} 张图片；未启用视觉识别时不要描述图片内容。\n\n"
    prompt += f"用户: {user_text}"
    return prompt[:MAX_PROMPT_CHARS]


def build_hermes_cmd(prompt: str) -> List[str]:
    cmd = [HERMES_BIN, "chat", "-q", prompt, "--quiet", "--max-turns", "1"]
    if HERMES_PROVIDER:
        cmd += ["--provider", HERMES_PROVIDER]
    if HERMES_MODEL:
        cmd += ["-m", HERMES_MODEL]
    return cmd


async def run_hermes(prompt: str) -> str:
    cmd = build_hermes_cmd(prompt)
    # subprocess.run is blocking; move it off the event loop.
    def _run() -> str:
        try:
            completed = subprocess.run(
                cmd,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=HERMES_TIMEOUT_SECONDS,
            )
        except subprocess.TimeoutExpired:
            return "我这边处理超时了，可以把问题缩短一点再试。"
        if completed.returncode != 0:
            err = completed.stderr.strip()[-500:]
            return f"Hermes 暂时调用失败：{err or 'unknown error'}"
        return completed.stdout.strip() or "我收到了，但没有生成有效回复。"

    return await asyncio.to_thread(_run)


def _xiaomi_chat_completions_url() -> str:
    if not XIAOMI_BASE_URL:
        return ""
    if XIAOMI_BASE_URL.endswith("/chat/completions"):
        return XIAOMI_BASE_URL
    if XIAOMI_BASE_URL.endswith("/v1"):
        return XIAOMI_BASE_URL + "/chat/completions"
    return XIAOMI_BASE_URL + "/v1/chat/completions"


def _fast_system_prompt() -> str:
    """Tiny glasses prompt: keep L1 payload small for domestic high-latency links."""
    return (
        "你是 Hermes 的 Rokid 眼镜快速模式。中文短答，适合语音播报；"
        "默认 60 字内，最多 3 点。先回答结论，不输出 Markdown 表格。"
        "写入记忆、发消息、日程、导航、任务执行等高影响动作必须先要求确认，不能声称已执行。"
        "如果用户让后台处理，只确认已转后台，不展开长篇。"
    )


def _provider_in_cooldown() -> bool:
    last_error_at = float(ROKID_METRICS.get("last_model_error_at") or 0.0)
    return bool(last_error_at and (time.time() - last_error_at) < ROKID_PROVIDER_COOLDOWN_SECONDS)


async def _get_http_client() -> httpx.AsyncClient:
    global _HTTP_CLIENT
    if _HTTP_CLIENT is None or _HTTP_CLIENT.is_closed:
        timeout = httpx.Timeout(
            connect=3.0,
            read=float(ROKID_FAST_TIMEOUT_SECONDS),
            write=5.0,
            pool=3.0,
        )
        limits = httpx.Limits(max_keepalive_connections=8, max_connections=16, keepalive_expiry=60.0)
        _HTTP_CLIENT = httpx.AsyncClient(timeout=timeout, limits=limits, http2=True)
    return _HTTP_CLIENT


@app.on_event("shutdown")
async def _close_http_client() -> None:
    global _HTTP_CLIENT
    if _HTTP_CLIENT is not None and not _HTTP_CLIENT.is_closed:
        await _HTTP_CLIENT.aclose()


async def run_fast_model(prompt: str) -> str:
    """Fast path for glasses: pooled async HTTP, no full Hermes CLI cold start."""
    if not XIAOMI_API_KEY or not XIAOMI_BASE_URL:
        raise RuntimeError("XIAOMI_API_KEY/XIAOMI_BASE_URL not configured")
    if _provider_in_cooldown():
        raise RuntimeError("fast provider temporarily cooling down")

    body = {
        "model": ROKID_FAST_MODEL,
        "messages": [
            {"role": "system", "content": _fast_system_prompt()},
            {"role": "user", "content": prompt[:1200]},
        ],
        "temperature": 0.2,
        "max_tokens": min(ROKID_FAST_MAX_TOKENS, 220),
    }
    client = await _get_http_client()
    resp = await client.post(
        _xiaomi_chat_completions_url(),
        json=body,
        headers={"Authorization": f"Bearer {XIAOMI_API_KEY}", "Content-Type": "application/json"},
    )
    resp.raise_for_status()
    data = resp.json()
    return (((data.get("choices") or [{}])[0].get("message") or {}).get("content") or "").strip()


async def run_answer_with_budget(prompt: str, user_text: str, session_key: str) -> str:
    """Run the fast model with a strict glasses UX budget.

    If the model is slow/empty/fails, return quickly and persist a L2 upgrade
    event so the request is not lost. Do not block the SSE request on Hermes CLI.
    """
    t0 = time.monotonic()
    try:
        answer = await asyncio.wait_for(run_fast_model(prompt), timeout=ROKID_MODEL_BUDGET_SECONDS)
        elapsed = time.monotonic() - t0
        print(
            f"rokid_budget_answer elapsed={elapsed:.3f}s budget={ROKID_MODEL_BUDGET_SECONDS:.1f}s chars={len(answer)}",
            flush=True,
        )
        if answer:
            ROKID_METRICS["model_ok"] = int(ROKID_METRICS.get("model_ok") or 0) + 1
            return answer
        reason = "empty_fast_model_answer"
    except Exception as exc:
        elapsed = time.monotonic() - t0
        reason = f"{type(exc).__name__}"
        ROKID_METRICS["model_error"] = int(ROKID_METRICS.get("model_error") or 0) + 1
        ROKID_METRICS["last_model_error_at"] = time.time()
        ROKID_METRICS["last_model_error"] = reason
        print(
            f"rokid_budget_answer error={reason} elapsed={elapsed:.3f}s budget={ROKID_MODEL_BUDGET_SECONDS:.1f}s",
            flush=True,
        )
    title = _normalize_task_title(user_text or prompt)
    if not should_enqueue_l2_on_model_failure(user_text):
        return fallback_answer_for_model_failure(user_text, reason)
    record_l2_upgrade_event({
        "type": "rokid_model_timeout",
        "session_key": session_key,
        "title": title,
        "prompt": prompt[:MAX_PROMPT_CHARS],
        "history": [user_text] if user_text else [],
        "reason": reason,
        "intent": classify_l2_upgrade_intent(user_text),
        "status": "pending_l2_upgrade",
    })
    return f"这个问题我先转后台处理：{title}。完成后回 Telegram。"


async def run_answer(prompt: str) -> str:
    t0 = time.monotonic()
    if ROKID_RESPONSE_MODE == "direct_xiaomi":
        try:
            answer = await run_fast_model(prompt)
            elapsed = time.monotonic() - t0
            print(f"rokid_answer mode=direct_xiaomi elapsed={elapsed:.3f}s chars={len(answer)}", flush=True)
            if answer:
                return answer
            return "我听到了，但刚才生成结果为空，请再说一遍。"
        except Exception as e:
            elapsed = time.monotonic() - t0
            print(f"rokid_answer mode=direct_xiaomi error={type(e).__name__} elapsed={elapsed:.3f}s fallback=hermes", flush=True)
            if not ROKID_ENABLE_HERMES_FALLBACK:
                return "我这边快速响应超时了，请再说一遍或让我后台处理。"
    answer = await run_hermes(prompt)
    elapsed = time.monotonic() - t0
    print(f"rokid_answer mode=hermes_cli elapsed={elapsed:.3f}s chars={len(answer)}", flush=True)
    return answer


def sse(event: str, data: Dict[str, Any]) -> str:
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


def _result_from_pair(route_id: str, handled: bool, answer: str) -> RouteResult:
    if not handled:
        return RouteResult(False)
    route = next((r for r in RUNTIME_ROUTE_CHAIN if r.route_id == route_id), None)
    metrics_bucket = route.metrics_bucket if route else ""
    return RouteResult(True, answer, route_id, metrics_bucket)


RUNTIME_ROUTE_HANDLERS = {
    "text_l0": lambda ctx: _result_from_pair("text_l0", *handle_l0_query(ctx.user_text)),
    "location_status": lambda ctx: _result_from_pair(
        "location_status", *handle_location_status_query(ctx.payload, ctx.user_text)
    ),
    "device_status": lambda ctx: _result_from_pair(
        "device_status", *handle_device_status_query(ctx.payload, ctx.user_text)
    ),
    "camera_view": lambda ctx: _result_from_pair(
        "camera_view", *handle_camera_view_query(ctx.payload, ctx.user_text)
    ),
    "sensor_analysis": lambda ctx: _result_from_pair(
        "sensor_analysis", *handle_sensor_analysis_request(ctx.payload, ctx.user_text)
    ),
    "sensor_result_status": lambda ctx: _result_from_pair(
        "sensor_result_status", *handle_sensor_result_status_query(ctx.user_text)
    ),
    "model_process_status": lambda ctx: _result_from_pair(
        "model_process_status", *handle_model_process_status_query(ctx.user_text)
    ),
    "photo_print_confirm": lambda ctx: _result_from_pair(
        "photo_print_confirm", *handle_photo_print_request(ctx.payload, ctx.user_text)
    ),
    "x2d_print_intent": lambda ctx: _result_from_pair(
        "x2d_print_intent", *_enqueue_x2d_print_intent(ctx.payload, ctx.user_text, ctx.session_key)
    ),
    "image_placeholder": lambda ctx: _result_from_pair(
        "image_placeholder", *handle_image_placeholder(ctx.payload, ctx.user_text)
    ),
    "kanban_view": lambda ctx: _result_from_pair(
        "kanban_view", *handle_rokid_kanban_query(ctx.user_text, ctx.session_key)
    ),
    "background_task_control": lambda ctx: _result_from_pair(
        "background_task_control", *handle_background_task_control(ctx.user_text, ctx.session_key)
    ),
    "local_brain_stats_legacy": lambda ctx: _result_from_pair(
        "local_brain_stats_legacy", *handle_local_brain_query(ctx.user_text)
    ),
    "lingzhu_plugin": lambda ctx: _result_from_pair(
        "lingzhu_plugin", *handle_lingzhu_plugin_request(ctx.payload, ctx.user_text)
    ),
    "high_impact_confirm": lambda ctx: _result_from_pair(
        "high_impact_confirm", *handle_high_impact_action_request(ctx.user_text)
    ),
    "task_dialogue": lambda ctx: _result_from_pair(
        "task_dialogue", *handle_task_dialogue(ctx.user_text, ctx.session_key)
    ),
    "orphan_action_confirmation": lambda ctx: _result_from_pair(
        "orphan_action_confirmation", *handle_orphan_action_confirmation(ctx.user_text, ctx.session_key)
    ),
    "model_fallback": lambda ctx: _resolve_model_fallback_route(ctx),
}


async def _resolve_model_fallback_route(ctx: RouteContext) -> RouteResult:
    answer = await run_answer_with_budget(ctx.prompt, ctx.user_text, ctx.session_key)
    return _result_from_pair("model_fallback", True, answer)


async def resolve_runtime_route(ctx: RouteContext) -> RouteResult:
    """Resolve a Rokid request through the declared runtime route chain."""
    return await dispatch_runtime_route(ctx, routes=RUNTIME_ROUTE_CHAIN, handlers=RUNTIME_ROUTE_HANDLERS)


def _increment_metric(bucket: str) -> None:
    if bucket:
        ROKID_METRICS[bucket] = int(ROKID_METRICS.get(bucket) or 0) + 1


async def stream_answer(payload: RokidRequest) -> AsyncIterator[str]:
    prompt = extract_user_prompt(payload)
    user_text = ""
    session_key = ""
    route_id = "not_resolved"
    metrics_bucket = ""
    answer = ""
    stream_error = ""
    ROKID_METRICS["requests"] = int(ROKID_METRICS.get("requests") or 0) + 1
    common = {
        "role": "agent",
        "message_id": payload.message_id,
        "agent_id": payload.agent_id or ROKID_AGENT_ID,
        "type": "answer",
    }
    ack = {**common, "answer_stream": ROKID_ACK_TEXT, "is_finish": False}
    ROKID_METRICS["ack_sent"] = int(ROKID_METRICS.get("ack_sent") or 0) + 1
    yield sse("message", ack)

    try:
        user_text = extract_user_text(payload)
        session_key = session_key_for(payload)
        result = await resolve_runtime_route(
            RouteContext(payload=payload, prompt=prompt, user_text=user_text, session_key=session_key)
        )
        route_id = result.route_id or "unknown"
        metrics_bucket = result.metrics_bucket or ""
        _increment_metric(result.metrics_bucket)
        answer = result.answer
        if not str(answer or "").strip():
            answer = "我在，但刚才没有生成有效回复，请再说一遍。"
        answer = make_voice_safe_answer(answer)
        # Rokid expects SSE. Hermes fast path is non-token streaming here, so chunk the final answer.
        chunk_size = 80
        for i in range(0, len(answer), chunk_size):
            chunk = answer[i : i + chunk_size]
            yield sse("message", {**common, "answer_stream": chunk, "is_finish": False})
            await asyncio.sleep(0.03)
    except Exception as exc:
        stream_error = type(exc).__name__
        route_id = "stream_exception"
        ROKID_METRICS["model_error"] = int(ROKID_METRICS.get("model_error") or 0) + 1
        ROKID_METRICS["last_model_error_at"] = time.time()
        ROKID_METRICS["last_model_error"] = type(exc).__name__
        print(f"rokid_stream error={type(exc).__name__}: {exc}", flush=True)
        answer = "我还在，但刚才服务有点抖。请再说一遍，或说后台处理。"
        yield sse("message", {**common, "answer_stream": answer, "is_finish": False})
    finally:
        if dev_review_enabled():
            try:
                if hasattr(payload, "model_dump"):
                    payload_dict = payload.model_dump()
                elif hasattr(payload, "dict"):
                    payload_dict = payload.dict()
                else:
                    payload_dict = dict(payload)
                record_path = schedule_dev_review(
                    payload=payload_dict,
                    user_text=user_text or extract_user_text(payload),
                    answer=answer,
                    route_id=route_id,
                    metrics_bucket=metrics_bucket,
                    error=stream_error or None,
                    pending_action_state=pending_action_snapshot(session_key, task_sessions=TASK_SESSIONS),
                    sensor_context=build_sensor_context(payload),
                )
                if record_path:
                    ROKID_METRICS["dev_reviews_recorded"] = int(ROKID_METRICS.get("dev_reviews_recorded") or 0) + 1
                    print(f"rokid_dev_review recorded={record_path}", flush=True)
            except Exception as review_exc:
                ROKID_METRICS["dev_review_errors"] = int(ROKID_METRICS.get("dev_review_errors") or 0) + 1
                print(f"rokid_dev_review error={type(review_exc).__name__}: {review_exc}", flush=True)
        yield sse("done", {**common, "answer_stream": "", "is_finish": True})


@app.get("/health")
def health() -> Dict[str, Any]:
    return {
        "ok": True,
        "app": APP_NAME,
        "agent_id": ROKID_AGENT_ID,
        "auth_configured": bool(ROKID_AGENT_AK),
        "metrics": ROKID_METRICS,
        "dev_review_enabled": dev_review_enabled(),
        "time": int(time.time()),
    }


@app.post("/rokid/sse")
async def rokid_sse(payload: RokidRequest, authorization: Optional[str] = Header(default=None)):
    check_auth(authorization)
    return StreamingResponse(stream_answer(payload), media_type="text/event-stream")


@app.post("/rokid/callback/message")
async def callback_message(request: Request, authorization: Optional[str] = Header(default=None)):
    # Placeholder for the optional Lingzhu callback protocol; not required for basic Q&A.
    check_auth(authorization)
    body = await request.json()
    return JSONResponse(
        {
            "code": 1,
            "msg": "success",
            "timestamp": int(time.time() * 1000),
            "uuid": str(uuid.uuid4()),
            "data": {"success": True, "messageId": body.get("message_id")},
        }
    )
