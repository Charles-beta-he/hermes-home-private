#!/usr/bin/env python3
"""V(x) System State Function — Complex Giant Systems health monitor.

V(x) = Σ wᵢ · fᵢ(xᵢ) ∈ [0, 1]

Components:
- orchestrator_health: selfcheck PASS=1, else 0
- dynamic_n_efficiency: applied_n / max(1, raw_n) 
- classifier_coverage: known_groups / total_dispatchable
- continuation_pressure: 1 - (active_checkpoints / max(1, total_tasks))
- envelope_health: live/since-ack risk score; historical terminal debt is diagnostic
- cron_health: 1 - (error_crons / max(1, total_crons))
- kanban_sync: mirrored / max(1, dispatchable)

V(x) < 0.5 → DEGRADED mode
V(x) < 0.3 → CRITICAL mode
"""
import json, subprocess, sys, time, math
from pathlib import Path

try:
    from kanban_coverage import live_report as kanban_coverage_live_report
except Exception:  # pragma: no cover - fail-soft for minimal recovery environments
    kanban_coverage_live_report = None

HOME = Path.home()
SCRIPTS = HOME / '.hermes' / 'scripts'
STATE = HOME / '.hermes' / 'state'

def safe_run(cmd, timeout=30):
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return r.stdout if r.returncode == 0 else ''
    except:
        return ''

def f_orchestrator():
    """Selfcheck PASS=1, FAIL=0."""
    out = safe_run(['python3', str(SCRIPTS / 'brain_task_orchestrator.py'), 'selfcheck'])
    return 1.0 if 'PASS' in out else 0.0

def f_dynamic_n():
    """applied_n / max(1, raw_n). Smooth transition bonus."""
    try:
        state = json.loads((STATE / 'dynamic_n_state.json').read_text())
        applied = state.get('current_n', 1)
        # Get raw from last history entry
        history = state.get('history', [])
        raw = history[-1].get('raw_n', 1) if history else 1
        if raw == 0:
            return 1.0  # No tasks = healthy
        return min(applied / max(1, raw), 1.0)
    except:
        return 0.5

def f_classifier():
    """Coverage: unique groups / sqrt(dispatchable). Capped at 1."""
    try:
        r = safe_run(['python3', str(SCRIPTS / 'task_classifier.py'), 'show'])
        data = json.loads(r)
        groups = len(data.get('groups', {}))
        dispatchable = data.get('dispatchable', 1)
        if dispatchable == 0:
            return 1.0
        return min(groups / max(1, math.sqrt(dispatchable)), 1.0)
    except:
        return 0.5

def f_continuation():
    """1 - (active_checkpoints / max(1, total_envelopes))."""
    try:
        cps = list((STATE / 'task_checkpoints').glob('*.json'))
        active = len(cps)
        # Total envelopes
        r = safe_run(['python3', str(SCRIPTS / 'envelope_bus.py'), 'stats'])
        data = json.loads(r)
        total = data.get('total', 1)
        return max(0, 1 - active / max(1, total))
    except:
        return 0.8

def envelope_diagnostics():
    """Return envelope health diagnostics separating live risk from history."""
    r = safe_run(['python3', str(SCRIPTS / 'envelope_bus.py'), 'stats'])
    data = json.loads(r)
    by_status = data.get('by_status', {}) if isinstance(data, dict) else {}
    escape_info = data.get('escape_info', {}) if isinstance(data, dict) else {}
    since_ack = escape_info.get('since_ack', {}) if isinstance(escape_info, dict) else {}
    historical = escape_info.get('historical', {}) if isinstance(escape_info, dict) else {}
    total = int(data.get('total', 0) or 0)
    pending = int(by_status.get('PENDING', 0) or 0)
    running = int(by_status.get('RUNNING', 0) or 0)
    timeouts = int(data.get('timeouts', 0) or 0)
    failures = int(since_ack.get('failures', 0) or 0)
    blocks = int(since_ack.get('blocks', 0) or 0)
    invalid_ts = int(since_ack.get('invalid_timestamps', 0) or 0)
    live_count = pending + running
    live_penalty = min(0.25, live_count / max(1, total) * 3)
    timeout_penalty = min(0.25, timeouts * 0.1)
    since_ack_penalty = min(0.65, failures * 0.15 + blocks * 0.2 + invalid_ts * 0.1)
    human_escape_penalty = 0.8 if data.get('human_escape_triggered') else 0.0
    score = max(0.0, 1.0 - live_penalty - timeout_penalty - since_ack_penalty - human_escape_penalty)
    return {
        'score': score,
        'total': total,
        'live_count': live_count,
        'pending': pending,
        'running': running,
        'timeouts': timeouts,
        'since_ack': since_ack,
        'historical': historical,
        'human_escape_triggered': bool(data.get('human_escape_triggered')),
        'penalties': {
            'live': round(live_penalty, 3),
            'timeouts': round(timeout_penalty, 3),
            'since_ack': round(since_ack_penalty, 3),
            'human_escape': round(human_escape_penalty, 3),
        },
        'policy': 'score penalizes live pending/running, timeouts, since-ack failures/blocks, and human_escape; historical terminal debt remains diagnostic',
    }


def f_envelope():
    """Envelope health based on live/since-ack risk, not historical terminal debt."""
    try:
        return envelope_diagnostics()['score']
    except:
        return 0.8

def f_cron():
    """1 - recent_error_crons / max(1, total_crons). Only count errors from last 48h."""
    try:
        out = safe_run(['hermes', 'cron', 'list'])
        total = out.count('[active]')
        if total == 0:
            return 1.0
        # Count only recent errors (from today/yesterday)
        import re
        today = time.strftime('%Y-%m-%d')
        yesterday = time.strftime('%Y-%m-%d', time.localtime(time.time() - 86400))
        recent_errors = 0
        lines = out.split('\n')
        for i, line in enumerate(lines):
            if 'error:' in line.lower():
                # Check if the error is from recent runs
                if today in line or yesterday in line:
                    recent_errors += 1
        return max(0, 1 - recent_errors / total)
    except:
        return 0.8

def get_kanban_coverage_report():
    """Return detailed Kanban coverage diagnostics, fail-soft."""
    if kanban_coverage_live_report is None:
        return None
    try:
        return kanban_coverage_live_report()
    except Exception:
        return None

def f_kanban():
    """Spawnability-aware Kanban coverage score.

    Old behavior measured only brain-mirror / dispatchable and returned 1.0
    when dispatchable == 0. That made an empty source queue look healthy even
    when Kanban ready work was nonspawnable. The detailed report separates
    projection coverage, provenance coverage, and ready-spawnability coverage.
    """
    report = get_kanban_coverage_report()
    if isinstance(report, dict) and isinstance(report.get('score'), (int, float)):
        return max(0.0, min(float(report['score']), 1.0))
    return 0.5

# Weights
WEIGHTS = {
    'orchestrator': 0.20,
    'dynamic_n': 0.10,
    'classifier': 0.10,
    'continuation': 0.15,
    'envelope': 0.15,
    'cron': 0.15,
    'kanban': 0.15,
}

FUNCTIONS = {
    'orchestrator': f_orchestrator,
    'dynamic_n': f_dynamic_n,
    'classifier': f_classifier,
    'continuation': f_continuation,
    'envelope': f_envelope,
    'cron': f_cron,
    'kanban': f_kanban,
}

def compute_v():
    components = {}
    for name, fn in FUNCTIONS.items():
        try:
            score = fn()
        except:
            score = 0.0
        components[name] = round(score, 3)
    
    v = sum(WEIGHTS[name] * components[name] for name in WEIGHTS)
    v = round(v, 3)
    
    if v >= 0.7:
        grade = 'HEALTHY'
    elif v >= 0.5:
        grade = 'DEGRADED'
    else:
        grade = 'CRITICAL'
    
    # Find bottleneck (lowest raw score, not weighted)
    bottleneck = min(components, key=components.get)
    
    weighted = {name: round(WEIGHTS[name] * components[name], 3) for name in WEIGHTS}
    
    return {
        'V': v,
        'grade': grade,
        'components': components,
        'weights': WEIGHTS,
        'weighted_scores': weighted,
        'bottleneck': bottleneck,
        'diagnostics': {
            'kanban_coverage': get_kanban_coverage_report(),
            'envelope': envelope_diagnostics(),
        },
        'timestamp': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
    }

def main():
    result = compute_v()
    
    if '--json' in sys.argv:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print(f"V(x) = {result['V']} [{result['grade']}]")
        print(f"Bottleneck: {result['bottleneck']}")
        for name in sorted(result['components']):
            w = result['weights'][name]
            s = result['components'][name]
            ws = result['weighted_scores'][name]
            bar = '█' * int(s * 10) + '░' * (10 - int(s * 10))
            print(f"  {name:15} {bar} {s:.2f} × {w:.2f} = {ws:.3f}")

if __name__ == '__main__':
    main()
