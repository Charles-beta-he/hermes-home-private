#!/usr/bin/env python3
from pathlib import Path
import wave, struct, math, random
try:
    from PIL import Image, ImageDraw, ImageFont, ImageFilter
except Exception as e:
    raise SystemExit('Pillow is required: '+str(e))

wav_path=Path('/Users/charles/.hermes/audio_cache/hermes_notification_bt_ready_unit_ready_norm-16lufs.wav')
out_dir=Path('/Users/charles/.hermes/audio_cache')
png_path=out_dir/'hermes_bt_unit_ready_desktop_waveform_3840x2160.png'
svg_path=out_dir/'hermes_bt_unit_ready_desktop_waveform.svg'

with wave.open(str(wav_path),'rb') as w:
    n=w.getnframes(); rate=w.getframerate(); ch=w.getnchannels(); sw=w.getsampwidth(); raw=w.readframes(n)
if sw!=2:
    raise SystemExit('expected 16-bit PCM')
vals=struct.unpack('<'+'h'*(len(raw)//2), raw)
if ch>1:
    vals=[sum(vals[i:i+ch])/ch for i in range(0,len(vals),ch)]
else:
    vals=list(vals)
mx=max(1,max(abs(x) for x in vals))
samples=[x/mx for x in vals]

W,H=3840,2160
bg=(5,9,14)
img=Image.new('RGB',(W,H),bg)
# subtle grid
layer=Image.new('RGBA',(W,H),(0,0,0,0)); d=ImageDraw.Draw(layer)
for x in range(0,W,120): d.line((x,0,x,H),fill=(28,75,92,28),width=1)
for y in range(0,H,120): d.line((0,y,W,y),fill=(28,75,92,22),width=1)
for x in range(0,W,480): d.line((x,0,x,H),fill=(28,119,151,34),width=1)
for y in range(0,H,480): d.line((0,y,W,y),fill=(28,119,151,28),width=1)
img=Image.alpha_composite(img.convert('RGBA'),layer)

# waveform data window
left,right=360,W-360
mid=H//2+40
amp=430
N=right-left
step=max(1,len(samples)//N)
peaks=[]
for i in range(N):
    seg=samples[i*step:(i+1)*step]
    if not seg: seg=[0]
    # RMS + peak hybrid for visual density
    rms=math.sqrt(sum(x*x for x in seg)/len(seg))
    pk=max(abs(x) for x in seg)
    val=0.38*rms+0.62*pk
    peaks.append(val)
# smooth
for _ in range(3):
    peaks=[(peaks[max(0,i-1)]+peaks[i]+peaks[min(len(peaks)-1,i+1)])/3 for i in range(len(peaks))]

# glow layers
for blur,width,alpha,color in [(26,10,80,(0,209,255)),(12,6,120,(72,255,220)),(4,3,210,(156,247,255))]:
    l=Image.new('RGBA',(W,H),(0,0,0,0)); dl=ImageDraw.Draw(l)
    pts_top=[]; pts_bot=[]
    for i,p in enumerate(peaks):
        x=left+i
        # slight command-center asymmetry
        mod=1+0.08*math.sin(i/34.0)+0.04*math.sin(i/9.0)
        y=amp*p*mod
        pts_top.append((x, mid-y))
        pts_bot.append((x, mid+y*0.86))
    dl.line(pts_top,fill=color+(alpha,),width=width,joint='curve')
    dl.line(pts_bot,fill=color+(int(alpha*0.72),),width=max(1,width-1),joint='curve')
    l=l.filter(ImageFilter.GaussianBlur(blur)) if blur>4 else l
    img=Image.alpha_composite(img,l)

# center crisp line, ticks, pulse dots
l=Image.new('RGBA',(W,H),(0,0,0,0)); d=ImageDraw.Draw(l)
d.line((left,mid,right,mid),fill=(40,220,255,105),width=2)
for i,p in enumerate(peaks[::48]):
    x=left+i*48
    y=amp*p
    d.line((x,mid-y,x,mid+y*0.86),fill=(99,242,255,80),width=2)
for i in range(16):
    x=left+int((right-left)*(i+0.5)/16)
    r=3+(i%4)
    d.ellipse((x-r,mid-r,x+r,mid+r),fill=(171,255,240,180))
img=Image.alpha_composite(img,l)

# typography
try:
    font_big=ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial Bold.ttf',88)
    font_mid=ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf',36)
    font_small=ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf',28)
    font_cn_mid=ImageFont.truetype('/System/Library/Fonts/Hiragino Sans GB.ttc',42)
except:
    try:
        font_big=ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial Unicode.ttf',88)
        font_mid=ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial Unicode.ttf',36)
        font_small=ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial Unicode.ttf',28)
        font_cn_mid=ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial Unicode.ttf',42)
    except:
        font_big=font_mid=font_small=font_cn_mid=ImageFont.load_default()
d=ImageDraw.Draw(img)
d.text((360,260),'HERMES',font=font_big,fill=(185,248,255,235))
d.text((365,360),'BT UNIT READY // TASK LINK ESTABLISHED',font=font_mid,fill=(88,210,230,190))
d.text((360,H-330),'指挥官，任务已接入。赫尔墨斯待命。',font=font_cn_mid,fill=(198,255,242,220))
d.text((360,H-270),'Notification Identity  ·  -16 LUFS  ·  3.6s  ·  24kHz mono',font=font_small,fill=(96,158,174,180))
# corner HUD
d.rectangle((W-760,250,W-360,420),outline=(80,220,240,100),width=2)
d.text((W-720,285),'LINK: STABLE',font=font_mid,fill=(158,255,230,220))
d.text((W-720,340),'MODE: STANDBY',font=font_mid,fill=(158,255,230,220))

img.convert('RGB').save(png_path,quality=95)

# simple SVG path version
pts=[]
for i,p in enumerate(peaks[::3]):
    x=360+i*3
    y=1080-430*p
    pts.append(f'{x:.1f},{y:.1f}')
svg=f'''<svg xmlns="http://www.w3.org/2000/svg" width="3840" height="2160" viewBox="0 0 3840 2160">
<rect width="3840" height="2160" fill="#05090e"/>
<text x="360" y="340" font-family="Arial" font-size="92" font-weight="700" fill="#b9f8ff">HERMES</text>
<text x="365" y="410" font-family="Arial" font-size="38" fill="#58d2e6">BT UNIT READY // TASK LINK ESTABLISHED</text>
<polyline points="{' '.join(pts)}" fill="none" stroke="#9cf7ff" stroke-width="4" stroke-linecap="round" stroke-linejoin="round"/>
<line x1="360" y1="1080" x2="3480" y2="1080" stroke="#28dcff" stroke-opacity="0.45" stroke-width="2"/>
<text x="360" y="1860" font-family="Arial" font-size="42" fill="#c6fff2">指挥官，任务已接入。赫尔墨斯待命。</text>
</svg>'''
svg_path.write_text(svg,encoding='utf-8')
print({'png':str(png_path),'svg':str(svg_path),'audio':str(wav_path),'duration_sec':round(len(samples)/rate,3)})
