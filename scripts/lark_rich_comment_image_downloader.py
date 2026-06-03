#!/usr/bin/env python3
from __future__ import annotations
"""Download Lark Task rich-comment image evidence when the API exposes keys.

Read-only helper. It never writes comments/status back to Lark. It tries the
Task comment list/detail surfaces, extracts image_key/file_token/media tokens
from the full rich JSON payload, downloads any exposed images/files, and records
explicit `unavailable` rows when Lark only returns literal `[Image]` placeholders.
"""

import argparse
import hashlib
import json
import mimetypes
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import lark_task_reader as ltr  # noqa: E402

DEFAULT_OUT_DIR = Path.home() / ".hermes" / "evidence" / "lark-rich-comment-images"
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp"}


def _jsonable(obj: Any) -> Any:
    try:
        json.dumps(obj)
        return obj
    except TypeError:
        return str(obj)


def _walk(obj: Any):
    if isinstance(obj, dict):
        yield obj
        for value in obj.values():
            yield from _walk(value)
    elif isinstance(obj, list):
        for item in obj:
            yield from _walk(item)


def _extract_candidate_keys(obj: Any) -> list[dict[str, str]]:
    """Extract possible rich image/media handles from a full comment payload."""
    candidates: list[dict[str, str]] = []
    seen: set[tuple[str, str]] = set()
    imageish_fields = (
        "image_key",
        "file_token",
        "file_key",
        "media_id",
        "media_token",
        "token",
    )
    for node in _walk(obj):
        # Prefer known image object shape.
        if isinstance(node.get("image"), dict):
            img = node["image"]
            for field in imageish_fields:
                value = img.get(field)
                if isinstance(value, str) and value:
                    key = (field, value)
                    if key not in seen:
                        seen.add(key)
                        candidates.append({"kind": field, "value": value, "source": "image"})
        # Some endpoints flatten image_key/file_token directly into element attrs.
        node_type = str(node.get("type") or node.get("tag") or node.get("element_type") or "").lower()
        for field in imageish_fields:
            value = node.get(field)
            if not isinstance(value, str) or not value:
                continue
            if field == "token" and not any(word in node_type for word in ("image", "img", "media", "file")):
                continue
            key = (field, value)
            if key not in seen:
                seen.add(key)
                candidates.append({"kind": field, "value": value, "source": node_type or "rich_node"})
    return candidates


def _comment_id(comment: dict[str, Any]) -> str:
    for key in ("comment_id", "id", "guid", "comment_guid"):
        value = comment.get(key)
        if value:
            return str(value)
    return ""


def _detail_candidates(token: str, task_guid: str, comment_id: str, client: ltr.LarkClient) -> list[dict[str, Any]]:
    if not comment_id:
        return []
    endpoints = [
        (f"/task/v2/comments/{urllib.parse.quote(comment_id, safe='')}", {}),
        (f"/task/v2/tasks/{urllib.parse.quote(task_guid, safe='')}/comments/{urllib.parse.quote(comment_id, safe='')}", {}),
        ("/task/v2/comments", {"comment_id": comment_id, "resource_id": task_guid, "resource_type": "task"}),
    ]
    out: list[dict[str, Any]] = []
    for path, query in endpoints:
        try:
            data = client.get(path, token, query=query or None)
            out.append({"endpoint": path, "ok": data.get("code") == 0, "payload": data})
        except Exception as exc:
            out.append({"endpoint": path, "ok": False, "error": type(exc).__name__ + ": " + str(exc)[:240]})
    return out


def _fetch_native_attachments(token: str, task_guid: str, client: ltr.LarkClient) -> dict[str, Any]:
    try:
        data = client.get("/task/v2/attachments", token, query={"resource_type": "task", "resource_id": task_guid, "page_size": 50})
        return data
    except Exception as exc:
        return {"code": -1, "msg": type(exc).__name__ + ": " + str(exc)[:240], "data": {"items": []}}


def _safe_name(seed: str, ext: str) -> str:
    digest = hashlib.sha256(seed.encode("utf-8")).hexdigest()[:24]
    return digest + (ext if ext.startswith(".") else "." + ext)


def _guess_attachment_ext(item: dict[str, Any], content_type: str = "") -> str:
    name = str(item.get("name") or item.get("file_name") or "")
    suffix = Path(name).suffix.lower()
    if suffix:
        return ".jpg" if suffix == ".jpeg" else suffix
    guessed = mimetypes.guess_extension((content_type or "").split(";", 1)[0].strip()) or ""
    return ".jpg" if guessed == ".jpe" else (guessed or ".bin")


def _download_url(url: str, token: str, max_bytes: int = ltr.MAX_IMAGE_BYTES) -> tuple[bytes, dict[str, str]]:
    req = urllib.request.Request(url)
    req.add_header("Authorization", f"Bearer {token}")
    with urllib.request.urlopen(req, timeout=30) as resp:
        chunks: list[bytes] = []
        total = 0
        while True:
            chunk = resp.read(64 * 1024)
            if not chunk:
                break
            total += len(chunk)
            if total > max_bytes:
                raise RuntimeError(f"binary response exceeds max_bytes={max_bytes}")
            chunks.append(chunk)
        return b"".join(chunks), {str(k).lower(): str(v) for k, v in resp.info().items()}


def _download_native_attachments(token: str, task_guid: str, items: list[dict[str, Any]], out_dir: Path, client: ltr.LarkClient) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for item in items:
        file_token = str(item.get("file_token") or item.get("token") or item.get("media_id") or "")
        name = str(item.get("name") or item.get("file_name") or "")
        url = str(item.get("url") or item.get("download_url") or "")
        ext = _guess_attachment_ext(item)
        is_image_name = ext.lower() in IMAGE_EXTENSIONS
        if not file_token and not url:
            records.append({"source": "task_native_attachment", "status": "unavailable", "name": name, "file_token": file_token, "local_path": "", "error": "attachment has no file_token/url"})
            continue
        seed = file_token or url or name or task_guid
        local_path = out_dir / _safe_name("attachment:" + seed, ext)
        try:
            if local_path.exists() and local_path.stat().st_size > 0:
                records.append({"source": "task_native_attachment", "status": "cached", "name": name, "file_token": file_token, "local_path": str(local_path), "size_bytes": local_path.stat().st_size, "is_image_name": is_image_name, "error": ""})
                continue
            # Task native attachments expose both a Drive-like file_token and a
            # short-lived authcode URL. In the Lark Task attachment surface,
            # file_token can require broader Drive scopes (99991679) even though
            # /task/v2/attachments already authorizes the caller to see the file.
            # Prefer the signed URL when present, and fall back to Drive media for
            # tenants/payloads that do not include url/download_url.
            if url:
                raw, headers = _download_url(url, token)
            elif file_token:
                raw, headers = client.get_binary(f"/drive/v1/medias/{urllib.parse.quote(file_token, safe='')}/download", token)
            else:
                raise RuntimeError("attachment has no downloadable url or file_token")
            content_type = headers.get("content-type", "")
            if not Path(local_path).suffix or local_path.suffix == ".bin":
                local_path = out_dir / _safe_name("attachment:" + seed, _guess_attachment_ext(item, content_type))
            local_path.write_bytes(raw)
            records.append({"source": "task_native_attachment", "status": "downloaded", "name": name, "file_token": file_token, "local_path": str(local_path), "content_type": content_type, "size_bytes": len(raw), "is_image_name": local_path.suffix.lower() in IMAGE_EXTENSIONS, "error": ""})
        except Exception as exc:
            records.append({"source": "task_native_attachment", "status": "failed", "name": name, "file_token": file_token, "local_path": "", "error": type(exc).__name__ + ": " + str(exc)[:240]})
    return records


def download_for_task(task_guid: str, out_dir: Path, *, include_debug: bool = False) -> dict[str, Any]:
    out_dir.mkdir(parents=True, exist_ok=True)
    client = ltr.LarkClient(timeout=30)
    token = ltr.get_token(auto_auth=True, auto_authorize=True)
    comments = ltr.fetch_comments(token, task_guid, client=client)

    rich_payloads: list[dict[str, Any]] = []
    detail_probe: list[dict[str, Any]] = []
    for c in comments:
        rich_payloads.append(c)
        cid = _comment_id(c)
        details = _detail_candidates(token, task_guid, cid, client)
        for d in details:
            if d.get("ok") and isinstance(d.get("payload"), dict):
                rich_payloads.append(d["payload"])
        if include_debug:
            detail_probe.append({"comment_id": cid, "details": details})

    candidates: list[dict[str, str]] = []
    for payload in rich_payloads:
        candidates.extend(_extract_candidate_keys(payload))
    # Also use the existing reader extraction from parsed content fields.
    for key in ltr.extract_comment_image_keys(comments):
        candidates.append({"kind": "image_key", "value": key, "source": "reader_content"})
    deduped_candidates: list[dict[str, str]] = []
    seen_values: set[str] = set()
    for c in candidates:
        value = c.get("value", "")
        if value and value not in seen_values:
            seen_values.add(value)
            deduped_candidates.append(c)

    image_keys = [c["value"] for c in deduped_candidates]
    comment_image_records = ltr.download_comment_images(token, image_keys, cache_dir=out_dir, client=client) if image_keys else []
    placeholder_count = ltr.count_comment_image_placeholders(comments)
    if placeholder_count and not image_keys:
        comment_image_records.extend(ltr._unavailable_image_placeholder_records(placeholder_count))  # noqa: SLF001

    attachments_payload = _fetch_native_attachments(token, task_guid, client)
    attachments = ((attachments_payload.get("data") or {}).get("items") or []) if isinstance(attachments_payload, dict) else []
    attachment_records = _download_native_attachments(token, task_guid, attachments, out_dir, client)

    downloaded = [r for r in comment_image_records + attachment_records if r.get("status") in {"downloaded", "cached"} and r.get("local_path")]
    result: dict[str, Any] = {
        "schema": "lark_rich_comment_image_download_v1",
        "task_guid": task_guid,
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "out_dir": str(out_dir),
        "comment_count": len(comments),
        "rich_candidate_keys": deduped_candidates,
        "comment_image_placeholders": placeholder_count,
        "comment_images": comment_image_records,
        "native_attachment_count": len(attachments),
        "native_attachments": attachment_records,
        "downloaded_count": len(downloaded),
        "downloaded_paths": [r.get("local_path") for r in downloaded],
        "status": "downloaded" if downloaded else ("unavailable_placeholders" if placeholder_count else "no_images_found"),
    }
    if include_debug:
        result["detail_probe"] = detail_probe
        result["attachments_payload"] = _jsonable(attachments_payload)
    manifest = out_dir / f"{task_guid}-manifest.json"
    manifest.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    result["manifest_path"] = str(manifest)
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Download exposed rich-comment images/native attachments for one Lark task (read-only).")
    parser.add_argument("--task-guid", "--task-id", dest="task_guid", required=True, help="Lark Task guid/id")
    parser.add_argument("--out-dir", default=str(DEFAULT_OUT_DIR), help="output/cache directory")
    parser.add_argument("--debug", action="store_true", help="include endpoint probe details in manifest")
    parser.add_argument("--json", action="store_true", help="print JSON result")
    args = parser.parse_args(argv)

    result = download_for_task(args.task_guid, Path(args.out_dir).expanduser(), include_debug=args.debug)
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"status={result['status']} downloaded={result['downloaded_count']} manifest={result['manifest_path']}")
        for path in result.get("downloaded_paths") or []:
            print(path)
    return 0 if result.get("status") in {"downloaded", "unavailable_placeholders", "no_images_found"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
