#!/usr/bin/env python3
"""Unified JSONL event ledger for Hermes harness executors."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import time
from pathlib import Path
from typing import Any

HERMES_HOME = Path(os.environ.get("HERMES_HOME", str(Path.home() / ".hermes"))).expanduser()
LEDGER_PATH = HERMES_HOME / "state" / "harness-event-ledger.jsonl"


def canonical_json(obj: Any) -> str:
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def digest(obj: Any) -> str:
    return hashlib.sha256(canonical_json(obj).encode("utf-8")).hexdigest()


def utc_ts() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def append_event(*, kind: str, payload: dict[str, Any], ledger_path: str | Path | None = None) -> dict[str, Any]:
    path = Path(ledger_path).expanduser() if ledger_path else LEDGER_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    event = {
        "schema": "hermes_harness_event_v1",
        "kind": kind,
        "payload": payload,
        "payload_digest": digest(payload),
        "created_at": utc_ts(),
    }
    event["event_id"] = digest({"kind": kind, "payload_digest": event["payload_digest"]})
    # Idempotent append by event_id.
    if path.exists():
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            try:
                existing = json.loads(line)
            except Exception:
                continue
            if existing.get("event_id") == event["event_id"]:
                existing["already_recorded"] = True
                existing["ledger_path"] = str(path)
                return existing
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(event, ensure_ascii=False, sort_keys=True) + "\n")
    event["already_recorded"] = False
    event["ledger_path"] = str(path)
    return event


def list_events(*, ledger_path: str | Path | None = None, kind: str | None = None, limit: int = 50) -> list[dict[str, Any]]:
    path = Path(ledger_path).expanduser() if ledger_path else LEDGER_PATH
    if not path.exists():
        return []
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        event = json.loads(line)
        if kind and event.get("kind") != kind:
            continue
        rows.append(event)
    return rows[-limit:]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Harness event ledger")
    sub = parser.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("append")
    p.add_argument("--kind", required=True)
    p.add_argument("--payload-json", required=True)
    p.add_argument("--ledger-path", default=None)
    p = sub.add_parser("list")
    p.add_argument("--kind", default=None)
    p.add_argument("--limit", type=int, default=50)
    p.add_argument("--ledger-path", default=None)
    args = parser.parse_args(argv)
    if args.cmd == "append":
        print(json.dumps(append_event(kind=args.kind, payload=json.loads(args.payload_json), ledger_path=args.ledger_path), ensure_ascii=False, indent=2))
    elif args.cmd == "list":
        print(json.dumps(list_events(ledger_path=args.ledger_path, kind=args.kind, limit=args.limit), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
