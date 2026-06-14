#!/usr/bin/env python3
"""Optional TurboVec adapter prototype for local-brain style retrieval.

This module is intentionally disabled-by-default. It provides a bounded adapter
surface for synthetic/local prototype validation without replacing the current
TF-IDF retrieval path in semantic_retrieval.py.

Env gates:
  HERMES_LOCAL_BRAIN_VECTOR_BACKEND=tfidf|turbovec
  HERMES_LOCAL_BRAIN_TURBOVEC_PROTOTYPE=0|1

CLI:
  python3 local_brain_turbovec_adapter.py status
  python3 local_brain_turbovec_adapter.py benchmark --docs 256 --dim 64 --queries 4
"""

from __future__ import annotations

import argparse
import json
import os
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

BACKEND_ENV_VAR = "HERMES_LOCAL_BRAIN_VECTOR_BACKEND"
PROTOTYPE_ENV_VAR = "HERMES_LOCAL_BRAIN_TURBOVEC_PROTOTYPE"
MANIFEST_NAME = "docstore.json"
INDEX_NAME = "index.tvim"
SCHEMA_VERSION = "local_brain_turbovec_adapter_v1"
SUPPORTED_BACKENDS = {"tfidf", "turbovec"}

_IMPORT_ERROR: Optional[str] = None
try:
    import numpy as np
    from turbovec import IdMapIndex
except Exception as exc:  # pragma: no cover - exercised through status resolution
    np = None
    IdMapIndex = None
    _IMPORT_ERROR = str(exc)


@dataclass
class BackendResolution:
    requested: str
    active: str
    prototype_enabled: bool
    available: bool
    fallback_reason: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "requested": self.requested,
            "active": self.active,
            "prototype_enabled": self.prototype_enabled,
            "available": self.available,
            "fallback_reason": self.fallback_reason,
            "rollback": f"unset {BACKEND_ENV_VAR} or set {BACKEND_ENV_VAR}=tfidf",
        }


def _env_flag(name: str) -> bool:
    return os.environ.get(name, "").strip().lower() in {"1", "true", "yes", "on"}


def turbovec_available() -> bool:
    return IdMapIndex is not None and np is not None


def resolve_backend(requested: Optional[str] = None) -> BackendResolution:
    requested_name = (requested or os.environ.get(BACKEND_ENV_VAR) or "tfidf").strip().lower() or "tfidf"
    if requested_name not in SUPPORTED_BACKENDS:
        raise ValueError(f"unsupported backend '{requested_name}'; expected one of {sorted(SUPPORTED_BACKENDS)}")

    prototype_enabled = _env_flag(PROTOTYPE_ENV_VAR)
    available = turbovec_available()

    if requested_name == "tfidf":
        return BackendResolution(
            requested=requested_name,
            active="tfidf",
            prototype_enabled=prototype_enabled,
            available=available,
        )

    if not prototype_enabled:
        return BackendResolution(
            requested=requested_name,
            active="tfidf",
            prototype_enabled=False,
            available=available,
            fallback_reason="prototype-disabled",
        )

    if not available:
        return BackendResolution(
            requested=requested_name,
            active="tfidf",
            prototype_enabled=True,
            available=False,
            fallback_reason=f"turbovec-unavailable: {_IMPORT_ERROR or 'missing dependency'}",
        )

    return BackendResolution(
        requested=requested_name,
        active="turbovec",
        prototype_enabled=True,
        available=True,
    )


def _normalize_vectors(vectors: Iterable[Iterable[float]]) -> "np.ndarray":
    if np is None:
        raise RuntimeError(f"turbovec adapter unavailable: {_IMPORT_ERROR or 'numpy/turbovec not installed'}")
    arr = np.asarray(list(vectors), dtype=np.float32)
    if arr.ndim != 2:
        raise ValueError(f"vectors must be 2D, got shape {arr.shape}")
    if arr.shape[0] == 0 or arr.shape[1] == 0:
        raise ValueError("vectors must be non-empty")
    return np.ascontiguousarray(arr)


def _normalize_query(vector: Iterable[float]) -> "np.ndarray":
    if np is None:
        raise RuntimeError(f"turbovec adapter unavailable: {_IMPORT_ERROR or 'numpy/turbovec not installed'}")
    arr = np.asarray(list(vector), dtype=np.float32)
    if arr.ndim != 1:
        raise ValueError(f"query must be 1D, got shape {arr.shape}")
    if arr.shape[0] == 0:
        raise ValueError("query must be non-empty")
    return np.ascontiguousarray(arr.reshape(1, -1))


class TurboVecAdapter:
    """Stable-id adapter over turbovec.IdMapIndex for synthetic prototype validation."""

    def __init__(self, dim: Optional[int] = None, bit_width: int = 4, *, index: Any = None,
                 documents: Optional[Dict[str, Dict[str, Any]]] = None,
                 key_to_id: Optional[Dict[str, int]] = None,
                 next_id: int = 1) -> None:
        if not turbovec_available():
            raise RuntimeError(f"turbovec adapter unavailable: {_IMPORT_ERROR or 'numpy/turbovec not installed'}")
        self.index = index if index is not None else IdMapIndex(dim=dim, bit_width=bit_width)
        self.documents: Dict[str, Dict[str, Any]] = documents or {}
        self.key_to_id: Dict[str, int] = {str(k): int(v) for k, v in (key_to_id or {}).items()}
        self.next_id = int(next_id)

    @property
    def dim(self) -> Optional[int]:
        return self.index.dim

    @property
    def bit_width(self) -> int:
        return self.index.bit_width

    def __len__(self) -> int:
        return len(self.documents)

    def contains(self, key: str) -> bool:
        return key in self.key_to_id

    def filter_keys(self, metadata_filter: Optional[Dict[str, Any]] = None) -> List[str]:
        if not metadata_filter:
            return sorted(self.documents.keys())
        matches: List[str] = []
        for key, payload in self.documents.items():
            metadata = payload.get("metadata") or {}
            if all(metadata.get(k) == v for k, v in metadata_filter.items()):
                matches.append(key)
        return sorted(matches)

    def add(self, items: Iterable[Dict[str, Any]]) -> Dict[str, Any]:
        materialized = list(items)
        if not materialized:
            return {"added": 0, "keys": []}

        vectors = _normalize_vectors(item["vector"] for item in materialized)
        ids: List[int] = []
        normalized_items: List[Dict[str, Any]] = []

        for item in materialized:
            key = str(item["key"])
            if key in self.key_to_id:
                external_id = self.key_to_id[key]
                self.index.remove(external_id)
            else:
                external_id = self.next_id
                self.next_id += 1
            ids.append(external_id)
            normalized_items.append({
                "key": key,
                "title": item.get("title") or key,
                "path": item.get("path") or key,
                "text": item.get("text", ""),
                "metadata": dict(item.get("metadata") or {}),
            })

        self.index.add_with_ids(vectors, np.asarray(ids, dtype=np.uint64))
        for external_id, payload in zip(ids, normalized_items):
            key = payload["key"]
            self.key_to_id[key] = int(external_id)
            self.documents[key] = {
                **payload,
                "id": int(external_id),
            }
        return {"added": len(normalized_items), "keys": [item["key"] for item in normalized_items]}

    def remove(self, key: str) -> bool:
        if key not in self.key_to_id:
            return False
        external_id = self.key_to_id.pop(key)
        self.documents.pop(key, None)
        return bool(self.index.remove(external_id))

    def search(self, query_vector: Iterable[float], top_k: int = 5,
               *, allow_keys: Optional[Iterable[str]] = None,
               metadata_filter: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        query = _normalize_query(query_vector)
        allowset: Optional[List[str]] = None
        if allow_keys is not None:
            allowset = [str(k) for k in allow_keys if str(k) in self.key_to_id]
        if metadata_filter:
            filtered = set(self.filter_keys(metadata_filter))
            allowset = sorted(filtered if allowset is None else filtered.intersection(allowset))
        if allowset is not None and not allowset:
            return []

        kwargs: Dict[str, Any] = {}
        effective_k = max(int(top_k), 1)
        if allowset is not None:
            allow_ids = [self.key_to_id[key] for key in allowset]
            kwargs["allowlist"] = np.asarray(allow_ids, dtype=np.uint64)
            effective_k = min(effective_k, len(allow_ids))
        scores, ids = self.index.search(query, k=effective_k, **kwargs)
        results: List[Dict[str, Any]] = []
        for score, external_id in zip(scores[0].tolist(), ids[0].tolist()):
            match = next((doc for doc in self.documents.values() if doc["id"] == int(external_id)), None)
            if not match:
                continue
            results.append({
                "key": match["key"],
                "id": int(external_id),
                "score": float(score),
                "title": match.get("title") or match["key"],
                "path": match.get("path") or match["key"],
                "metadata": dict(match.get("metadata") or {}),
            })
        return results

    def persist(self, directory: str | Path) -> Dict[str, Any]:
        directory = Path(directory)
        directory.mkdir(parents=True, exist_ok=True)
        index_path = directory / INDEX_NAME
        manifest_path = directory / MANIFEST_NAME
        self.index.write(str(index_path))
        payload = {
            "schema_version": SCHEMA_VERSION,
            "bit_width": self.bit_width,
            "dim": self.dim,
            "next_id": self.next_id,
            "documents": sorted(self.documents.values(), key=lambda item: item["id"]),
            "key_to_id": self.key_to_id,
        }
        manifest_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        return {"index_path": str(index_path), "manifest_path": str(manifest_path)}

    @classmethod
    def load(cls, directory: str | Path) -> "TurboVecAdapter":
        directory = Path(directory)
        manifest = json.loads((directory / MANIFEST_NAME).read_text(encoding="utf-8"))
        if manifest.get("schema_version") != SCHEMA_VERSION:
            raise ValueError(f"unsupported schema_version: {manifest.get('schema_version')}")
        index = IdMapIndex.load(str(directory / INDEX_NAME))
        documents = {str(item["key"]): dict(item) for item in manifest.get("documents", [])}
        return cls(
            dim=manifest.get("dim"),
            bit_width=int(manifest.get("bit_width", 4)),
            index=index,
            documents=documents,
            key_to_id={str(k): int(v) for k, v in (manifest.get("key_to_id") or {}).items()},
            next_id=int(manifest.get("next_id", 1)),
        )


def _unit_normalize(vectors: "np.ndarray") -> "np.ndarray":
    norms = np.linalg.norm(vectors, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    return np.ascontiguousarray(vectors / norms)


def run_synthetic_benchmark(num_docs: int = 256, dim: int = 64, queries: int = 4,
                            top_k: int = 5, bit_width: int = 4) -> Dict[str, Any]:
    if not turbovec_available():
        raise RuntimeError(f"turbovec adapter unavailable: {_IMPORT_ERROR or 'numpy/turbovec not installed'}")
    if dim % 8 != 0:
        raise ValueError("dim must be a positive multiple of 8 for turbovec")

    rng = np.random.default_rng(42)
    doc_vectors = _unit_normalize(rng.normal(size=(num_docs, dim)).astype(np.float32))
    query_vectors = _unit_normalize(rng.normal(size=(queries, dim)).astype(np.float32))

    adapter = TurboVecAdapter(dim=dim, bit_width=bit_width)
    docs = []
    for idx in range(num_docs):
        docs.append({
            "key": f"doc-{idx}",
            "title": f"Synthetic Doc {idx}",
            "path": f"synthetic/doc-{idx}.md",
            "vector": doc_vectors[idx].tolist(),
            "metadata": {"tenant": "alpha" if idx % 2 == 0 else "beta", "bucket": idx % 7},
        })

    t0 = time.perf_counter()
    add_report = adapter.add(docs)
    add_ms = round((time.perf_counter() - t0) * 1000, 3)

    t1 = time.perf_counter()
    first_search = adapter.search(query_vectors[0].tolist(), top_k=top_k)
    search_ms = round((time.perf_counter() - t1) * 1000, 3)

    t2 = time.perf_counter()
    filtered = adapter.search(query_vectors[0].tolist(), top_k=top_k, metadata_filter={"tenant": "alpha"})
    filter_ms = round((time.perf_counter() - t2) * 1000, 3)

    temp_dir = Path(os.environ.get("TMPDIR", "/tmp")) / "local-brain-turbovec-benchmark"
    if temp_dir.exists():
        for child in temp_dir.iterdir():
            if child.is_file():
                child.unlink()
    temp_dir.mkdir(parents=True, exist_ok=True)

    persist_report = adapter.persist(temp_dir)
    reloaded = TurboVecAdapter.load(temp_dir)
    load_ok = len(reloaded) == num_docs
    reloaded_hits = reloaded.search(query_vectors[1].tolist(), top_k=top_k, allow_keys=[f"doc-{i}" for i in range(0, min(20, num_docs), 2)])
    removed = reloaded.remove("doc-0")

    return {
        "schema": SCHEMA_VERSION,
        "resolution": resolve_backend().to_dict(),
        "num_docs": num_docs,
        "dim": dim,
        "bit_width": bit_width,
        "queries": queries,
        "timings_ms": {
            "add": add_ms,
            "search": search_ms,
            "filter": filter_ms,
        },
        "verifications": {
            "add": add_report["added"] == num_docs,
            "search": bool(first_search),
            "filter": bool(filtered),
            "persist": Path(persist_report["index_path"]).exists(),
            "load": load_ok,
            "remove": removed,
        },
        "artifacts": persist_report,
        "first_result": first_search[0] if first_search else None,
        "filtered_result_count": len(filtered),
        "reload_result_count": len(reloaded_hits),
    }


def _build_argparser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Optional TurboVec adapter prototype for local-brain retrieval")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("status", help="Show backend resolution and dependency status")
    bench = sub.add_parser("benchmark", help="Run synthetic benchmark covering add/search/filter/persist/load/remove")
    bench.add_argument("--docs", type=int, default=256)
    bench.add_argument("--dim", type=int, default=64)
    bench.add_argument("--queries", type=int, default=4)
    bench.add_argument("--top", type=int, default=5)
    bench.add_argument("--bit-width", type=int, default=4)
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    parser = _build_argparser()
    args = parser.parse_args(argv)
    if args.command == "status":
        print(json.dumps({
            "schema": SCHEMA_VERSION,
            "resolution": resolve_backend().to_dict(),
            "turbovec_available": turbovec_available(),
            "import_error": _IMPORT_ERROR,
        }, ensure_ascii=False, indent=2))
        return 0
    if args.command == "benchmark":
        report = run_synthetic_benchmark(
            num_docs=args.docs,
            dim=args.dim,
            queries=args.queries,
            top_k=args.top,
            bit_width=args.bit_width,
        )
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 0
    parser.error(f"unknown command: {args.command}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
