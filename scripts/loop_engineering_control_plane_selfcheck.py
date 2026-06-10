#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any

HOME = Path.home()
PROFILE_HERMES_HOME = Path(os.environ.get('HERMES_HOME', str(HOME / '.hermes'))).expanduser().resolve()
GLOBAL_HERMES_HOME = Path('/Users/charles/.hermes').resolve()


def detect_hermes_home() -> Path:
    candidates = [
        GLOBAL_HERMES_HOME,
        PROFILE_HERMES_HOME,
        (HOME / '.hermes').resolve(),
    ]
    for candidate in candidates:
        if (candidate / 'scripts' / 'taskpool_dynamic_runner.py').exists() and (candidate / 'docs' / 'private' / 'loop-engineering-wechat-intake-20260609.md').exists():
            return candidate
    for candidate in candidates:
        if (candidate / 'scripts' / 'taskpool_dynamic_runner.py').exists():
            return candidate
    return PROFILE_HERMES_HOME


HERMES_HOME = detect_hermes_home()
SCRIPTS = HERMES_HOME / 'scripts'

DYNAMIC_RUNNER = SCRIPTS / 'taskpool_dynamic_runner.py'
DYNAMIC_RUNNER_TEST = SCRIPTS / 'test_taskpool_dynamic_runner.py'
DISPATCH_TICK_TEST = SCRIPTS / 'test_brain_task_dispatch_tick.py'
MULTIMODEL_LOOP = SCRIPTS / 'brain_task_multimodel_loop_runner.py'
INTAKE_NOTE = HERMES_HOME / 'docs' / 'private' / 'loop-engineering-wechat-intake-20260609.md'


@dataclass
class CheckResult:
    id: str
    status: str
    summary: str
    evidence: list[dict[str, Any]]
    missing: list[str]



def read(path: Path) -> str:
    return path.read_text(encoding='utf-8')



def find_literal(text: str, needle: str) -> dict[str, Any] | None:
    idx = text.find(needle)
    if idx < 0:
        return None
    line = text[:idx].count('\n') + 1
    return {'match_type': 'literal', 'line': line, 'needle': needle}



def require_literals(path: Path, literals: list[str]) -> tuple[list[dict[str, Any]], list[str]]:
    text = read(path)
    evidence: list[dict[str, Any]] = []
    missing: list[str] = []
    for literal in literals:
        hit = find_literal(text, literal)
        if hit:
            evidence.append({'path': str(path), **hit})
        else:
            missing.append(f'{path.name}: {literal}')
    return evidence, missing



def check_source_intake() -> CheckResult:
    evidence, missing = require_literals(
        INTAKE_NOTE,
        [
            'Convert loop hype into governed agent-loop architecture',
            'Prefer event-governed taskpool loops over naive cron polling.',
            'Add loop budget controls: context-growth cap, iteration budget, cost estimation, dedupe, and no-output/non-convergence stop.',
            'Make feedback gates concrete: tests, type checks, real logs/errors, taskpool proof/evidence, regression harness, selfcheck.',
        ],
    )
    status = 'PASS' if not missing else 'FAIL'
    return CheckResult(
        id='source-intake-boundaries',
        status=status,
        summary='Intake note captures event-governed loop, budget, feedback gate, and anti-drift boundaries.' if status == 'PASS' else 'Intake note is missing one or more required Loop Engineering interpretation boundaries.',
        evidence=evidence,
        missing=missing,
    )



def check_dynamic_runner_preclaim_gate() -> CheckResult:
    source_evidence, source_missing = require_literals(
        DYNAMIC_RUNNER,
        [
            'event["human_escape"] = escape_status',
            'autorun_allowed = not bool(escape_status.get("triggered"))',
            'tick_cmd = [sys.executable, str(TICK), "--summary", "--no-state"]',
            'event["autorun_skipped_reason"] = "human_escape_active_preclaim"',
        ],
    )
    test_evidence, test_missing = require_literals(
        DYNAMIC_RUNNER_TEST,
        [
            'assert "--parallel-autorun" not in cmd, cmd',
            'assert "--autorun-step" not in cmd, cmd',
            'assert calls[0][-2:] == ["--summary", "--no-state"], calls[0]',
            'assert event["autorun_skipped_reason"] == "human_escape_active_preclaim"',
        ],
    )
    missing = source_missing + test_missing
    status = 'PASS' if not missing else 'FAIL'
    return CheckResult(
        id='dynamic-runner-preclaim-gate',
        status=status,
        summary='Dynamic runner keeps summary/no-state observation mode and skips preclaim autorun when human escape is active.' if status == 'PASS' else 'Dynamic runner preclaim gate evidence is incomplete.',
        evidence=source_evidence + test_evidence,
        missing=missing,
    )



def check_dispatch_tick_autorun_denial() -> CheckResult:
    evidence, missing = require_literals(
        DISPATCH_TICK_TEST,
        [
            'def test_tick_summary_autorun_step_denial_is_visible_and_non_mutating():',
            'assert payload["autorun"]["requested"] is True, payload',
            'assert payload["autorun"]["claimed"] is False, payload',
            'assert payload["autorun"]["advanced"] is False, payload',
            'assert "autorun_disabled" in payload["autorun"]["reasons"], payload',
            'assert task_row(env, task_id)["status"] == "pending"',
            'def test_tick_summary_ambient_multimodel_env_does_not_run_expensive_step():',
            'assert payload["multimodel_step"] == {}, payload',
        ],
    )
    status = 'PASS' if not missing else 'FAIL'
    return CheckResult(
        id='dispatch-tick-non-mutating-denial',
        status=status,
        summary='Dispatch tick tests prove denied autorun stays non-mutating and ambient multimodel env does not trigger the expensive step.' if status == 'PASS' else 'Dispatch tick denial/non-expensive-step evidence is incomplete.',
        evidence=evidence,
        missing=missing,
    )



def check_multimodel_feedback_gates() -> CheckResult:
    evidence, missing = require_literals(
        MULTIMODEL_LOOP,
        [
            '1. runs deterministic gates,',
            '4. stops only when ratification says the work is complete.',
            'DEFAULT_VERIFY_COMMANDS = [',
            'python3 scripts/brain_task_orchestrator.py proof-check --json',
            'python3 scripts/brain_task_orchestrator.py boundary-check --json',
            'python3 scripts/brain_task_idle_runner.py --json',
            'def collect_model_quota_probe(models: list[str] | None = None) -> dict[str, Any]:',
            'def deterministic_gates(skip: bool = False, extra_commands: list[str] | None = None) -> dict[str, Any]:',
            'return {"status": "PASS" if not failures else "FAIL", "commands": results, "failures": failures}',
        ],
    )
    status = 'PASS' if not missing else 'FAIL'
    return CheckResult(
        id='multimodel-feedback-gates',
        status=status,
        summary='Multi-model loop runner already encodes deterministic feedback gates, quota observability, and ratification stop conditions.' if status == 'PASS' else 'Multi-model loop runner evidence is incomplete.',
        evidence=evidence,
        missing=missing,
    )



def build_report() -> dict[str, Any]:
    checks = [
        check_source_intake(),
        check_dynamic_runner_preclaim_gate(),
        check_dispatch_tick_autorun_denial(),
        check_multimodel_feedback_gates(),
    ]
    failed = [c.id for c in checks if c.status != 'PASS']
    next_bounded_step = {
        'status': 'implemented',
        'artifact': str(Path(__file__).resolve()),
        'purpose': 'Provide a deterministic, re-runnable audit that Hermes taskpool loops stay event-governed, feedback-gated, and do not silently escalate into ambient expensive autorun.',
        'scope_boundary': 'Static evidence audit only; it does not mutate taskpool state, enable autorun, or certify runtime economics beyond the checked guardrails.',
    }
    return {
        'schema': 'loop_engineering_control_plane_selfcheck_v1',
        'status': 'PASS' if not failed else 'FAIL',
        'failed_checks': failed,
        'check_count': len(checks),
        'checks': [asdict(c) for c in checks],
        'next_bounded_step': next_bounded_step,
        'current_state_summary': {
            'source_intake': 'done',
            'event_governed_dynamic_runner_guard': 'present',
            'dispatch_tick_non_mutating_denial_test': 'present',
            'multimodel_feedback_gate_runner': 'present',
            'explicit_loop_engineering_audit': 'landed_by_this_script',
        },
    }



def main() -> int:
    parser = argparse.ArgumentParser(description='Deterministic Loop Engineering control-plane selfcheck for Hermes taskpool loops.')
    parser.add_argument('--json', action='store_true', help='print JSON report')
    parser.add_argument('--pretty', action='store_true', help='pretty-print JSON report')
    parser.add_argument('--out', help='write report JSON to path')
    args = parser.parse_args()

    report = build_report()
    if args.out:
        out_path = Path(args.out).expanduser().resolve()
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    text = json.dumps(report, ensure_ascii=False, indent=2 if (args.json or args.pretty) else None)
    print(text)
    return 0 if report['status'] == 'PASS' else 2


if __name__ == '__main__':
    raise SystemExit(main())
