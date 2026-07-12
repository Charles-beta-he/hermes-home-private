from __future__ import annotations

import hashlib
import json
import math
import re
import time
from collections import Counter
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Callable


def tokenize(text: str) -> list[str]:
    return re.findall(r"[a-z0-9_]+|[\u4e00-\u9fff]", text.lower())


@dataclass(frozen=True)
class EvidenceChunk:
    source_id: str
    chunk_id: str
    text: str


class LocalEvidenceRetriever:
    """Deterministic local-file retriever; it does not generate answers."""

    def __init__(self, chunks: list[EvidenceChunk]):
        self.chunks = chunks
        self._doc_tokens = [Counter(tokenize(c.text)) for c in chunks]
        self._df = Counter(token for doc in self._doc_tokens for token in doc)

    @classmethod
    def from_texts(cls, texts: dict[str, str], chunk_chars: int = 600) -> "LocalEvidenceRetriever":
        if chunk_chars < 50:
            raise ValueError("chunk_chars must be >= 50")
        chunks: list[EvidenceChunk] = []
        for source_id, text in sorted(texts.items()):
            normalized = " ".join(text.split())
            for index in range(0, len(normalized), chunk_chars):
                part = normalized[index:index + chunk_chars].strip()
                if part:
                    chunks.append(EvidenceChunk(source_id, f"{source_id}:{index // chunk_chars}", part))
        return cls(chunks)

    def search(self, query: str, limit: int = 5, min_score: float = 0.0) -> list[dict[str, Any]]:
        if not query.strip() or limit <= 0:
            return []
        if min_score < 0:
            raise ValueError("min_score must be non-negative")
        q = Counter(tokenize(query))
        total = max(len(self.chunks), 1)
        scored = []
        for chunk, doc in zip(self.chunks, self._doc_tokens):
            score = 0.0
            for token, qtf in q.items():
                tf = doc.get(token, 0)
                if tf:
                    score += qtf * (1.0 + math.log(tf)) * math.log(1.0 + total / (1 + self._df[token]))
            if score > 0 and score >= min_score:
                scored.append({"source_id": chunk.source_id, "chunk_id": chunk.chunk_id, "text": chunk.text, "score": round(score, 6)})
        return sorted(scored, key=lambda x: (-x["score"], x["chunk_id"]))[:limit]


@dataclass
class MemoryRecord:
    id: str
    owner: str
    text: str
    created_at: float
    expires_at: float | None
    metadata: dict[str, Any]


class JsonMemoryStore:
    """Owner-scoped, deduplicated, TTL-aware memory with atomic local persistence."""

    def __init__(self, path: Path, clock: Callable[[], float] = time.time):
        self.path = path
        self.clock = clock
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            self._write([])

    def _read(self) -> list[MemoryRecord]:
        return [MemoryRecord(**row) for row in json.loads(self.path.read_text(encoding="utf-8"))]

    def _write(self, rows: list[MemoryRecord]) -> None:
        tmp = self.path.with_suffix(self.path.suffix + ".tmp")
        tmp.write_text(json.dumps([asdict(r) for r in rows], ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        tmp.replace(self.path)

    def add(self, owner: str, text: str, ttl_seconds: int | None = None, metadata: dict[str, Any] | None = None, idempotency_key: str | None = None) -> MemoryRecord:
        owner, normalized = owner.strip(), " ".join(text.split())
        if not owner or not normalized:
            raise ValueError("owner and text are required")
        if ttl_seconds is not None and ttl_seconds <= 0:
            raise ValueError("ttl_seconds must be positive")
        metadata = metadata or {}
        required_scope = {"domain", "conversation_id", "role", "provenance"}
        if metadata and not required_scope <= set(metadata):
            raise ValueError("metadata must include domain, conversation_id, role, and provenance")
        now = self.clock()
        self.purge_expired()
        rows = self._read()
        identity = idempotency_key.strip() if idempotency_key else normalized
        digest = hashlib.sha256(f"{owner}\0{identity}".encode()).hexdigest()[:20]
        for row in rows:
            if row.id == digest:
                return row
        record = MemoryRecord(digest, owner, normalized, now, now + ttl_seconds if ttl_seconds else None, metadata)
        rows.append(record)
        self._write(rows)
        return record

    def list(self, owner: str) -> list[MemoryRecord]:
        self.purge_expired()
        return [r for r in self._read() if r.owner == owner]

    def search(self, owner: str, query: str, limit: int = 5) -> list[MemoryRecord]:
        terms = set(tokenize(query))
        rows = self.list(owner)
        scored = [(len(terms & set(tokenize(r.text))), r) for r in rows]
        return [r for score, r in sorted(scored, key=lambda x: (-x[0], -x[1].created_at)) if score > 0][:limit]

    def delete(self, owner: str, record_id: str) -> bool:
        rows = self._read()
        kept = [row for row in rows if not (row.owner == owner and row.id == record_id)]
        if len(kept) == len(rows):
            return False
        self._write(kept)
        return True

    def clear(self, owner: str, conversation_id: str | None = None) -> int:
        rows = self._read()
        def remove(row: MemoryRecord) -> bool:
            if row.owner != owner:
                return False
            return conversation_id is None or row.metadata.get("conversation_id") == conversation_id
        kept = [row for row in rows if not remove(row)]
        removed = len(rows) - len(kept)
        if removed:
            self._write(kept)
        return removed

    def purge_expired(self) -> int:
        now = self.clock()
        rows = self._read()
        kept = [r for r in rows if r.expires_at is None or r.expires_at > now]
        if len(kept) != len(rows):
            self._write(kept)
        return len(rows) - len(kept)


@dataclass(frozen=True)
class ToolSpec:
    name: str
    description: str
    side_effect: str
    handler: Callable[..., Any]


class GovernedToolRegistry:
    """Tool discovery plus fail-closed side-effect authorization."""

    ALLOWED_EFFECTS = {"none", "local_read", "local_write", "external_read", "external_write", "destructive"}

    def __init__(self):
        self._tools: dict[str, ToolSpec] = {}

    def register(self, spec: ToolSpec) -> None:
        if spec.side_effect not in self.ALLOWED_EFFECTS:
            raise ValueError("invalid side_effect")
        if spec.name in self._tools:
            raise ValueError("duplicate tool")
        self._tools[spec.name] = spec

    def discover(self) -> list[dict[str, str]]:
        return [{"name": t.name, "description": t.description, "side_effect": t.side_effect} for t in sorted(self._tools.values(), key=lambda x: x.name)]

    def invoke(self, name: str, arguments: dict[str, Any], allowed_effects: set[str] | None = None) -> Any:
        if name not in self._tools:
            raise KeyError(name)
        spec = self._tools[name]
        allowed = allowed_effects or {"none"}
        if spec.side_effect not in allowed:
            raise PermissionError(f"tool effect {spec.side_effect} is not authorized")
        return spec.handler(**arguments)
