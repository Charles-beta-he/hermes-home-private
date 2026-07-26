#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, Mapping

from work_package_compiler import CompileError, compile_work_package, digest


def compile_batch(seeds: Iterable[Mapping[str, Any]], routing: Mapping[str, Any]) -> Dict[str, Any]:
    accepted = []
    rejected = []
    for index, seed in enumerate(seeds):
        candidate_id = seed.get("content", {}).get("content_id", f"candidate-{index}")
        try:
            accepted.append(compile_work_package(seed, routing))
        except (CompileError, KeyError, TypeError, ValueError) as exc:
            rejected.append(
                {
                    "candidate_id": candidate_id,
                    "error": str(exc),
                    "state": "rejected",
                }
            )

    result: Dict[str, Any] = {
        "schema_version": 1,
        "summary": {
            "accepted": len(accepted),
            "rejected": len(rejected),
            "total": len(accepted) + len(rejected),
        },
        "accepted": accepted,
        "rejected": rejected,
        "authority": {
            "may_publish": False,
            "may_submit_platform": False,
        },
    }
    result["batch_digest"] = digest(result)
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Compile a batch of mini-game candidates")
    parser.add_argument("--batch", required=True, help="JSON array of seed objects")
    parser.add_argument("--routing", required=True)
    parser.add_argument("--output")
    args = parser.parse_args()
    try:
        seeds = json.loads(Path(args.batch).read_text(encoding="utf-8"))
        routing = json.loads(Path(args.routing).read_text(encoding="utf-8"))
        if not isinstance(seeds, list):
            raise ValueError("batch must be a JSON array")
        result = compile_batch(seeds, routing)
    except (OSError, json.JSONDecodeError, TypeError, ValueError) as exc:
        print(json.dumps({"status": "blocked", "error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2

    rendered = json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if args.output:
        Path(args.output).write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
