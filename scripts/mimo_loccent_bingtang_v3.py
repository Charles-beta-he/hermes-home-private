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
out=Path('/Users/charles/.hermes/audio_cache')
base='/Users/charles/.hermes/audio_cache/hermes_boot_loccent_bingtang_v3'
texts={
 'pause_tags': Path(base+'_script.txt').read_text(encoding='utf-8').strip(),
 'ellipsis': Path(base+'_script_ellipsis.txt').read_text(encoding='utf-8').strip(),
}
style='冷静专业的中文控制中心汇报语气，带一点战前热血和坚定感。不要喊叫，不要夸张；通过停顿、重音和句尾上扬表达“启动完成、即将出击”的气势。语速中等，节奏短促，像大型机甲启动状态播报。'
summary=[]
url=base_url.rstrip()+'/chat/completions'
for name,text in texts.items():
    payload={'model':'mimo-v2.5-tts','messages':[{'role':'user','content':style},{'role':'assistant','content':text}], 'audio':{'format':'wav','voice':'冰糖'}}
    req=urllib.request.Request(url,data=json.dumps(payload,ensure_ascii=False).encode(),headers={'Content-Type':'application/json','Authorization':f'Bearer {api_key}','api-key':api_key},method='POST')
    try:
        with urllib.request.urlopen(req,timeout=240) as r: raw=r.read(); status=r.status
        obj=json.loads(raw); audio=base64.b64decode(obj['choices'][0]['message']['audio']['data'])
        p=out/f'hermes_boot_loccent_bingtang_v3_{name}.wav'; p.write_bytes(audio)
        summary.append({'name':name,'ok':True,'http':status,'path':str(p),'bytes':len(audio)})
    except Exception as e: summary.append({'name':name,'ok':False,'error':type(e).__name__+': '+str(e)[:300]})
print(json.dumps(summary,ensure_ascii=False,indent=2))
