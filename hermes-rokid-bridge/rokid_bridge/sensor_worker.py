"""Background worker for Rokid sensor jobs.

This worker is intentionally fail-soft and dependency-optional. It consumes the
JSON jobs created by the SSE request path and writes structured result files
without blocking the glasses response path or claiming that a model saw/heard
anything unless the relevant dependency actually produced evidence.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import time
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any, Dict, List, Optional

from .sensor_context import DEFAULT_JOBS_DIR

DEFAULT_RESULTS_DIR = "~/.hermes/brains/rokid-glasses/sensor_results"
ASR_CORRECTIONS = {
    "进毒": "进度",
    "装太": "状态",
    "壮态": "状态",
    "却认执行": "确认执行",
    "缺认执行": "确认执行",
    "确人执行": "确认执行",
}


def _jobs_dir() -> Path:
    root = Path(os.path.expanduser(os.getenv("ROKID_SENSOR_JOBS_DIR", DEFAULT_JOBS_DIR)))
    root.mkdir(parents=True, exist_ok=True)
    return root


def _results_dir() -> Path:
    root = Path(os.path.expanduser(os.getenv("ROKID_SENSOR_RESULTS_DIR", DEFAULT_RESULTS_DIR)))
    root.mkdir(parents=True, exist_ok=True)
    return root


def _read_json(path: Path) -> Dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def _write_json(path: Path, payload: Dict[str, Any]) -> Path:
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(path)
    return path


def _attach_artifact_receipt(result_path: Path, result: Dict[str, Any]) -> Dict[str, Any]:
    receipted = dict(result)
    receipted["output_path"] = str(result_path)
    checksum_payload = json.dumps(receipted, ensure_ascii=False, sort_keys=True).encode("utf-8")
    receipted["artifact_sha256"] = hashlib.sha256(checksum_payload).hexdigest()
    return receipted


def _dep_available(name: str) -> bool:
    return importlib.util.find_spec(name) is not None


def _result_path(prefix: str, job_path: Path, payload: Dict[str, Any]) -> Path:
    digest = hashlib.sha256((job_path.name + json.dumps(payload, sort_keys=True, ensure_ascii=False)).encode("utf-8")).hexdigest()[:12]
    return _results_dir() / f"{prefix}_result_{int(time.time())}_{digest}.json"


def _mark_job_processed(job_path: Path, job: Dict[str, Any], result_path: Path, status: str) -> None:
    updated = dict(job)
    updated["status"] = "processed"
    updated["processed_at"] = int(time.time())
    updated["result_path"] = str(result_path)
    updated["result_status"] = status
    _write_json(job_path, updated)


def _uri_hash(uri: str) -> str:
    return hashlib.sha256(str(uri or "").encode("utf-8")).hexdigest()


def _safe_image_ref(item: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "image_id": item.get("image_id"),
        "index": item.get("index"),
        "uri_hash": _uri_hash(str(item.get("uri") or "")),
        "retention": item.get("retention") or "ephemeral",
        "persist_raw": False,
    }


def _local_path_from_uri(uri: str) -> Optional[Path]:
    parsed = urllib.parse.urlparse(uri)
    if parsed.scheme == "file":
        return Path(urllib.request.url2pathname(parsed.path))
    if not parsed.scheme and uri.startswith("/"):
        return Path(uri)
    return None


def _image_access_proof(item: Dict[str, Any]) -> Dict[str, Any]:
    uri = str(item.get("uri") or "")
    parsed = urllib.parse.urlparse(uri)
    proof: Dict[str, Any] = {
        "image_id": item.get("image_id"),
        "index": item.get("index"),
        "uri_hash": _uri_hash(uri),
        "uri_scheme": parsed.scheme or "file" if uri.startswith("/") else parsed.scheme or "unknown",
        "access_status": "not_checked",
    }
    local_path = _local_path_from_uri(uri)
    if local_path is not None:
        try:
            data = local_path.read_bytes()
            proof.update({
                "access_status": "accessible",
                "byte_count": len(data),
                "sha256": hashlib.sha256(data).hexdigest(),
            })
        except OSError as exc:
            proof.update({"access_status": "unreachable", "error": type(exc).__name__})
        return proof
    if parsed.scheme in {"http", "https"}:
        try:
            max_bytes = int(os.getenv("ROKID_SENSOR_IMAGE_MAX_BYTES", "5242880"))
            request = urllib.request.Request(uri, headers={"User-Agent": "hermes-rokid-sensor-worker/1"})
            with urllib.request.urlopen(request, timeout=5) as response:  # nosec - user-provided evidence URL, bounded read only
                data = response.read(max_bytes + 1)
                truncated = len(data) > max_bytes
                if truncated:
                    data = data[:max_bytes]
                proof.update({
                    "access_status": "accessible" if data else "empty_response",
                    "http_status": int(getattr(response, "status", 0) or 0),
                    "content_type": response.headers.get("content-type"),
                    "content_length": response.headers.get("content-length"),
                    "byte_count": len(data),
                    "sha256": hashlib.sha256(data).hexdigest() if data else None,
                    "truncated": truncated,
                })
        except Exception as exc:
            proof.update({"access_status": "unreachable", "error": type(exc).__name__})
        return proof
    proof["access_status"] = "unsupported_uri"
    return proof


def _vision_adapter_status() -> Dict[str, Any]:
    adapter = os.getenv("ROKID_VISION_ADAPTER", "").strip()
    if not adapter:
        return {
            "vlm": "unavailable",
            "adapter": None,
            "no_stub_fallback": True,
            "reason": "ROKID_VISION_ADAPTER not configured",
        }
    return {
        "vlm": "configured_not_executed",
        "adapter": adapter,
        "no_stub_fallback": True,
        "reason": "adapter execution not wired into fail-closed worker",
    }


def _vision_result(job_path: Path, job: Dict[str, Any]) -> Dict[str, Any]:
    sensor_context_obj = job.get("sensor_context")
    sensor_context: Dict[str, Any] = sensor_context_obj if isinstance(sensor_context_obj, dict) else {}
    image_obj = sensor_context.get("image")
    image: Dict[str, Any] = image_obj if isinstance(image_obj, dict) else {}
    items_obj = image.get("items")
    items: List[Dict[str, Any]] = [item for item in items_obj if isinstance(item, dict)] if isinstance(items_obj, list) else []
    deps = {
        "supervision": "available" if _dep_available("supervision") else "pending_dependency",
        "cv2": "available" if _dep_available("cv2") else "pending_dependency",
    }
    dependency_ready = all(v == "available" for v in deps.values())
    adapter_status = _vision_adapter_status()
    access_proofs = [_image_access_proof(item) for item in items]
    status = "adapter_unavailable" if items and adapter_status.get("vlm") == "unavailable" else "ready_for_model" if dependency_ready and items else "dependency_pending" if items else "missing_image"
    return {
        "schema": "vision_analysis_result_v1",
        "created_at": int(time.time()),
        "source_job": job_path.name,
        "status": status,
        "mode": "background_only",
        "question": job.get("question", ""),
        "dependencies": deps,
        "adapter_status": adapter_status,
        "image_count": len(items),
        "image_refs": [_safe_image_ref(item) for item in items],
        "image_access_proofs": access_proofs,
        "visual_facts": [],
        "notes": [
            "图片已进入后台视觉队列。",
            "当前结果只记录图片证据与依赖状态；没有可靠视觉模型输出前不描述画面内容。",
        ],
        "privacy": job.get("privacy", {"retention": "ephemeral", "persist_raw": False}),
        "fail_soft": True,
    }


def _apply_text_corrections(text: str) -> List[str]:
    candidates: List[str] = []
    for wrong, right in ASR_CORRECTIONS.items():
        if wrong in text and right not in candidates:
            candidates.append(text.replace(wrong, right))
            if right not in candidates:
                candidates.append(right)
    return candidates


def _try_whisper_transcribe(audio_uri: str) -> Optional[str]:
    if not audio_uri or not _dep_available("whisper"):
        return None
    # Keep the worker safe: only local files are attempted. Remote/unsupported URIs
    # remain queued as evidence and can be handled by a dedicated downloader later.
    path = audio_uri
    if audio_uri.startswith("file://"):
        path = audio_uri[7:]
    if "://" in path or not Path(path).exists():
        return None
    try:
        import whisper  # type: ignore

        model_name = os.getenv("ROKID_WHISPER_MODEL", "base")
        model = whisper.load_model(model_name)
        result = model.transcribe(path)
        text = result.get("text") if isinstance(result, dict) else None
        return str(text).strip() if text else None
    except Exception:
        return None


def _asr_result(job_path: Path, job: Dict[str, Any]) -> Dict[str, Any]:
    audio = job.get("audio") if isinstance(job.get("audio"), dict) else {}
    recognized_text = str(audio.get("asr_text") or "").strip()
    audio_uri = str(audio.get("uri") or "").strip()
    deps = {
        "whisper": "available" if _dep_available("whisper") else "pending_dependency",
        "torch": "available" if _dep_available("torch") else "pending_dependency",
    }
    whisper_text = _try_whisper_transcribe(audio_uri)
    candidates = _apply_text_corrections(recognized_text)
    if whisper_text and whisper_text != recognized_text and whisper_text not in candidates:
        candidates.insert(0, whisper_text)
    status = "reviewed" if whisper_text else "dependency_pending" if audio.get("available") else "missing_audio"
    return {
        "schema": "asr_review_result_v1",
        "created_at": int(time.time()),
        "source_job": job_path.name,
        "status": status,
        "mode": "background_only",
        "dependencies": deps,
        "audio_available": bool(audio.get("available")),
        "audio_uri": audio_uri or None,
        "recognized_text": recognized_text,
        "whisper_text": whisper_text,
        "correction_candidates": candidates,
        "notes": [
            "Whisper 复核在后台执行；依赖或音频不可用时只输出文本级纠错候选。",
            "纠错候选不会自动改写线上路由，需经测试后沉淀到 ASR 归一化规则。",
        ],
        "fail_soft": True,
    }


def process_sensor_job(job_path: Path) -> Optional[Path]:
    job = _read_json(job_path)
    if not job or job.get("status") not in {"queued", "missing_audio", "missing_image"}:
        return None
    schema = job.get("schema")
    if schema == "vision_analysis_job_v1":
        result = _vision_result(job_path, job)
        result_path = _result_path("vision", job_path, result)
    elif schema == "asr_review_job_v1":
        result = _asr_result(job_path, job)
        result_path = _result_path("asr", job_path, result)
    else:
        result = {
            "schema": "sensor_job_error_v1",
            "created_at": int(time.time()),
            "source_job": job_path.name,
            "status": "unsupported_schema",
            "fail_soft": True,
        }
        result_path = _result_path("sensor", job_path, result)
    _write_json(result_path, _attach_artifact_receipt(result_path, result))
    _mark_job_processed(job_path, job, result_path, str(result.get("status") or "unknown"))
    return result_path


def process_sensor_queue(*, limit: int = 10) -> List[Path]:
    processed: List[Path] = []
    for job_path in sorted(_jobs_dir().glob("*.json"), key=lambda p: p.stat().st_mtime):
        if len(processed) >= limit:
            break
        result = process_sensor_job(job_path)
        if result is not None:
            processed.append(result)
    return processed


def _latest_result() -> Optional[Dict[str, Any]]:
    paths = sorted(_results_dir().glob("*.json"), key=lambda p: p.stat().st_mtime)
    if not paths:
        return None
    data = _read_json(paths[-1])
    data["path"] = str(paths[-1])
    return data


def summarize_latest_sensor_result() -> str:
    result = _latest_result()
    if not result:
        return "还没有传感器后台复核结果。"
    schema = result.get("schema")
    status = result.get("status", "unknown")
    if schema == "asr_review_result_v1":
        candidates = result.get("correction_candidates") if isinstance(result.get("correction_candidates"), list) else []
        if candidates:
            return f"最近传感器复核：语音复核状态 {status}；候选纠错：{'、'.join(map(str, candidates[:3]))}。"
        return f"最近传感器复核：语音复核状态 {status}；暂无候选纠错。"
    if schema == "vision_analysis_result_v1":
        count = result.get("image_count", 0)
        output_path = str(result.get("output_path") or "")
        evidence = f"；证据 {Path(output_path).name}" if output_path else ""
        return f"最近传感器复核：视觉分析状态 {status}；图片 {count} 张{evidence}；没有可靠视觉模型输出前不描述画面内容。"
    return f"最近传感器复核：状态 {status}。"


if __name__ == "__main__":
    for path in process_sensor_queue():
        print(path)
