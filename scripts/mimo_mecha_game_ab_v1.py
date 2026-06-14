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
if not api_key: raise SystemExit('missing XIAOMI_API_KEY/MIMO_API_KEY')
scripts=json.loads(Path('/Users/charles/.hermes/audio_cache/mecha_game_ab_v1_scripts.json').read_text(encoding='utf-8'))
out=Path('/Users/charles/.hermes/audio_cache')

cases={
 'loccent_betty_ok': {
   'model':'mimo-v2.5-tts-voicedesign',
   'voice_prompt':'成熟女性控制中心汇报员声线，融合军用驾驶舱告警电脑的短促节奏。冷静、专业、稳定，状态词清晰有重音；通过停顿表达出击前的热血和压迫感，不喊叫，不甜美，不播音腔。全程标准中文。'
 },
 'ada_clean_ok': {
   'model':'mimo-v2.5-tts-voicedesign',
   'voice_prompt':'干净、冷静、清晰的日式科幻机体 AI 女性声线。专业但不冰冷，语速中等，短句自然，像机体内部系统上线汇报。不要英文腔，不要播音腔，不要过度机械。'
 },
 'bt_unit_ready': {
   'model':'mimo-v2.5-tts-voicedesign',
   'voice_prompt':'低沉可靠的机体 AI 声线，中性偏男性，稳定、克制、带保护性，像重型机甲本体在回应驾驶员。短句确认任务状态，不夸张，不热血喊叫。全程标准中文。'
 },
 'ac_warning_fail': {
   'model':'mimo-v2.5-tts-voicedesign',
   'voice_prompt':'冷峻的战斗系统警告声线，女性或中性皆可。短促、硬、压迫感强，像高速机甲战斗 HUD 告警。不要情绪表演，不要喊叫，保持清晰可读。'
 }
}
url=base_url.rstrip()+'/chat/completions'
summary=[]
for name,cfg in cases.items():
    payload={
      'model':cfg['model'],
      'messages':[{'role':'user','content':cfg['voice_prompt']},{'role':'assistant','content':scripts[name]}],
      'audio':{'format':'wav','optimize_text_preview':False}
    }
    req=urllib.request.Request(url,data=json.dumps(payload,ensure_ascii=False).encode(),headers={'Content-Type':'application/json','Authorization':f'Bearer {api_key}','api-key':api_key},method='POST')
    try:
        with urllib.request.urlopen(req,timeout=240) as r:
            raw=r.read(); status=r.status
        obj=json.loads(raw)
        audio=base64.b64decode(obj['choices'][0]['message']['audio']['data'])
        p=out/f'mecha_game_ab_v1_{name}.wav'
        p.write_bytes(audio)
        summary.append({'name':name,'ok':True,'http':status,'path':str(p),'bytes':len(audio)})
    except Exception as e:
        summary.append({'name':name,'ok':False,'error':type(e).__name__+': '+str(e)[:300]})
print(json.dumps(summary,ensure_ascii=False,indent=2))
