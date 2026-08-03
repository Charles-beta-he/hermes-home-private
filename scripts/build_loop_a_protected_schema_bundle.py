#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

from loop_a_protected.schema_bundle import SchemaBundleError, export_schema_bundle


DEFAULT_OUTPUT = Path(__file__).resolve().parents[1] / "docs/private/dreaming-loop-a-schema-bundle-v1.json"


def main() -> int:
    parser = argparse.ArgumentParser(description="Build or verify the frozen Loop A schema bundle artifact")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    try:
        data = export_schema_bundle(args.output, check=args.check)
    except SchemaBundleError as exc:
        parser.exit(1, f"error: {exc}\n")
    print(f"{'verified' if args.check else 'wrote'} {args.output} ({len(data)} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
