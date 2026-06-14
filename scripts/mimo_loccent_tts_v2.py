#!/usr/bin/env python3
import base64, json, os, urllib.request
from pathlib import Path

HOME=Path.home()
for line in (HOME/'.hermes/.env').read_text(errors='ignore').splitlines():
    line=line.strip()
    if line and not line.startswith('#') and '=' in line:
        k,v=line.split('=',1)
        os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))
api_key=os.environ.get('XIAOMI_API_KEY') or os.environ.get('MIMO_API_KEY')
base_url=os.environ.get('XIAOMI_BASE_URL') or 'https://api.xiaomimimo.com/v1'
if not api_key: raise SystemExit('missing XIAOMI_API_KEY/MIMO_API_KEY')
text=Path('/Users/charles/.hermes/audio_cache/hermes_boot_loccent_v2_script.txt').read_text(encoding='utf-8').strip()
out=Path('/Users/charles/.hermes/audio_cache')

cases=[
  {
    'name':'loccent_female_director',
    'model':'mimo-v2.5-tts-voicedesign',
    'messages':[
      {'role':'user','content':'成熟女性控制中心汇报员声线。冷静、专业、短促、稳定，像大型机甲出动前的指挥中心状态播报。全程标准中文，不要英文腔，不要播音主持腔，不要甜美，不要情绪表演。语速中等，句尾收束干净，状态词略带重音。'},
      {'role':'assistant','content':text}
    ],
    'audio':{'format':'wav','optimize_text_preview':False}
  },
  {
    'name':'loccent_system_ai',
    'model':'mimo-v2.5-tts-voicedesign',
    'messages':[
      {'role':'user','content':'中性偏女性的战术系统语音。声音克制、精准、低情绪波动，像机甲驾驶舱与指挥中心共用的状态提示。中文自然连贯，不要一个字一个字蹦，不要英文语调。语速略快，停顿短，专业但不机械。'},
      {'role':'assistant','content':text}
    ],
    'audio':{'format':'wav','optimize_text_preview':False}
  },
  {
    'name':'preset_bingtang_loccent',
    'model':'mimo-v2.5-tts',
    'messages':[
      {'role':'user','content':'冷静专业的中文控制中心汇报语气，语速中等，节奏短促，像大型机甲启动状态播报。不要英文腔，不要甜美，不要播音腔。'},
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
        p=out/f"hermes_boot_loccent_v2_{c['name']}.wav"
        p.write_bytes(audio)
        summary.append({'name':c['name'],'ok':True,'http':status,'path':str(p),'bytes':len(audio),'model':c['model']})
    except Exception as e:
        summary.append({'name':c['name'],'ok':False,'error':type(e).__name__+': '+str(e)[:300]})
print(json.dumps(summary,ensure_ascii=False,indent=2))
