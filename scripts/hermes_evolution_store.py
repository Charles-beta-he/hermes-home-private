#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import os
import shutil
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class ResolvedArtifact:
    relative_path: str
    path: Path
    source: str
    writable: bool
    degraded: bool = False
    reason: str = ""
    imported_from: str | None = None


class EvolutionStore:
    """Canonical writable store for Hermes dreaming/evolution runtime data.

    Skill packages and archived skill packages are definitions/history. Runtime
    evolution state is written under ~/.hermes/state/evolution so archiving a
    skill package cannot silently turn nightly evolution into a read-only loop.
    """

    def __init__(self, hermes_home: str | Path | None = None) -> None:
        self.home = Path(hermes_home or os.environ.get("HERMES_HOME") or Path.home() / ".hermes").expanduser()
        self.skills_dir = self.home / "skills"
        self.archived_skills_dir = self.home / "skills-archived"
        self.evolution_dir = self.home / "state" / "evolution"
        self.dreaming_dir = self.home / "state" / "dreaming"
        self.events_path = self.evolution_dir / "events.jsonl"
        self.runs_path = self.dreaming_dir / "canonical_state.jsonl"

    def canonical_path(self, relative_path: str) -> Path:
        clean = self._clean_relative_path(relative_path)
        return self.evolution_dir / clean

    def resolve_artifact(
        self,
        relative_path: str,
        *,
        intent: str = "read",
        import_if_missing: bool = True,
    ) -> ResolvedArtifact:
        """Resolve an evolution artifact.

        - write intent always returns the canonical writable path.
        - archived paths are read-only and degraded when returned for read intent.
        - if canonical is missing and archived/active source exists, write intent
          performs a one-time import into canonical and logs hashes.
        """
        if intent not in {"read", "write"}:
            raise ValueError(f"unsupported intent: {intent}")

        clean = self._clean_relative_path(relative_path)
        canonical = self.canonical_path(clean)
        active = self.skills_dir / clean
        archived = self.archived_skills_dir / clean

        if canonical.exists():
            return ResolvedArtifact(clean, canonical, "canonical", True)

        source_path: Path | None = None
        source_name = ""
        if active.exists():
            source_path = active
            source_name = "active_import"
        elif archived.exists():
            source_path = archived
            source_name = "archived"

        if intent == "write":
            if source_path is not None and import_if_missing:
                self._import_to_canonical(source_path, canonical, clean, source_name)
                return ResolvedArtifact(clean, canonical, "canonical", True, imported_from=str(source_path))
            canonical.parent.mkdir(parents=True, exist_ok=True)
            return ResolvedArtifact(clean, canonical, "canonical", True, degraded=True, reason="canonical_missing_created")

        if source_path is not None:
            if source_name == "archived":
                return ResolvedArtifact(clean, source_path, "archived", False, degraded=True, reason="archived_readonly")
            return ResolvedArtifact(clean, source_path, "active", True)

        return ResolvedArtifact(clean, canonical, "canonical", True, degraded=True, reason="missing")

    def append_event(self, event: str, details: dict[str, Any]) -> None:
        self.events_path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "schema": "hermes_evolution_store_event_v1",
            "ts": now_utc(),
            "event": event,
            "details": details,
        }
        with self.events_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(payload, ensure_ascii=False, sort_keys=True) + "\n")

    def read_events(self) -> list[dict[str, Any]]:
        if not self.events_path.exists():
            return []
        events: list[dict[str, Any]] = []
        for line in self.events_path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                events.append(json.loads(line))
        return events

    def append_dream_run(self, payload: dict[str, Any]) -> dict[str, Any]:
        self.runs_path.parent.mkdir(parents=True, exist_ok=True)
        record = {
            "schema": "hermes_dream_run_v1",
            "ts": now_utc(),
            **payload,
        }
        record.setdefault("proof_hash", stable_hash(record))
        with self.runs_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")
        return record

    def _import_to_canonical(self, source: Path, canonical: Path, relative_path: str, source_name: str) -> None:
        canonical.parent.mkdir(parents=True, exist_ok=True)
        if source.is_file():
            shutil.copy2(source, canonical)
        else:
            if canonical.exists():
                shutil.rmtree(canonical)
            shutil.copytree(source, canonical)
        self.append_event(
            "archive_imported" if source_name == "archived" else "active_imported",
            {
                "relative_path": relative_path,
                "source": str(source),
                "canonical": str(canonical),
                "source_kind": source_name,
                "source_sha256": file_sha256(source) if source.is_file() else None,
                "canonical_sha256": file_sha256(canonical) if canonical.is_file() else None,
                "readonly_source": source_name == "archived",
            },
        )

    @staticmethod
    def _clean_relative_path(relative_path: str) -> str:
        clean = str(Path(relative_path))
        if clean.startswith("/") or clean == "." or clean.startswith("..") or "/../" in clean:
            raise ValueError(f"relative_path must stay under evolution store: {relative_path}")
        return clean


def now_utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def file_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def stable_hash(payload: Any) -> str:
    data = json.dumps(payload, ensure_ascii=False, sort_keys=True, default=str).encode("utf-8")
    return hashlib.sha256(data).hexdigest()


def classify_nightly_result(returncode: int, stdout: str, stderr: str) -> dict[str, Any]:
    combined = f"{stdout}\n{stderr}"
    degraded = any(
        marker in combined
        for marker in [
            "(archived)",
            "preserving archived",
            "read-only",
            "readonly",
            "active confidence DB missing",
            "active darwin results.tsv missing",
        ]
    )
    state_advanced = any(marker in combined for marker in ["✓ 改进已保留", "skill_improved"])
    effective_audit = state_advanced or any(marker in combined for marker in ["= 无变化", "评分变化", "审计目标"])

    if returncode != 0:
        status = "ERROR"
    elif degraded:
        status = "WARN"
    elif state_advanced:
        status = "OK"
    elif effective_audit:
        status = "WARN"
    else:
        status = "WARN"

    if "无 skill 需要审计" in combined:
        effective_audit = False

    reasons: list[str] = []
    if degraded:
        reasons.append("degraded_or_readonly_source")
    if returncode != 0:
        reasons.append("script_returncode_nonzero")
    if effective_audit and not state_advanced:
        reasons.append("audit_without_state_advancement")
    if not effective_audit:
        reasons.append("no_effective_audit_detected")

    return {
        "status": status,
        "effective_audit": effective_audit,
        "state_advanced": state_advanced,
        "degraded": degraded,
        "write_blocked": degraded,
        "reasons": reasons,
    }


def resolved_to_dict(resolved: ResolvedArtifact) -> dict[str, Any]:
    data = asdict(resolved)
    data["path"] = str(resolved.path)
    return data


def default_store() -> EvolutionStore:
    return EvolutionStore()
