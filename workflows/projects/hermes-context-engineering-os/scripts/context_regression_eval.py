#!/usr/bin/env python3
"""Context Regression Eval for Hermes Context Engineering OS.

Runs pass/fail fixture expectations against the local Context Packet linter.
No external services, no lifecycle writes, no model calls.
"""
import subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LINT = ROOT / "scripts" / "context_packet_lint.py"
PASS_DIR = ROOT / "eval" / "fixtures" / "pass"
FAIL_DIR = ROOT / "eval" / "fixtures" / "fail"


def run_packet(path: Path):
    proc = subprocess.run([sys.executable, str(LINT), str(path)], text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    return proc.returncode, proc.stdout.strip()


def main() -> int:
    failures = []
    checked = 0
    for path in sorted(PASS_DIR.glob("*.json")):
        checked += 1
        code, out = run_packet(path)
        print(f"PASS_EXPECT {path.name}: exit={code}")
        if code != 0:
            failures.append((path, "expected pass", out))
    for path in sorted(FAIL_DIR.glob("*.json")):
        checked += 1
        code, out = run_packet(path)
        print(f"FAIL_EXPECT {path.name}: exit={code}")
        if code == 0:
            failures.append((path, "expected fail", out))
    if failures:
        print("\nREGRESSION FAIL")
        for path, expected, out in failures:
            print(f"- {path}: {expected}\n{out}")
        return 1
    print(f"\nREGRESSION PASS checked={checked}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
