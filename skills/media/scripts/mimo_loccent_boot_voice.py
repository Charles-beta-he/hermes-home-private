#!/usr/bin/env python3
"""Generate a short LOCCENT-style Hermes boot voice with MiMo TTS.

Usage:
  python scripts/mimo_loccent_boot_voice.py \
    --script /path/script.txt --out-prefix /tmp/hermes_boot --voice 冰糖

Requires XIAOMI_API_KEY or MIMO_API_KEY and XIAOMI_BASE_URL/MIMO base URL if not default.
"""
import argparse, base64, json, os, urllib.request
from pathlib import Path


def load_dotenv(path: Path):
    if not path.exists():
        return
    for line in path.read_text(errors='ignore').splitlines():
        line=line.strip()
        if line and not line.startswith('#') and '=' in line:
            k,v=line.split('=',1)
            os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--script', required=True)
    ap.add_argument('--out-prefix', required=True)
    ap.add_argument('--voice', default='冰糖')
    ap.add_argument('--model', default='mimo-v2.5-tts')
    ap.add_argument('--style', default='冷静专业的中文控制中心汇报语气，带一点战前热血和坚定感。不要喊叫，不要夸张；通过停顿、重音和句尾上扬表达“启动完成、即将出击”的气势。语速中等，节奏短促，像大型机甲启动状态播报。')
    args=ap.parse_args()

    load_dotenv(Path.home()/'.hermes/.env')
    key=os.environ.get('XIAOMI_API_KEY') or os.environ.get('MIMO_API_KEY')
    if not key:
        raise SystemExit('missing XIAOMI_API_KEY/MIMO_API_KEY')
    base=os.environ.get('XIAOMI_BASE_URL') or 'https://api.xiaomimimo.com/v1'
    text=Path(args.script).read_text(encoding='utf-8').strip()
    payload={
        'model': args.model,
        'messages': [{'role':'user','content':args.style}, {'role':'assistant','content':text}],
        'audio': {'format':'wav','voice':args.voice},
    }
    req=urllib.request.Request(
        base.rstrip()+'/chat/completions',
        data=json.dumps(payload,ensure_ascii=False).encode(),
        headers={'Content-Type':'application/json','Authorization':f'Bearer {key}','api-key':key},
        method='POST',
    )
    with urllib.request.urlopen(req, timeout=240) as r:
        raw=r.read()
    obj=json.loads(raw)
    audio=base64.b64decode(obj['choices'][0]['message']['audio']['data'])
    out=Path(args.out_prefix).with_suffix('.wav')
    out.write_bytes(audio)
    print(json.dumps({'ok': True, 'path': str(out), 'bytes': len(audio), 'model': args.model, 'voice': args.voice}, ensure_ascii=False))

if __name__ == '__main__':
    main()
