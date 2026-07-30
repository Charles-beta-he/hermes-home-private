#!/usr/bin/env python3
"""Bind local rank/gameplay captures to immutable SHA-256 evidence entries."""

import argparse
import copy
import hashlib
import json
import os
import re
import tempfile
from pathlib import Path
from typing import Any, Dict, Mapping, Optional, Tuple


DIRECT_SOURCE_TYPES = {"direct_app_rank_capture", "direct_gameplay_capture"}
SHA256_RE = re.compile(r"[0-9a-f]{64}")
PLACEHOLDER_DIGESTS = {None, "", "replace-with-sha256"}


class IntakeError(ValueError):
    """Raised when capture binding cannot be proven from a local regular file."""


def _stable_identity(stat_result: os.stat_result) -> Tuple[int, int, int, int]:
    return (stat_result.st_dev, stat_result.st_ino, stat_result.st_size, stat_result.st_mtime_ns)


def _digest_file(path: Path) -> Tuple[str, int]:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        before = os.fstat(stream.fileno())
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
        after = os.fstat(stream.fileno())
    if _stable_identity(before) != _stable_identity(after):
        raise IntakeError(f"media changed while hashing: {path}")
    if _stable_identity(path.stat()) != _stable_identity(after):
        raise IntakeError(f"media path changed while hashing: {path}")
    return digest.hexdigest(), after.st_size


def bind_direct_media(snapshot: Mapping[str, Any], base_dir: Optional[Path] = None) -> Dict[str, Any]:
    if not isinstance(snapshot, Mapping):
        raise IntakeError("snapshot must be an object")
    sources = snapshot.get("sources")
    if not isinstance(sources, list) or not sources:
        raise IntakeError("snapshot.sources must be a non-empty array")

    root = (base_dir or Path.cwd()).resolve()
    bound = copy.deepcopy(dict(snapshot))
    seen = set()

    for index, raw_source in enumerate(bound["sources"]):
        if not isinstance(raw_source, dict):
            raise IntakeError(f"sources[{index}] must be an object")
        source_id = raw_source.get("source_id")
        if not isinstance(source_id, str) or not source_id:
            raise IntakeError(f"sources[{index}].source_id must be non-empty")
        if source_id in seen:
            raise IntakeError(f"duplicate source_id: {source_id}")
        seen.add(source_id)

        media_value = raw_source.get("local_media_path")
        if media_value is None:
            continue
        if raw_source.get("source_type") not in DIRECT_SOURCE_TYPES or raw_source.get("evidence_level") != "direct":
            raise IntakeError(f"source {source_id} may not bind local media unless it is direct evidence")
        if raw_source.get("content_review") is not None:
            raise IntakeError(
                f"source {source_id}.content_review must be added by a human after media binding"
            )
        if not isinstance(media_value, str) or not media_value.strip():
            raise IntakeError(f"source {source_id}.local_media_path must be non-empty")

        declared_path = Path(media_value).expanduser()
        resolved_path = (declared_path if declared_path.is_absolute() else root / declared_path).resolve()
        if not resolved_path.exists():
            raise IntakeError(f"source {source_id} media does not exist: {resolved_path}")
        if not resolved_path.is_file():
            raise IntakeError(f"source {source_id} media is not a regular file: {resolved_path}")

        computed, media_size = _digest_file(resolved_path)
        declared_digest = raw_source.get("evidence_digest")
        if declared_digest not in PLACEHOLDER_DIGESTS:
            if not isinstance(declared_digest, str) or SHA256_RE.fullmatch(declared_digest) is None:
                raise IntakeError(f"source {source_id} has invalid declared evidence_digest")
            if declared_digest != computed:
                raise IntakeError(f"source {source_id} evidence_digest does not match local media")

        raw_source["local_media_path"] = str(resolved_path)
        raw_source["evidence_digest"] = computed
        raw_source["media_size_bytes"] = media_size

    return bound


def _write_json_atomic(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=str(path.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            json.dump(payload, stream, ensure_ascii=False, indent=2, sort_keys=True)
            stream.write("\n")
        os.replace(temp_name, path)
    except Exception:
        try:
            os.unlink(temp_name)
        except FileNotFoundError:
            pass
        raise


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, help="draft market snapshot JSON")
    parser.add_argument("--output", type=Path, required=True, help="bound snapshot JSON")
    args = parser.parse_args()

    input_path = args.input.resolve()
    snapshot = json.loads(input_path.read_text(encoding="utf-8"))
    bound = bind_direct_media(snapshot, base_dir=input_path.parent)
    _write_json_atomic(args.output.resolve(), bound)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
