#!/usr/bin/env python3
import base64, json, os, urllib.request
from pathlib import Path

HOME = Path.home()
for line in (HOME / '.hermes/.env').read_text(errors='ignore').splitlines():
    line=line.strip()
    if line and not line.startswith('#') and '=' in line:
        k,v=line.split('=',1)
        os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))
api_key=os.environ.get('XIAOMI_API_KEY') or os.environ.get('MIMO_API_KEY')
base_url=os.environ.get('XIAOMI_BASE_URL') or 'https://api.xiaomimimo.com/v1'
if not api_key: raise SystemExit('missing XIAOMI_API_KEY/MIMO_API_KEY')
text=Path('/Users/charles/.hermes/audio_cache/hermes_boot_pacificrim_v1_script.txt').read_text(encoding='utf-8').strip()
out=Path('/Users/charles/.hermes/audio_cache')

# NOTE: high-level cinematic cockpit AI direction only; no request to clone any actor or exact IP voice.
cases=[
  {
    'name':'jaeger_ai_voicedesign',
    'model':'mimo-v2.5-tts-voicedesign',
    'messages':[
      {'role':'user','content':'女性化但不过分拟人的大型机甲 cockpit AI 声线。冷静、精密、无情绪波动，像 Jaeger 启动时的系统 A.I. 汇报。声音干净、稍低、带轻微电子质感；语速中慢，停顿短促，状态词如 online、locked、nominal、green 要清晰。不要可爱，不要播音腔，不要逐字机械蹦字，不要模仿任何具体演员或现成角色，只取“好莱坞重型机甲驾驶舱系统汇报”的抽象质感。'},
      {'role':'assistant','content':text}
    ],
    'audio':{'format':'wav','optimize_text_preview':False}
  },
  {
    'name':'loccent_operator_voicedesign',
    'model':'mimo-v2.5-tts-voicedesign',
    'messages':[
      {'role':'user','content':'成熟女性 Mission Control / LOCCENT Operator 声线，冷静、专业、低压、战术指挥感。像大型机甲出动前的控制中心状态播报：不是情绪表演，而是精准、克制、带轻微压迫感的系统汇报。英文技术术语发音稳定，中文自然连贯，语速中等偏慢。'},
      {'role':'assistant','content':text}
    ],
    'audio':{'format':'wav','optimize_text_preview':False}
  },
  {
    'name':'preset_bingtang_system_ai',
    'model':'mimo-v2.5-tts',
    'messages':[
      {'role':'user','content':'用冷静、克制、偏科幻系统 A.I. 的中文女性声线朗读。像重型机甲驾驶舱状态汇报，语速中慢，停顿短促，英文技术词清晰；不要活泼，不要甜美，不要播音腔。'},
      {'role':'assistant','content':text}
    ],
    'audio':{'format':'wav','voice':'冰糖'}
  }
]
url=base_url.rstrip()+'/chat/completions'
summary=[]
for c in cases:
  payload={'model':c['model'],'messages':c['messages'],'audio':c['audio']}
  req=urllib.request.Request(url,data=json.dumps(payload,ensure_ascii=False).encode(),headers={'Content-Type':'application/json','Authorization':f'Bearer {api_key}','api-key':api_key},method='POST')
  try:
    with urllib.request.urlopen(req,timeout=240) as r:
      raw=r.read(); status=r.status
    obj=json.loads(raw)
    audio=base64.b64decode(obj['choices'][0]['message']['audio']['data'])
    p=out/f"hermes_boot_pacificrim_v1_{c['name']}.wav"
    p.write_bytes(audio)
    summary.append({'name':c['name'],'ok':True,'http':status,'path':str(p),'bytes':len(audio),'model':c['model']})
  except Exception as e:
    summary.append({'name':c['name'],'ok':False,'error':type(e).__name__+': '+str(e)[:300]})
print(json.dumps(summary,ensure_ascii=False,indent=2))
