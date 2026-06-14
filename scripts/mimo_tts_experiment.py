#!/usr/bin/env python3
import base64
import json
import os
import sys
import urllib.request
from pathlib import Path

HOME = Path.home()
# Minimal .env loader without printing secrets.
for line in (HOME / '.hermes/.env').read_text(errors='ignore').splitlines():
    line = line.strip()
    if not line or line.startswith('#') or '=' not in line:
        continue
    k, v = line.split('=', 1)
    os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))

base_url = os.environ.get('XIAOMI_BASE_URL') or 'https://api.xiaomimimo.com/v1'
api_key = os.environ.get('XIAOMI_API_KEY') or os.environ.get('MIMO_API_KEY')
if not api_key:
    raise SystemExit('missing XIAOMI_API_KEY/MIMO_API_KEY')

script_path = Path('/Users/charles/.hermes/audio_cache/hermes_boot_mimo_v1_script.txt')
text = script_path.read_text(encoding='utf-8').strip()
out_dir = Path('/Users/charles/.hermes/audio_cache')

cases = [
    {
        'name': 'preset_baihua_commander',
        'model': 'mimo-v2.5-tts',
        'messages': [
            {
                'role': 'user',
                'content': '用低沉、冷静、专业可靠的中文男声播报。整体像科幻机甲的启动战备自检，但不要夸张，不要逐字机械朗读；语速中慢，停顿自然，英文技术术语清晰，关键状态词有轻微重音。'
            },
            {'role': 'assistant', 'content': text},
        ],
        'audio': {'format': 'wav', 'voice': '白桦'},
    },
    {
        'name': 'preset_soda_tactical',
        'model': 'mimo-v2.5-tts',
        'messages': [
            {
                'role': 'user',
                'content': '冷静、干练、带战术通信感的中文男声。像驾驶舱 AI 在汇报系统上线，不要戏剧腔，不要播音腔；语速中等偏慢，短句之间留出自然间隔。'
            },
            {'role': 'assistant', 'content': text},
        ],
        'audio': {'format': 'wav', 'voice': '苏打'},
    },
    {
        'name': 'voicedesign_mecha_operator',
        'model': 'mimo-v2.5-tts-voicedesign',
        'messages': [
            {
                'role': 'user',
                'content': '三十多岁的中文男性系统 Operator 声线，低沉、磁性、克制、专业，像近未来重型机甲驾驶舱里的任务控制 AI。语速中慢，咬字清晰但自然，英文技术术语发音稳定；有战备感和压迫感，但不要像机器人逐字朗读，不要夸张表演。'
            },
            {'role': 'assistant', 'content': text},
        ],
        'audio': {'format': 'wav', 'optimize_text_preview': False},
    },
]

url = base_url.rstrip('/') + '/chat/completions'
summary = []
for case in cases:
    payload = {'model': case['model'], 'messages': case['messages'], 'audio': case['audio']}
    data = json.dumps(payload, ensure_ascii=False).encode('utf-8')
    req = urllib.request.Request(
        url,
        data=data,
        headers={
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {api_key}',
            'api-key': api_key,
        },
        method='POST',
    )
    try:
        with urllib.request.urlopen(req, timeout=180) as resp:
            raw = resp.read()
            status = resp.status
    except Exception as e:
        summary.append({'name': case['name'], 'ok': False, 'error': type(e).__name__ + ': ' + str(e)[:300]})
        continue
    try:
        obj = json.loads(raw)
        audio_data = obj['choices'][0]['message']['audio']['data']
        audio_bytes = base64.b64decode(audio_data)
        wav_path = out_dir / f"hermes_boot_mimo_v1_{case['name']}.wav"
        wav_path.write_bytes(audio_bytes)
        summary.append({'name': case['name'], 'ok': True, 'http': status, 'path': str(wav_path), 'bytes': len(audio_bytes), 'model': case['model']})
    except Exception as e:
        err_path = out_dir / f"hermes_boot_mimo_v1_{case['name']}_response.json"
        err_path.write_bytes(raw)
        summary.append({'name': case['name'], 'ok': False, 'http': status, 'error': type(e).__name__ + ': ' + str(e)[:300], 'response_path': str(err_path), 'raw_prefix': raw[:300].decode('utf-8','ignore')})

print(json.dumps(summary, ensure_ascii=False, indent=2))
