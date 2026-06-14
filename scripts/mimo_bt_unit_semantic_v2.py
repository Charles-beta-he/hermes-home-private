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
scripts=json.loads(Path('/Users/charles/.hermes/audio_cache/bt_unit_semantic_v2_scripts.json').read_text(encoding='utf-8'))
out=Path('/Users/charles/.hermes/audio_cache')
voice_prompt=(
  '低沉可靠的机体 AI 声线，中性偏男性，稳定、克制、带保护性，像重型机甲本体在回应驾驶员。'
  '必须根据语义调整节奏和语气：连接/上线类句子用短促确认；核心/通信正常用平稳低压；'
  '风险扫描完成和关键链路全绿略加强重音；最后对“指挥官”的呼叫放慢半拍，语气坚定但不煽情。'
  '不要喊叫，不要播音腔，不要英文腔；中文自然、短句、有停顿。'
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
        p=out/f'bt_unit_semantic_v2_{name}.wav'
        p.write_bytes(audio)
        summary.append({'name':name,'ok':True,'http':status,'path':str(p),'bytes':len(audio)})
    except Exception as e:
        summary.append({'name':name,'ok':False,'error':type(e).__name__+': '+str(e)[:300]})
print(json.dumps(summary,ensure_ascii=False,indent=2))
