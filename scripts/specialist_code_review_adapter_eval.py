#!/usr/bin/env python3
"""Local fixture evaluation for specialist code-review adapter patterns.

No external install, no API keys, no network, no private-code upload. The script
creates a synthetic diff/review fixture, builds a deterministic coverage
manifest, verifies reviewer finding positions, filters invalid/duplicate
findings, and writes a report. This evaluates the Hermes adapter contract, not a
third-party CLI benchmark.
"""
from __future__ import annotations

import argparse
import json
import tempfile
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

DEFAULT_OUT_DIR = Path.home() / ".hermes" / "docs" / "private" / "open-code-review-adapter-eval"


@dataclass
class FileRange:
    path: str
    changed_lines: list[int]
    risk_tags: list[str]
    bundle: str


@dataclass
class Finding:
    id: str
    file: str
    line: int
    severity: str
    message: str
    quote: str
    source: str = "fixture-reviewer"


def fixture() -> tuple[dict[str, str], list[FileRange], list[Finding]]:
    files = {
        "app/auth.py": "def login(user, password):\n    query = f\"SELECT * FROM users WHERE name='{user}'\"\n    return db.execute(query)\n",
        "app/ui.tsx": "export function Label({ text }) {\n  return <div>{text}</div>\n}\n",
        "docs/readme.md": "# Demo\n",
    }
    manifest = [
        FileRange("app/auth.py", [2], ["security", "sql-injection", "auth"], "auth-security"),
        FileRange("app/ui.tsx", [2], ["ui", "xss-check"], "ui-safety"),
        FileRange("docs/readme.md", [1], ["docs"], "docs-low-risk"),
    ]
    findings = [
        Finding("F1", "app/auth.py", 2, "blocker", "SQL query uses string interpolation with user input", "query = f\"SELECT * FROM users WHERE name='{user}'\""),
        Finding("F2", "app/auth.py", 99, "blocker", "Line drift example: valid file but invalid line", "missing"),
        Finding("F3", "app/missing.py", 1, "blocker", "Missing file example", "missing"),
        Finding("F4", "app/ui.tsx", 2, "advisory", "React escapes text; this is low confidence duplicate/noise", "return <div>{text}</div>"),
        Finding("F1-dup", "app/auth.py", 2, "blocker", "Duplicate of SQL interpolation finding", "query = f\"SELECT * FROM users WHERE name='{user}'\""),
    ]
    return files, manifest, findings


def verify(files: dict[str, str], manifest: list[FileRange], findings: list[Finding]) -> dict[str, Any]:
    ranges = {m.path: set(m.changed_lines) for m in manifest}
    exact_lines: dict[tuple[str, int], str] = {}
    for path, content in files.items():
        for i, line in enumerate(content.splitlines(), start=1):
            exact_lines[(path, i)] = line.strip()
    accepted: list[dict[str, Any]] = []
    rejected: list[dict[str, Any]] = []
    seen: set[tuple[str, int, str]] = set()
    for f in findings:
        reason = ""
        if f.file not in files:
            reason = "file_not_in_reviewed_tree"
        elif f.line not in ranges.get(f.file, set()):
            reason = "line_not_in_changed_range"
        elif f.quote and f.quote.strip() not in exact_lines.get((f.file, f.line), ""):
            reason = "quote_mismatch"
        else:
            # Duplicate detection is position/evidence based. Different wording
            # for the same file/line/quote should not create another blocker.
            key = (f.file, f.line, f.quote.strip())
            if key in seen:
                reason = "duplicate"
            else:
                seen.add(key)
        item = asdict(f)
        if reason:
            item["rejected_reason"] = reason
            rejected.append(item)
        else:
            # Precision-biased rule: only blocker/security findings survive as blockers.
            if f.severity != "blocker":
                item["accepted_as"] = "advisory"
            else:
                item["accepted_as"] = "blocker"
            accepted.append(item)
    return {
        "accepted": accepted,
        "rejected": rejected,
        "summary": {
            "input_findings": len(findings),
            "accepted": len(accepted),
            "rejected": len(rejected),
            "blockers": sum(1 for x in accepted if x.get("accepted_as") == "blocker"),
            "advisory": sum(1 for x in accepted if x.get("accepted_as") == "advisory"),
        },
    }


def evaluate() -> dict[str, Any]:
    files, manifest, findings = fixture()
    result = verify(files, manifest, findings)
    comparison = [
        {
            "dimension": "coverage",
            "existing_requesting_code_review": "reviews git diff, large diffs split manually",
            "specialist_adapter_contract": "coverage manifest enumerates changed files/ranges and ignored reasons before model review",
            "recommendation": "add manifest for large/high-risk diffs",
        },
        {
            "dimension": "line_position",
            "existing_requesting_code_review": "reviewer JSON is evaluated semantically; line validation not mandatory",
            "specialist_adapter_contract": "reject finding when file/line/quote does not match reviewed tree/range",
            "recommendation": "add position verifier before blocker status",
        },
        {
            "dimension": "external_cli",
            "existing_requesting_code_review": "no third-party CLI dependency",
            "specialist_adapter_contract": "optional only; requires separate install/provider authorization",
            "recommendation": "do not adopt by default",
        },
    ]
    return {
        "ok": True,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "boundary": "local fixture only; no install, no API key, no network, no private code upload",
        "manifest": [asdict(m) for m in manifest],
        "verification": result,
        "comparison": comparison,
        "decision": "Keep as Hermes-native review-control-plane pattern now; defer external OCR CLI adapter until exact install/provider/code-sharing authority exists.",
    }


def write_report(result: dict[str, Any], out_dir: Path) -> dict[str, str]:
    out_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    json_path = out_dir / f"adapter-eval-{stamp}.json"
    md_path = out_dir / f"adapter-eval-{stamp}.md"
    json_path.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    lines = [
        "# Specialist Code Review Adapter Evaluation",
        "",
        f"Generated: {result['generated_at']}",
        f"Boundary: {result['boundary']}",
        f"Decision: {result['decision']}",
        "",
        "## Verification Summary",
        "",
        f"- Input findings: {result['verification']['summary']['input_findings']}",
        f"- Accepted: {result['verification']['summary']['accepted']}",
        f"- Rejected: {result['verification']['summary']['rejected']}",
        f"- Blockers: {result['verification']['summary']['blockers']}",
        f"- Advisory: {result['verification']['summary']['advisory']}",
        "",
        "## Comparison",
        "",
    ]
    for row in result["comparison"]:
        lines.append(f"### {row['dimension']}")
        lines.append(f"- Existing: {row['existing_requesting_code_review']}")
        lines.append(f"- Specialist contract: {row['specialist_adapter_contract']}")
        lines.append(f"- Recommendation: {row['recommendation']}")
        lines.append("")
    md_path.write_text("\n".join(lines), encoding="utf-8")
    return {"json": str(json_path), "markdown": str(md_path)}


def selftest() -> dict[str, Any]:
    r = evaluate()
    assert r["verification"]["summary"]["input_findings"] == 5
    assert r["verification"]["summary"]["blockers"] == 1
    assert r["verification"]["summary"]["rejected"] == 3
    return {"ok": True, "summary": r["verification"]["summary"]}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out-dir", default=str(DEFAULT_OUT_DIR))
    ap.add_argument("--write-report", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--pretty", action="store_true")
    args = ap.parse_args()
    result = selftest() if args.selftest else evaluate()
    if args.write_report and not args.selftest:
        result["reports"] = write_report(result, Path(args.out_dir).expanduser())
    print(json.dumps(result, ensure_ascii=False, indent=2 if args.pretty else None, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
