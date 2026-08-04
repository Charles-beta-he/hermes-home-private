#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any, Dict, List

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / "docs/private/dreaming-loop-a-hostile-uid-freeze-manifest-v10-candidate-20260803.json"
DOCS = (
    "docs/private/dreaming-loop-a-hostile-uid-protocol-v7-20260803.md",
    "docs/private/dreaming-loop-a-hostile-uid-protocol-v8-candidate-20260803.md",
    "docs/private/dreaming-loop-a-hostile-uid-v7-to-v8-normative-delta-20260803.md",
    "docs/private/dreaming-loop-a-hostile-uid-v8-to-v9-normative-delta-20260803.md",
    "docs/private/dreaming-loop-a-hostile-uid-v9-to-v10-normative-delta-20260803.md",
    "docs/private/dreaming-loop-a-schema-bundle-v1.json",
)
BUILDERS = (
    "scripts/build_loop_a_protected_schema_bundle.py",
    "scripts/build_loop_a_protected_freeze_manifest.py",
)


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8") + b"\n"


def candidate_paths() -> List[str]:
    paths: List[str] = [str(item) for item in (*DOCS, *BUILDERS)]
    paths.extend(
        item.relative_to(ROOT).as_posix()
        for item in (ROOT / "scripts/loop_a_protected").glob("*.py")
    )
    paths.extend(
        item.relative_to(ROOT).as_posix()
        for item in (ROOT / "scripts/loop_a_protected/native").glob("*.c")
    )
    paths.extend(
        item.relative_to(ROOT).as_posix()
        for item in (ROOT / "scripts").glob("test_loop_a_protected_*.py")
    )
    result = sorted(set(paths), key=lambda item: item.encode("ascii"))
    if len(result) != len(paths):
        raise ValueError("candidate path set contains duplicates")
    return result


def build_manifest() -> Dict[str, Any]:
    entries = []
    for relative in candidate_paths():
        path = ROOT / relative
        if not path.is_file() or path.is_symlink():
            raise ValueError(f"candidate path is not one regular file: {relative}")
        data = path.read_bytes()
        entries.append({"path": relative, "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()})
    candidate_payload = {
        "algorithm": "sha256(canonical-json(candidate-entries))",
        "candidate_entries": entries,
    }
    candidate_digest = hashlib.sha256(canonical_bytes(candidate_payload)).hexdigest()
    manifest = {
        "schema": 1,
        "candidate_revision": 10,
        "status": "candidate-hold",
        "authority": "local-reversible candidate; production root mutation requires exact digest-bound one-time authorization",
        "candidate_algorithm": candidate_payload["algorithm"],
        "candidate_entries": entries,
        "candidate_digest": candidate_digest,
        "manifest_digest": None,
    }
    preimage = canonical_bytes(manifest)
    manifest["manifest_digest"] = hashlib.sha256(preimage).hexdigest()
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description="Build or verify the Loop A revision-10 candidate freeze manifest")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    expected = canonical_bytes(build_manifest())
    if args.check:
        try:
            observed = args.output.read_bytes()
        except OSError as exc:
            parser.exit(1, f"error: cannot read manifest: {exc}\n")
        if observed != expected:
            parser.exit(1, "error: candidate freeze manifest drift\n")
        action = "verified"
    else:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_bytes(expected)
        action = "wrote"
    value = json.loads(expected)
    print(f"{action} {args.output} entries={len(value['candidate_entries'])} candidate={value['candidate_digest']} manifest={value['manifest_digest']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
