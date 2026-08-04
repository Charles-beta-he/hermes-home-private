from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from loop_a_protected.canonical import canonical_bytes
from loop_a_protected.darwin_runtime_bundle import (
    build_darwin_runtime_bundle,
    write_deterministic_runtime_archive,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Build one digest-bound Darwin Loop A runtime archive")
    parser.add_argument("--python", required=True, type=Path)
    parser.add_argument("--python-sha256", required=True)
    parser.add_argument("--stdlib", required=True, type=Path)
    parser.add_argument("--stdlib-digest", required=True)
    parser.add_argument("--libpython", required=True, type=Path)
    parser.add_argument("--libpython-sha256", required=True)
    parser.add_argument("--execution-closure", required=True, type=Path)
    parser.add_argument("--release-lineage", required=True)
    parser.add_argument("--release-sequence", required=True, type=int)
    parser.add_argument("--created-at", required=True)
    parser.add_argument("--policy-generation", required=True, type=int)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--report", required=True, type=Path)
    args = parser.parse_args()

    closure = json.loads(args.execution_closure.read_text(encoding="utf-8"))
    bundle = build_darwin_runtime_bundle(
        cpython_source=args.python.resolve(),
        authorized_cpython_sha256=args.python_sha256,
        stdlib_source=args.stdlib.resolve(),
        authorized_stdlib_digest=args.stdlib_digest,
        libpython_source=args.libpython.resolve(),
        authorized_libpython_sha256=args.libpython_sha256,
        release_lineage=args.release_lineage,
        release_sequence=args.release_sequence,
        created_at=args.created_at,
        policy_generation=args.policy_generation,
        execution_closure=closure,
    )
    output, archive_digest = write_deterministic_runtime_archive(bundle, args.output.resolve())
    report = {
        "schema": 1,
        "authority": "local-reversible-candidate-only",
        "runtime_manifest_digest": bundle.manifest["version_digest"],
        "runtime_inventory_digest": bundle.inventory["inventory_digest"],
        "archive_path": str(output),
        "archive_byte_count": output.stat().st_size,
        "archive_sha256": archive_digest,
        "python_sha256": args.python_sha256,
        "stdlib_digest": args.stdlib_digest,
        "libpython_sha256": args.libpython_sha256,
        "execution_closure_sha256": hashlib.sha256(canonical_bytes(closure)).hexdigest(),
        "file_count": len(bundle.contents),
    }
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_bytes(canonical_bytes(report))
    print(canonical_bytes(report).decode("utf-8"), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
