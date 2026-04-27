#!/usr/bin/env python3
"""
自进化管线 — 自动化全组件自测
验证每个组件可用并检查已知问题
"""

import os, sys, json, subprocess
from pathlib import Path

HERMES_HOME = os.path.expanduser("~/.hermes")
SELF_TEST_DB = "/tmp/hermes-self-test-route_outcomes.db"
ROUTE_ENV = dict(os.environ, HERMES_ROUTE_DB_PATH=SELF_TEST_DB)
if os.path.exists(SELF_TEST_DB):
    os.remove(SELF_TEST_DB)

tests = []
passed = 0
failed = 0

def test(name, fn):
    global passed, failed
    try:
        ok, msg = fn()
        if ok:
            passed += 1
            print(f"  ✓ {name}")
        else:
            failed += 1
            print(f"  ✗ {name}: {msg}")
    except Exception as e:
        failed += 1
        print(f"  ✗ {name}: {e}")
    tests.append((name, ok if 'ok' in dir() else False))

# ── 文件存在性 ──

FILES = [
    "scripts/post-session-autopsy.py",       # L0 sensor
    "scripts/self-improvement-pipeline.py",  # L0 prioritizer
    "scripts/route_store.py",                # L1 store
    "scripts/eval-harness.py",               # L4 gate
    "agent-hooks/record-trace.sh",           # L1 hook
    f"skills/software-development/router/SKILL.md",                  # L2 skill
    f"skills/software-development/self-improvement-pipeline/SKILL.md",# system skill
    os.path.expanduser("~/.pua/evolution.md"),       # evolution tracking
]

for f in FILES:
    path = os.path.join(HERMES_HOME, f) if not f.startswith("~") else os.path.expanduser(f)
    test(f"File exists: {os.path.basename(path)}", lambda p=path: (os.path.exists(p), f"not found: {p}"))

# ── Executable ──

test("record-trace.sh is executable", lambda: (
    os.access(os.path.join(HERMES_HOME, "agent-hooks/record-trace.sh"), os.X_OK),
    "not executable"
))

# ── Config.yaml hooks ──

test("config.yaml has hooks", lambda: (
    os.path.exists(os.path.join(HERMES_HOME, "config.yaml")),
    "config.yaml missing"
))

with open(os.path.join(HERMES_HOME, "config.yaml")) as f:
    cfg = f.read()
test("hooks_auto_accept = true", lambda: (
    "hooks_auto_accept: true" in cfg,
    f"hooks_auto_accept not set to true"
))
test("record-trace in hooks", lambda: (
    "record-trace.sh" in cfg,
    "record-trace.sh hook not registered in config.yaml"
))

# ── Route Store CLI ──

r = subprocess.run(
    [sys.executable, os.path.join(HERMES_HOME, "scripts/route_store.py"), "summary"],
    capture_output=True, text=True, timeout=10, env=ROUTE_ENV
)
test("route_store.py summary runs", lambda: (r.returncode == 0, r.stderr[:100]))

# ── Route Store: append + query + stats + scores ──

r = subprocess.run(
    [sys.executable, os.path.join(HERMES_HOME, "scripts/route_store.py"),
     "append", "--skill", "test-harness", "--task_class", "self_test",
     "--route", "verify", "--verdict", "pass", "--duration_s", "0.5",
     "--tokens_in", "100", "--tokens_out", "50"],
    capture_output=True, text=True, timeout=10, env=ROUTE_ENV
)
test("route_store.py append works", lambda: (r.returncode == 0, r.stderr[:100]))

r = subprocess.run(
    [sys.executable, os.path.join(HERMES_HOME, "scripts/route_store.py"),
     "query", "--task-class", "self_test", "--limit", "5"],
    capture_output=True, text=True, timeout=10, env=ROUTE_ENV
)
has_data = "self_test" in r.stdout
test("route_store.py query by task_class", lambda: (has_data, f"no results for self_test"))

r = subprocess.run(
    [sys.executable, os.path.join(HERMES_HOME, "scripts/route_store.py"),
     "stats", "--task-class", "self_test"],
    capture_output=True, text=True, timeout=10, env=ROUTE_ENV
)
has_pass = '"pass_rate": 1.0' in r.stdout or '"pass_rate": 1' in r.stdout
test("route_store.py stats pass_rate=1.0", lambda: (has_pass, f"stats unexpected: {r.stdout[:200]}"))

r = subprocess.run(
    [sys.executable, os.path.join(HERMES_HOME, "scripts/route_store.py"),
     "scores", "--task-class", "self_test"],
    capture_output=True, text=True, timeout=10, env=ROUTE_ENV
)
test("route_store.py scores returns list", lambda: (
    r.returncode == 0 and "score" in r.stdout,
    f"scores failed: {r.stderr[:100]}"
))

# ── Post-Session Autopsy ──

r = subprocess.run(
    [sys.executable, os.path.join(HERMES_HOME, "scripts/post-session-autopsy.py"),
     "--recent", "2"],
    capture_output=True, text=True, timeout=15
)
has_report = "Post-Session Autopsy Report" in r.stdout
test("post-session-autopsy.py --recent 2", lambda: (has_report, r.stderr[:200] or r.stdout[-200:]))

# ── Self-Improvement Pipeline ──

r = subprocess.run(
    [sys.executable, os.path.join(HERMES_HOME, "scripts/self-improvement-pipeline.py"),
     "--preview"],
    capture_output=True, text=True, timeout=15
)
test("self-improvement-pipeline.py --preview", lambda: (r.returncode == 0, r.stderr[:200]))

# ── Eval Harness ──

r = subprocess.run(
    [sys.executable, os.path.join(HERMES_HOME, "scripts/eval-harness.py"),
     "--status"],
    capture_output=True, text=True, timeout=10
)
test("eval-harness.py --status", lambda: (r.returncode == 0, r.stderr[:200]))

# ── Skills-staging dir ──

staging = os.path.join(HERMES_HOME, "skills-staging")
test("skills-staging/ directory exists", lambda: (
    os.path.isdir(staging), "not found"
))

# ── Evolution.md ──

evo = os.path.expanduser("~/.pua/evolution.md")
test("evolution.md exists", lambda: (
    os.path.exists(evo), "not found"
))

# ── Improvement signals file ──

sig = os.path.join(HERMES_HOME, "notes/improvement-signals.jsonl")
test("improvement-signals.jsonl exists", lambda: (
    os.path.exists(sig), "not found; run autopsy --recent 5 --write"
))

# ── Route outcomes DB ──

db = os.path.join(HERMES_HOME, "route_outcomes.db")
db_ok = os.path.exists(db)
if db_ok:
    import sqlite3
    conn = sqlite3.connect(db)
    tables = conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
    table_names = [t[0] for t in tables]
    has_table = "route_outcomes" in table_names
    count = conn.execute("SELECT COUNT(*) FROM route_outcomes").fetchone()[0]
    conn.close()
    test("route_outcomes.db has table + data", lambda: (
        has_table and count > 0,
        f"table ok={has_table}, row_count={count}"
    ))
else:
    test("route_outcomes.db exists", lambda: (False, "not found"))

# ── Summary ──

print(f"\n{'='*50}")
print(f"  Self-Test Results: {passed}/{passed+failed} passed")
if failed > 0:
    print(f"  FAILURES: {failed}")
    print(f"  Run manual checks on failing components")
else:
    print(f"  ALL PASS — system is operational")
print(f"{'='*50}")

sys.exit(0 if failed == 0 else 1)
