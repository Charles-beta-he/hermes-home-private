from __future__ import annotations
import hashlib
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class TranscriptEvent:
    session_id: str
    text: str
    final: bool
    source: str = "manual_or_runtime"


class TranscriptRouter:
    """Routes real transcript text; empty results fail closed without fabricated fallback."""
    def route(self, event: TranscriptEvent) -> dict[str, Any]:
        text=" ".join(event.text.split())
        if not event.session_id.strip(): raise ValueError("session_id is required")
        if not text: return {"status":"blocked","reason":"empty_transcript","append_to_ledger":False}
        return {"status":"partial" if not event.final else "final","session_id":event.session_id,"text":text,"append_to_ledger":event.final}


class MonitorDeduplicator:
    """Local event dedupe contract; it neither schedules nor dispatches notifications."""
    def __init__(self): self._seen:set[str]=set()
    def evaluate(self, source_id: str, payload: str) -> dict[str, Any]:
        if not source_id.strip() or not payload.strip(): raise ValueError("source_id and payload are required")
        event_id=hashlib.sha256(f"{source_id}\0{payload}".encode()).hexdigest()[:20]
        duplicate=event_id in self._seen
        if not duplicate: self._seen.add(event_id)
        return {"event_id":event_id,"status":"duplicate" if duplicate else "new","should_prepare_local_receipt":not duplicate,"should_dispatch":False}
