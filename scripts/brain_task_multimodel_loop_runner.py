#!/usr/bin/env python3
"""Evidence-first multi-model loop runner for local-brain tasks.

This is a control-plane orchestrator, not a Markdown executor. Each loop round:
1. runs deterministic gates,
2. writes a claim/evidence state bundle,
3. runs (or evaluates a supplied) consult_models discussion artifact,
4. stops only when ratification says the work is complete.

If models return amend/not_certified, the runner fails closed unless an explicit
bounded --executor-command is provided by a higher-level operator.
"""
from __future__ import annotations

import argparse
import json
import os
import shlex
import subprocess
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

TZ = timezone(timedelta(hours=8))
HOME = Path.home()
HERMES_HOME = Path(os.environ.get("HERMES_HOME", str(HOME / ".hermes"))).expanduser().resolve()
SCRIPTS = HERMES_HOME / "scripts"
CONSULT = SCRIPTS / "consult_models.py"
DEFAULT_ROUND_DIR = HERMES_HOME / "state" / "brain_task_multimodel_loop"

CERTIFIED_STATUSES = {"certified", "certified_with_minor_risks"}
CLOSED_ISSUE_STATUSES = {"resolved", "accepted_risk", "closed", "noop", "non_blocking", "non-blocking"}
APPROVE_VOTES = {"approve", "approved"}

DEFAULT_TARGET_FILES = [
    "scripts/brain_task_orchestrator.py",
    "scripts/brain_task_dispatch_tick.py",
    "scripts/brain_task_idle_runner.py",
    "scripts/test_brain_task_orchestrator.py",
    "scripts/test_brain_task_dispatch_tick.py",
    "scripts/test_brain_task_idle_runner.py",
]

DEFAULT_VERIFY_COMMANDS = [
    "python3 -m py_compile scripts/brain_task_orchestrator.py scripts/brain_task_dispatch_tick.py scripts/brain_task_idle_runner.py scripts/test_brain_task_orchestrator.py scripts/test_brain_task_dispatch_tick.py scripts/test_brain_task_idle_runner.py scripts/test_brain_task_multimodel_loop_runner.py",
    "python3 scripts/test_brain_task_orchestrator.py",
    "python3 scripts/test_brain_task_dispatch_tick.py",
    "python3 scripts/test_brain_task_idle_runner.py",
    "python3 scripts/test_brain_task_multimodel_loop_runner.py",
    "python3 scripts/brain_task_orchestrator.py selfcheck --json",
    "python3 scripts/brain_task_orchestrator.py proof-check --json",
    "python3 scripts/brain_task_idle_runner.py --json",
]


def iso() -> str:
    return datetime.now(TZ).replace(microsecond=0).isoformat()


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def run_command(cmd: str, timeout: int = 180) -> dict[str, Any]:
    start = time.time()
    proc = subprocess.run(
        cmd,
        cwd=str(HERMES_HOME),
        shell=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=timeout,
        check=False,
    )
    return {
        "cmd": cmd,
        "returncode": proc.returncode,
        "ok": proc.returncode == 0,
        "duration_seconds": round(time.time() - start, 3),
        "stdout_tail": (proc.stdout or "")[-3000:],
        "stderr_tail": (proc.stderr or "")[-3000:],
    }


def deterministic_gates(skip: bool = False, extra_commands: list[str] | None = None) -> dict[str, Any]:
    commands = list(DEFAULT_VERIFY_COMMANDS)
    commands.extend(extra_commands or [])
    if skip:
        return {"status": "SKIPPED", "commands": [], "failures": []}
    results = [run_command(cmd) for cmd in commands]
    failures = [r for r in results if not r.get("ok")]
    return {"status": "PASS" if not failures else "FAIL", "commands": results, "failures": failures}


def build_state_payload(question: str, gates: dict[str, Any], round_index: int, target_files: list[str] | None = None) -> dict[str, Any]:
    target_files = target_files or DEFAULT_TARGET_FILES
    claims = [
        {
            "id": "C-001",
            "text": "The local-brain automation remains fail-closed: default ticks observe only and do not execute Markdown task bodies or mark tasks done.",
        },
        {
            "id": "C-002",
            "text": "A loop round is complete only when deterministic gates pass and multi-model ratification has no unresolved severity>=3 issues, no amend/reject votes, and sufficient agreement.",
        },
    ]
    evidence = [
        {
            "id": f"E-{round_index:03d}-deterministic-gates",
            "type": "command_bundle",
            "supports": ["C-001", "C-002"],
            "status": gates.get("status"),
            "summary": {
                "command_count": len(gates.get("commands") or []),
                "failure_count": len(gates.get("failures") or []),
            },
            "commands": gates.get("commands") or [],
        }
    ]
    return {
        "schema": "brain_task_multimodel_loop_state_v1",
        "question": question,
        "generated_at": iso(),
        "round_index": round_index,
        "context": {
            "hermes_home": str(HERMES_HOME),
            "target_files": target_files,
            "automation_boundary": "control-plane only; no Markdown execution; no automatic done",
        },
        "constraints": [
            "Use evidence-first multi-model certification; model agreement without evidence is not enough.",
            "Default behavior must remain fail-closed and observe-only unless explicit gates pass.",
            "Stop the loop only when ratification says best_within_constraints and no severity>=3 blockers remain.",
        ],
        "acceptance_criteria": [
            "Deterministic gates pass.",
            "consult_models discussion_result status is certified or certified_with_minor_risks.",
            "All ratification votes approve and best_within_constraints=true when votes are present.",
            "No unresolved severity>=3 issue_ledger or remaining_risks entries.",
            "agreement_matrix framing/approach/implementation_order >= 0.85 when present.",
        ],
        "claims": claims,
        "evidence": evidence,
        "verify_commands": DEFAULT_VERIFY_COMMANDS,
    }


def write_state(path: Path, payload: dict[str, Any]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def build_consult_run_command(state_file: Path, tier: str = "T3", quorum: int = 4, max_rounds: int = 5, timeout: int = 180) -> list[str]:
    return [
        sys.executable,
        str(CONSULT),
        "run",
        str(state_file),
        "--tier",
        tier,
        "--quorum",
        str(quorum),
        "--discussion",
        "--max-rounds",
        str(max_rounds),
        "--timeout",
        str(timeout),
        "--keep",
    ]


def _severity(item: dict[str, Any]) -> int:
    try:
        return int(item.get("severity") or 0)
    except Exception:
        return 0


def _issue_status(item: dict[str, Any]) -> str:
    return str(item.get("status") or item.get("resolution_status") or "").strip().lower()


def open_high_severity(items: Any) -> list[dict[str, Any]]:
    out = []
    for item in items or []:
        if not isinstance(item, dict):
            continue
        if _severity(item) >= 3 and _issue_status(item) not in CLOSED_ISSUE_STATUSES:
            out.append(item)
    return out


def evaluate_discussion(discussion: dict[str, Any]) -> dict[str, Any]:
    passed, reasons = verify_ratification(discussion)
    status = str(discussion.get("status") or "not_certified").strip().lower()
    models = discussion.get("models_consulted") or []
    open_issues = open_high_severity(discussion.get("issue_ledger") or [])
    open_risks = open_high_severity(discussion.get("remaining_risks") or [])
    return {
        "done": passed,
        "next_action": "LOOP_DONE" if passed else "continue_loop",
        "blocking_reasons": reasons,
        "status": status,
        "model_count": len(models),
        "open_high_severity_issue_count": len(open_issues),
        "open_high_severity_remaining_risk_count": len(open_risks),
    }


def verify_ratification(discussion: dict[str, Any]) -> tuple[bool, list[str]]:
    """Return whether a discussion_result satisfies the stop gate.

    This is the explicit ratification verifier required by the loop contract:
    status certified, quorum-style model count, agreement threshold, closed
    high-severity ledger, approve votes, best_within_constraints, and grounded
    truth assessment. It intentionally returns reasons instead of raising so the
    issue ledger can drive the next loop round.
    """
    reasons: list[str] = []
    status = str(discussion.get("status") or "not_certified").strip().lower()
    if status not in CERTIFIED_STATUSES:
        reasons.append("status_not_certified")

    models = discussion.get("models_consulted") or []
    if len(models) < 3:
        reasons.append("insufficient_model_count")

    agreement = discussion.get("agreement_matrix") or {}
    for axis in ("framing", "approach", "implementation_order"):
        if axis in agreement:
            try:
                if float(agreement.get(axis) or 0) < 0.85:
                    reasons.append(f"agreement_below_threshold:{axis}")
            except Exception:
                reasons.append(f"agreement_invalid:{axis}")

    open_issues = open_high_severity(discussion.get("issue_ledger") or [])
    if open_issues:
        reasons.append("open_high_severity_issue")

    open_risks = open_high_severity(discussion.get("remaining_risks") or [])
    if open_risks:
        reasons.append("open_high_severity_remaining_risk")

    votes = discussion.get("ratification_votes") or []
    for vote in votes:
        if not isinstance(vote, dict):
            continue
        if str(vote.get("vote") or "").strip().lower() not in APPROVE_VOTES:
            reasons.append("non_approve_vote")
            break
        if vote.get("best_within_constraints") is False:
            reasons.append("best_within_constraints_false")
            break

    truth = discussion.get("truth_assessment") or discussion.get("truth_gate") or {}
    unsupported = truth.get("unsupported_high_severity_claim_ids") or []
    contradicted = truth.get("contradicted_high_severity_claim_ids") or []
    if unsupported:
        reasons.append("unsupported_high_severity_claim")
    if contradicted:
        reasons.append("contradicted_high_severity_claim")
    if "evidence_coverage" in truth:
        try:
            if float(truth.get("evidence_coverage") or 0) < 0.85:
                reasons.append("evidence_coverage_below_threshold")
        except Exception:
            reasons.append("evidence_coverage_invalid")

    deduped = sorted(set(reasons))
    return not deduped, deduped


def should_continue(discussion: dict[str, Any]) -> tuple[bool, str]:
    """Invert verify_ratification() for the driver stop/continue boundary."""
    passed, reasons = verify_ratification(discussion)
    if passed:
        return False, "all_criteria_met"
    return True, ",".join(reasons)


def newest_discussion_result(since: float) -> Path | None:
    candidates = []
    for p in HERMES_HOME.glob("tick-*/discussion_result.json"):
        try:
            if p.stat().st_mtime >= since:
                candidates.append(p)
        except OSError:
            continue
    return sorted(candidates, key=lambda p: p.stat().st_mtime)[-1] if candidates else None


def run_consult(state_file: Path, tier: str, quorum: int, max_rounds: int, timeout: int) -> dict[str, Any]:
    cmd = build_consult_run_command(state_file, tier=tier, quorum=quorum, max_rounds=max_rounds, timeout=timeout)
    start = time.time()
    outer_timeout = max(timeout * quorum + 120, timeout + 120)
    try:
        proc = subprocess.run(cmd, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=outer_timeout, check=False)
        returncode: int | str = proc.returncode
        stdout_tail = (proc.stdout or "")[-3000:]
        stderr_tail = (proc.stderr or "")[-3000:]
        timed_out = False
    except subprocess.TimeoutExpired as exc:
        returncode = "timeout"
        stdout_tail = ((exc.output or "") if isinstance(exc.output, str) else "")[-3000:]
        stderr_tail = ((exc.stderr or "") if isinstance(exc.stderr, str) else "")[-3000:]
        timed_out = True
    discussion_path = newest_discussion_result(start)
    return {
        "cmd": cmd,
        "returncode": returncode,
        "timed_out": timed_out,
        "timeout_seconds": outer_timeout,
        "stdout_tail": stdout_tail,
        "stderr_tail": stderr_tail,
        "discussion_result_path": str(discussion_path) if discussion_path else "",
    }


def run_executor(command: str, issue_ledger_path: Path, state_path: Path, timeout: int) -> dict[str, Any]:
    argv = shlex.split(command)
    env = os.environ.copy()
    env["HERMES_MM_LOOP_ISSUE_LEDGER"] = str(issue_ledger_path)
    env["HERMES_MM_LOOP_STATE"] = str(state_path)
    proc = subprocess.run(argv, cwd=str(HERMES_HOME), env=env, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=timeout, check=False)
    return {
        "cmd": argv,
        "returncode": proc.returncode,
        "ok": proc.returncode == 0,
        "stdout_tail": (proc.stdout or "")[-3000:],
        "stderr_tail": (proc.stderr or "")[-3000:],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run deterministic + multi-model certification loop for local-brain automation")
    parser.add_argument("--question", default="完善本地大脑任务池自动化流程：每轮 loop 推进后由多模型验证，直到多模型认为结束")
    parser.add_argument("--round-dir", default=str(DEFAULT_ROUND_DIR))
    parser.add_argument("--state-out", default="")
    parser.add_argument("--max-loop-rounds", type=int, default=3)
    parser.add_argument("--discussion-max-rounds", type=int, default=5)
    parser.add_argument("--tier", default="T3")
    parser.add_argument("--quorum", type=int, default=4)
    parser.add_argument("--timeout", type=int, default=180)
    parser.add_argument("--discussion-result", default="", help="Use existing discussion_result.json instead of calling models (test/replay mode)")
    parser.add_argument("--skip-deterministic", action="store_true")
    parser.add_argument("--executor-command", default="", help="Explicit bounded command to apply unresolved issue ledger between rounds")
    parser.add_argument("--executor-timeout", type=int, default=300)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    round_dir = Path(args.round_dir).expanduser()
    round_dir.mkdir(parents=True, exist_ok=True)
    rounds: list[dict[str, Any]] = []

    for i in range(1, max(args.max_loop_rounds, 1) + 1):
        gates = deterministic_gates(skip=args.skip_deterministic)
        state_path = Path(args.state_out).expanduser() if args.state_out else round_dir / f"round-{i:02d}-state.json"
        state = build_state_payload(args.question, gates, i)
        write_state(state_path, state)

        if gates.get("status") == "FAIL":
            payload = {"status": "DETERMINISTIC_GATES_FAILED", "rounds_used": i, "state_path": str(state_path), "rounds": rounds + [{"round": i, "gates": gates}]}
            print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
            return 2

        if args.discussion_result:
            discussion_path = Path(args.discussion_result).expanduser()
            consult_result = {"mode": "fixture", "discussion_result_path": str(discussion_path)}
        else:
            consult_result = run_consult(state_path, tier=args.tier, quorum=args.quorum, max_rounds=args.discussion_max_rounds, timeout=args.timeout)
            discussion_path = Path(consult_result.get("discussion_result_path") or "")

        if not discussion_path.exists():
            round_record = {"round": i, "gates": {"status": gates.get("status")}, "state_path": str(state_path), "consult": consult_result, "verdict": {"done": False, "blocking_reasons": ["discussion_result_missing"], "next_action": "continue_loop"}}
            rounds.append(round_record)
        else:
            discussion = load_json(discussion_path)
            verdict = evaluate_discussion(discussion)
            issue_path = round_dir / f"round-{i:02d}-issue-ledger.json"
            write_state(issue_path, {"issue_ledger": discussion.get("issue_ledger") or [], "remaining_risks": discussion.get("remaining_risks") or [], "verdict": verdict})
            round_record = {"round": i, "gates": {"status": gates.get("status")}, "state_path": str(state_path), "discussion_result_path": str(discussion_path), "issue_ledger_path": str(issue_path), "verdict": verdict}
            rounds.append(round_record)
            if verdict.get("done"):
                payload = {"status": "LOOP_DONE", "rounds_used": i, "rounds": rounds, "final_discussion_result": str(discussion_path)}
                print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
                return 0

            if args.executor_command and i < args.max_loop_rounds:
                executor = run_executor(args.executor_command, Path(round_record.get("issue_ledger_path", round_dir)), state_path, args.executor_timeout)
                round_record["executor"] = executor
                if not executor.get("ok"):
                    payload = {"status": "EXECUTOR_FAILED", "rounds_used": i, "rounds": rounds}
                    print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
                    return 4

        if not args.executor_command:
            break

    payload = {"status": "NOT_CERTIFIED_MAX_ROUNDS", "rounds_used": len(rounds), "rounds": rounds, "safety": "fail-closed; no Markdown execution and no automatic done"}
    print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
    return 3


if __name__ == "__main__":
    raise SystemExit(main())
