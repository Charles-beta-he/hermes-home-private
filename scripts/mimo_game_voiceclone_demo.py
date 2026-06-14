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
ref=Path('/Users/charles/.hermes/audio_cache/game_clone_demo_reference_ac_warning_style.wav')
text=Path('/Users/charles/.hermes/audio_cache/game_clone_demo_target_script.txt').read_text(encoding='utf-8').strip()
ref_b64=base64.b64encode(ref.read_bytes()).decode('ascii')
payload={
  'model':'mimo-v2.5-tts-voiceclone',
  'messages':[
    {'role':'user','content':'保持参考音频的战斗系统警告质感，但目标文本要清晰可懂。语速短促，状态播报坚定，不要喊叫。'},
    {'role':'assistant','content':text}
  ],
  'audio':{'format':'wav','voice':'data:audio/wav;base64,'+ref_b64}
}
req=urllib.request.Request(base_url.rstrip()+'/chat/completions',data=json.dumps(payload,ensure_ascii=False).encode(),headers={'Content-Type':'application/json','Authorization':f'Bearer {api_key}','api-key':api_key},method='POST')
with urllib.request.urlopen(req,timeout=300) as r:
    raw=r.read(); status=r.status
obj=json.loads(raw)
audio=base64.b64decode(obj['choices'][0]['message']['audio']['data'])
out=Path('/Users/charles/.hermes/audio_cache/game_clone_demo_ac_warning_voiceclone.wav')
out.write_bytes(audio)
print(json.dumps({'ok':True,'http':status,'reference':str(ref),'target_script':'/Users/charles/.hermes/audio_cache/game_clone_demo_target_script.txt','path':str(out),'bytes':len(audio)},ensure_ascii=False,indent=2))
