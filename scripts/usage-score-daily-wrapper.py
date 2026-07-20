#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

H = Path.home() / '.hermes'
SCRIPT = H / 'scripts' / 'usage-score.py'
STATE = H / 'state' / 'usage-score.json'
DEPRECATED_STATE = H / 'scripts' / 'usage-score.json'
LOG = H / 'logs' / 'usage-score-daily-wrapper.jsonl'
TIMEOUT = 100


def utc() -> str:
    return datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')


def main() -> int:
    start = time.time()
    try:
        p = subprocess.run(
            [sys.executable, str(SCRIPT)],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=TIMEOUT,
        )
        res = {
            'ok': p.returncode == 0,
            'returncode': p.returncode,
            'timeout': False,
            'stdout_tail': (p.stdout or '')[-3000:],
            'stderr_tail': (p.stderr or '')[-2000:],
        }
    except subprocess.TimeoutExpired as e:
        out = e.stdout if isinstance(e.stdout, str) else ''
        err = e.stderr if isinstance(e.stderr, str) else ''
        res = {
            'ok': False,
            'returncode': 124,
            'timeout': True,
            'stdout_tail': out[-3000:],
            'stderr_tail': err[-2000:],
        }

    discussion_result = {
        'status': 'not_evaluated',
        'reason': 'usage_score_not_parsed',
    }
    try:
        usage_data = json.loads(STATE.read_text())
        components = usage_data.get('components') if isinstance(usage_data, dict) else {}
        if not isinstance(components, dict):
            components = {}
        self_evolution_closure = components.get('self_evolution_closure')
        if not isinstance(self_evolution_closure, dict):
            self_evolution_closure = {}
        closure_events = self_evolution_closure.get('closure_events_14d')
        closure_score = self_evolution_closure.get('score')
        closure_gap = closure_events == 0 or closure_score == 0 or closure_score == 0.0
        usage = {
            'artifact_path': str(STATE),
            'deprecated_artifact_path': str(DEPRECATED_STATE),
            'deprecated_artifact_exists': DEPRECATED_STATE.exists(),
            'score': usage_data.get('score'),
            'grade': usage_data.get('grade'),
            'ts': usage_data.get('ts'),
            'size': STATE.stat().st_size,
            'parse_ok': True,
            'self_evolution_closure': self_evolution_closure,
        }
        if closure_gap:
            discussion_result = {
                'status': 'advisory_action_proposed',
                'root_cause_class': 'verifier_gap',
                'trigger': 'self_evolution_closure_zero',
                'evidence': {
                    'usage_score_path': str(STATE),
                    'usage_score': usage_data.get('score'),
                    'usage_grade': usage_data.get('grade'),
                    'self_evolution_closure': self_evolution_closure,
                },
                'recommended_low_risk_action': (
                    'Inspect and repair self-evolution closure evidence emission before changing models, tiers, or cron cadence.'
                ),
                'forbidden_actions': ['swap_model', 'raise_tier', 'lower_tier', 'duplicate_cron'],
            }
        else:
            discussion_result = {
                'status': 'no_action',
                'reason': 'self_evolution_closure_nonzero',
                'evidence': {
                    'usage_score_path': str(STATE),
                    'self_evolution_closure': self_evolution_closure,
                },
            }
    except Exception as e:
        usage = {
            'artifact_path': str(STATE),
            'deprecated_artifact_path': str(DEPRECATED_STATE),
            'deprecated_artifact_exists': DEPRECATED_STATE.exists(),
            'parse_ok': False,
            'error': repr(e),
        }
        discussion_result = {
            'status': 'degraded_recorded',
            'reason': 'usage_score_unreadable',
            'error': repr(e),
            'recommended_low_risk_action': 'Repair usage-score generation/readability before changing models, tiers, or cron cadence.',
        }

    rec = {
        'ts': utc(),
        'ok': True,
        'status': 'ok' if res.get('ok') else 'timeout_recorded' if res.get('timeout') else 'degraded_recorded',
        'duration_s': round(time.time() - start, 3),
        'run': res,
        'usage': usage,
        'discussion_result': discussion_result,
    }
    LOG.parent.mkdir(parents=True, exist_ok=True)
    with LOG.open('a', encoding='utf-8') as f:
        f.write(json.dumps(rec, ensure_ascii=False) + '\n')
    print(json.dumps(rec, ensure_ascii=False, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
