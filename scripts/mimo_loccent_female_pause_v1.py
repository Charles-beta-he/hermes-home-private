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
text=Path('/Users/charles/.hermes/audio_cache/hermes_boot_loccent_female_pause_v1_script.txt').read_text(encoding='utf-8').strip()
payload={
  'model':'mimo-v2.5-tts-voicedesign',
  'messages':[
    {'role':'user','content':'成熟女性控制中心汇报员声线。冷静、专业、短促、稳定，像大型机甲出动前的指挥中心状态播报。全程标准中文，不要英文腔，不要播音主持腔，不要甜美，不要情绪表演。语速中等，句尾收束干净，状态词略带重音。通过停顿和坚定收束表达战前热血，不要喊叫。'},
    {'role':'assistant','content':text}
  ],
  'audio':{'format':'wav','optimize_text_preview':False}
}
url=base_url.rstrip()+'/chat/completions'
req=urllib.request.Request(url,data=json.dumps(payload,ensure_ascii=False).encode(),headers={'Content-Type':'application/json','Authorization':f'Bearer {api_key}','api-key':api_key},method='POST')
with urllib.request.urlopen(req,timeout=240) as r:
    raw=r.read(); status=r.status
obj=json.loads(raw)
audio=base64.b64decode(obj['choices'][0]['message']['audio']['data'])
out=Path('/Users/charles/.hermes/audio_cache/hermes_boot_loccent_female_pause_v1.wav')
out.write_bytes(audio)
print(json.dumps({'ok':True,'http':status,'path':str(out),'bytes':len(audio)},ensure_ascii=False,indent=2))
