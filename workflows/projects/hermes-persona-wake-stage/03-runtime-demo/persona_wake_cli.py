#!/usr/bin/env python3
from __future__ import annotations
import argparse, json
from pathlib import Path

CONTRACT = Path(__file__).with_name('runtime-contract.json')

def load():
    return json.loads(CONTRACT.read_text(encoding='utf-8'))

def main() -> int:
    p = argparse.ArgumentParser(description='Local-only Hermes persona wake runtime demo')
    p.add_argument('command', choices=['wake','mode','status','handoff-preview'])
    p.add_argument('--mode', default='control-room-c')
    p.add_argument('--json', action='store_true')
    args = p.parse_args()
    c = load()
    mode = next((m for m in c['modes'] if m['id'] == args.mode), c['modes'][0])
    result = {
        'ok': True,
        'surface': 'cli',
        'command': args.command,
        'mode': mode,
        'authority_model': c['authority_model'],
        'external_side_effects': [],
        'blocked_by_design': c['blocked_commands'],
        'message': f"{mode['label']} ready: local wake stage only; no voice/send/deploy/secret/destructive action."
    }
    if args.command == 'handoff-preview':
        result['handoff_preview'] = {
            'evidence_required': ['runtime readback', 'negative side-effect proof', 'surface screenshot if UI'],
            'next_gate': 'select concrete production surface before external behavior'
        }
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(result['message'])
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
