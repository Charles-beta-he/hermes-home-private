#!/usr/bin/env python3
from __future__ import annotations
import json, subprocess, sys
from pathlib import Path

ROOT=Path(__file__).parent
contract=json.loads((ROOT/'runtime-contract.json').read_text(encoding='utf-8'))
assert contract['authority_model']['external_send_enabled'] is False
assert contract['authority_model']['voice_output_enabled'] is False
assert contract['authority_model']['credential_entry_enabled'] is False
assert contract['authority_model']['payment_enabled'] is False
assert contract['authority_model']['destructive_action_enabled'] is False
html=(ROOT/'persona-wake-local.html').read_text(encoding='utf-8').lower()
for token in ['no external send','no voice default','blocked']:
    assert token in html
out=subprocess.check_output([sys.executable, str(ROOT/'persona_wake_cli.py'), 'wake', '--json'], text=True)
data=json.loads(out)
assert data['ok'] is True
assert data['external_side_effects'] == []
assert data['authority_model']['external_send_enabled'] is False
print(json.dumps({'status':'PASS','checked':['contract-negative-authority','html-boundary-copy','cli-json-readback']}))
