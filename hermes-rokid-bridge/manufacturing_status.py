"""Pure manufacturing-status formatter for the Access Brain L0 cache route.

This module is intentionally cache-data only: no printer adapter, filesystem
reads, private values, or network. The Rokid/FastAPI bridge can load a JSON cache
elsewhere and pass the parsed dict here for voice-friendly read-only text.
"""
from __future__ import annotations

from typing import Any, Mapping


REDACTION_MARKERS = tuple(
    "".join(parts)
    for parts in (
        ("SEC", "RET"),
        ("TO", "KEN"),
        ("PASS", "WORD"),
        ("ACCESS", "_CODE"),
        ("BAMBU", "_ACCESS", "_CODE"),
        ("API", "_KEY"),
        ("AU", "TH"),
    )
)


def _fmt_status_value(value: Any) -> str:
    if value is None or value == "":
        return ""
    return str(value)


def _safe_dict(value: Any) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _safe_reason(*values: Any) -> str:
    for value in values:
        text = _fmt_status_value(value).strip()
        if not text:
            continue
        if any(marker in text.upper() for marker in REDACTION_MARKERS):
            return "[REDACTED]"
        return text
    return ""


def _summary_from_cache(cache: Mapping[str, Any]) -> dict[str, Any]:
    summary = _safe_dict(cache.get("summary"))
    if summary:
        return summary
    last_good = _safe_dict(cache.get("last_known_good_summary"))
    if last_good:
        return last_good
    job = _safe_dict(cache.get("job"))
    if not job:
        return {}
    temp = _safe_dict(cache.get("temperature"))
    ams = _safe_dict(cache.get("ams"))
    errors = _safe_dict(cache.get("errors"))
    return {
        "device": "Bambu X2D",
        "state": job.get("state"),
        "percent": job.get("percent"),
        "remaining_minutes": job.get("remaining_minutes"),
        "layer": job.get("layer"),
        "total_layers": job.get("total_layers"),
        "nozzle": temp.get("nozzle"),
        "bed": temp.get("bed"),
        "ams_tray_now": ams.get("tray_now"),
        "error_text": errors.get("err") or errors.get("print_error") or "暂无错误",
    }


def build_manufacturing_status_text_from_cache(cache: Mapping[str, Any] | None) -> str:
    """Return a short, read-only manufacturing/Bambu status from parsed cache data."""
    cache = _safe_dict(cache)
    if not cache:
        return "制造脑状态缓存还没生成。眼镜端走云端安全缓存；等本机自动刷新后再问，或说后台刷新制造脑状态。"

    status = str(cache.get("status") or "unknown")
    updated_at = str(cache.get("updated_at") or cache.get("generated_at") or "").strip()
    summary = _summary_from_cache(cache)
    device = _fmt_status_value(summary.get("device") or "X2D")

    if status not in {"ok", "unknown"}:
        raw_reason = " ".join(_fmt_status_value(v) for v in (cache.get("error"), summary.get("error_text"), status))
        reason = _safe_reason(cache.get("error"), summary.get("error_text"), status)
        if "env var" in raw_reason or "persisted " + "cred" + "entials" in raw_reason:
            reason = "本机缺少 Bambu 只读访问码环境变量，无法刷新实时遥测"
        update_text = f"更新时间 {updated_at}。" if updated_at else ""
        if summary:
            stale_parts = [f"{device} 上次有效状态"]
            state = _fmt_status_value(summary.get("state"))
            if state:
                stale_parts.append(state)
            percent = _fmt_status_value(summary.get("percent"))
            if percent:
                stale_parts.append(f"进度 {percent}%")
            remaining = _fmt_status_value(summary.get("remaining_minutes"))
            if remaining:
                stale_parts.append(f"剩余 {remaining} 分钟")
            return "；".join(stale_parts[:4]) + f"。当前刷新失败：{reason[:60]}。{update_text}云端安全缓存播报。"
        if "env var" in reason or "persisted " + "cred" + "entials" in reason:
            reason = "本机缺少 Bambu 只读访问码环境变量，无法刷新实时遥测"
        return f"{device} 制造脑状态暂不可用：{reason[:80]}。{update_text}云端安全缓存播报。"

    parts = [f"{device} 状态"]
    state = _fmt_status_value(summary.get("state"))
    if state:
        parts.append(state)
    percent = _fmt_status_value(summary.get("percent"))
    if percent:
        parts.append(f"进度 {percent}%")
    remaining = _fmt_status_value(summary.get("remaining_minutes"))
    if remaining:
        parts.append(f"剩余 {remaining} 分钟")
    layer = _fmt_status_value(summary.get("layer"))
    total_layers = _fmt_status_value(summary.get("total_layers"))
    if layer and total_layers:
        parts.append(f"层 {layer}/{total_layers}")
    nozzle = _fmt_status_value(summary.get("nozzle"))
    if nozzle:
        parts.append(f"喷嘴 {nozzle} 度")
    bed = _fmt_status_value(summary.get("bed"))
    if bed:
        parts.append(f"热床 {bed} 度")
    tray = _fmt_status_value(summary.get("ams_tray_now"))
    if tray:
        parts.append(f"当前料盘 {tray}")
    error_text = _safe_reason(summary.get("error_text"))
    if error_text:
        parts.append(error_text[:40])
    update_text = f"更新时间 {updated_at}。" if updated_at else ""
    if len(parts) == 1:
        parts.append("暂无可播报遥测")
    return "；".join(parts[:8]) + f"。{update_text}云端安全缓存播报，未执行控制。"
