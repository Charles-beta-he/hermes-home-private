#!/usr/bin/env python3
import base64, json, os, urllib.request
from pathlib import Path
HOME=Path.home()
for line in (HOME/'.hermes/.env').read_text(errors='ignore').splitlines():
    line=line.strip()
    if line and not line.startswith('#') and '=' in line:
        k,v=line.split('=',1); os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))
api_key=os.environ.get('XIAOMI_API_KEY') or os.environ.get('MIMO_API_KEY')
base_url=os.environ.get('XIAOMI_BASE_URL') or 'https://api.xiaomimimo.com/v1'
if not api_key: raise SystemExit('missing key')
scripts=json.loads(Path('/Users/charles/.hermes/audio_cache/hermes_notification_bt_scripts.json').read_text(encoding='utf-8'))
out=Path('/Users/charles/.hermes/audio_cache')
voice_prompt=(
  '低沉可靠的机体 AI 声线，中性偏男性，稳定、克制、带保护性，像重型机甲本体在回应驾驶员。'
  '这是短通知音，不要拖长，不要播音腔。根据语义调整节奏：称呼“指挥官”放慢半拍；确认状态短促；'
  '最后“待命/稳定/完成”坚定收束。全程标准中文，不要英文腔。'
)
summary=[]
url=base_url.rstrip()+'/chat/completions'
for name,text in scripts.items():
    payload={
      'model':'mimo-v2.5-tts-voicedesign',
      'messages':[{'role':'user','content':voice_prompt},{'role':'assistant','content':text}],
      'audio':{'format':'wav','optimize_text_preview':False}
    }
    req=urllib.request.Request(url,data=json.dumps(payload,ensure_ascii=False).encode(),headers={'Content-Type':'application/json','Authorization':f'Bearer {api_key}','api-key':api_key},method='POST')
    try:
        with urllib.request.urlopen(req,timeout=240) as r:
            raw=r.read(); status=r.status
        obj=json.loads(raw)
        audio=base64.b64decode(obj['choices'][0]['message']['audio']['data'])
        p=out/f'{name}.wav'
        p.write_bytes(audio)
        summary.append({'name':name,'ok':True,'http':status,'path':str(p),'bytes':len(audio)})
    except Exception as e:
        summary.append({'name':name,'ok':False,'error':type(e).__name__+': '+str(e)[:300]})
print(json.dumps(summary,ensure_ascii=False,indent=2))
