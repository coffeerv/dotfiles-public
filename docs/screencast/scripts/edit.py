import os,json,pathlib,subprocess,textwrap,concurrent.futures
from PIL import Image,ImageDraw,ImageFont
from common import R, S
V=R/'video'; A=V/'assets'; A.mkdir(exist_ok=True,parents=True)
F=os.environ.get('SCREENCAST_FONT','/System/Library/Fonts/Helvetica.ttc' if pathlib.Path('/System/Library/Fonts/Helvetica.ttc').exists() else '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf')
M=os.environ.get('SCREENCAST_MONO_FONT','/System/Library/Fonts/Menlo.ttc' if pathlib.Path('/System/Library/Fonts/Menlo.ttc').exists() else '/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf')
(R/'subtitles').mkdir(parents=True,exist_ok=True)
def font(n,mono=False): return ImageFont.truetype(M if mono else F,n)
def text(d,xy,t,size=36,fill='#E5EDF5',mono=False): d.text(xy,t,font=font(size,mono),fill=fill)
def card(name,kicker,title,subtitle,rows,footer):
 im=Image.new('RGB',(1920,1080),'#0B1220');d=ImageDraw.Draw(im)
 d.rounded_rectangle((100,100,170,108),radius=4,fill='#4FD1C5')
 text(d,(100,145),kicker,28,'#4FD1C5'); text(d,(100,215),title,76)
 text(d,(100,320),subtitle,34,'#A7B6CB')
 y=440
 for heading,body in rows:
  d.rounded_rectangle((100,y,1820,y+120),radius=14,fill='#152239')
  text(d,(135,y+18),heading,34,'#E5EDF5',True);text(d,(135,y+69),body,27,'#A7B6CB')
  y+=145
 text(d,(100,990),footer,25,'#A7B6CB');im.save(A/(name+'.png'))
card('intro','DOTFILES / MULTI-IDENTITY','Una identidad por proyecto','The right Git identity for every project',[
 ('personal','alex@personal.example  ·  GitHub personal'),
 ('acme','alex@acme.example  ·  GitHub Acme  ·  AWS_PROFILE  ·  Node 24'),
 ('studio','alex@studio.example  ·  GitHub personal')], 'DEMO: Linux aislado / isolated Linux · Datos ficticios / fictional accounts')
card('start','01 / PREPARACIÓN · GETTING STARTED','De tu fork al wizard','Herramientas preinstaladas en esta demo / Tools preinstalled for this demo',[
 ('mise use -g chezmoi','Instala mise primero / Install mise first'),
 ('chezmoi init https://github.com/<user>/<fork>.git','Usa tu copia del repositorio / Use your copy of the repository'),
 ('cd "$(chezmoi source-path)" && mise trust','Después / Then: mise run setup -- --advanced')], 'Requisito real / Real prerequisite: gestor de contraseñas con agente SSH / password manager with SSH agent')
scenes=[
 {'id':'01-intro','title':'DOTFILES / MULTI-IDENTITY','duration':25,'card':'intro'},
 {'id':'02-start','title':'01  PREPARACIÓN / GETTING STARTED','duration':33,'parts':[{'card':'start','duration':18},{'start':0,'end':17,'duration':15}]},
 {'id':'03-personal','title':'02  IDENTIDAD PERSONAL / PERSONAL IDENTITY','duration':40,'parts':[{'start':17.8,'end':81,'duration':40}]},
 {'id':'04-organizations','title':'03  ORGANIZACIONES / ORGANIZATIONS','duration':80,'parts':[{'start':83,'end':154,'duration':53},{'start':322.8,'end':329.8,'duration':8},{'start':168.5,'end':185,'duration':14},{'start':350,'end':353,'duration':5}]},
 {'id':'05-keys','title':'04  LLAVES PÚBLICAS / PUBLIC KEYS','duration':32,'parts':[{'start':217.5,'end':242,'duration':32}]},
 {'id':'06-apply','title':'05  REVISAR Y APLICAR / REVIEW AND APPLY','duration':35,'parts':[{'start':366.5,'end':392,'duration':35}]},
 {'id':'07-verify','title':'06  VERIFICACIÓN / VERIFICATION','duration':50,'parts':[{'start':413.5,'end':461.5,'duration':50}]},
 {'id':'08-next','title':'07  PRÓXIMOS PASOS / NEXT STEPS','duration':35,'parts':[{'start':467.8,'end':475.5,'duration':35}]}
]
# Extend chapters if either narration needs more time; never truncate a voice track.
for scene in scenes:
 old=scene['duration'];dur=0;complete=all((R/f"audio/{scene['id']}-{lang}.wav").exists() for lang in ('es','en'))
 for lang in ('es','en'):
  audio=R/f"audio/{scene['id']}-{lang}.wav"
  if audio.exists():
   seconds=float(subprocess.check_output(['ffprobe','-v','error','-show_entries','format=duration','-of','csv=p=0',str(audio)]))
   dur=max(dur,seconds+3)
 if not complete: dur=max(old,dur)
 if dur!=old:
  for part in scene.get('parts',[]): part['duration']*=dur/old
  scene['duration']=dur
(R/'timeline.json').write_text(json.dumps(scenes,indent=2)+'\n')
def run(args): subprocess.run(['ffmpeg','-y','-v','error',*map(str,args)],check=True)
def encode_task(item):
 s,idx,p=item;out=V/f"part-{s['id']}-{idx}.mp4"; dur=p['duration']
 if 'card' in p:
  run(['-loop','1','-framerate','30','-i',A/(p['card']+'.png'),'-t',dur,'-c:v','libx264','-preset','veryfast','-crf','19','-pix_fmt','yuv420p',out])
 else:
  header=A/(s['id']+'-header.png')
  im=Image.new('RGB',(1920,64),'#0B1220');d=ImageDraw.Draw(im)
  text(d,(32,17),s['title'],25,'#4FD1C5');text(d,(1450,19),'Linux · demo aislada / isolated',22,'#A7B6CB');im.save(header)
  length=p['end']-p['start']; ratio=min(dur/length,1.5)
  filt=f'[0:v]setpts={ratio}*(PTS-STARTPTS),fps=30,scale=1808:1016,pad=1920:1080:56:64:color=0x101827,tpad=stop_mode=clone:stop_duration={dur}[v];[v][1:v]overlay=0:0,format=yuv420p[out]'
  run(['-ss',p['start'],'-t',length,'-i',V/'wizard-raw.mp4','-i',header,'-filter_complex',filt,'-map','[out]','-t',dur,'-an','-r','30','-c:v','libx264','-preset','veryfast','-crf','19',out])
 return out
jobs=[(s,n,p) for s in scenes for n,p in enumerate(s.get('parts',[{'card':s.get('card'),'duration':s['duration']}]))]
with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool: files=list(pool.map(encode_task,jobs))
(V/'concat.txt').write_text(''.join("file '"+str(p)+"'\n" for p in files))
run(['-f','concat','-safe','0','-i',V/'concat.txt','-c','copy','-movflags','+faststart',V/'picture-lock.mp4'])
# Reading subtitles: time allocated by word count within each chapter, to be realigned to TTS later.
ns=json.loads((S/'narration.json').read_text())
def stamp(t):
 ms=round(t*1000);h,ms=divmod(ms,3600000);m,ms=divmod(ms,60000);sec,ms=divmod(ms,1000)
 return f'{h:02}:{m:02}:{sec:02},{ms:03}'
for lang in ('es','en'):
 blocks=[];t=0;idx=1
 for s,n in zip(scenes,ns):
  narration=n[lang]
  if not (R/f"audio/{s['id']}-{lang}.wav").exists():
   narration=narration.replace(' La narración de este tutorial fue generada con inteligencia artificial.','').replace(" This tutorial's narration was generated with artificial intelligence.",'')
  speech_file=R/f"audio/{s['id']}-{lang}.wav"
  speech_duration=float(subprocess.check_output(['ffprobe','-v','error','-show_entries','format=duration','-of','csv=p=0',str(speech_file)])) if speech_file.exists() else s['duration']-2
  words=narration.split();chunks=[words[i:i+14] for i in range(0,len(words),14)];offset=1
  for chunk in chunks:
   dt=speech_duration*len(chunk)/len(words)
   blocks.append(f'{idx}\n{stamp(t+offset)} --> {stamp(t+offset+dt)}\n'+textwrap.fill(' '.join(chunk),width=56)+'\n')
   idx+=1;offset+=dt
  t+=s['duration']
 (R/f'subtitles/{lang}.srt').write_text('\n'.join(blocks))
run(['-i',V/'picture-lock.mp4','-i',R/'subtitles/es.srt','-i',R/'subtitles/en.srt','-map','0:v','-map','1:0','-map','2:0','-c:v','copy','-c:s','mov_text','-metadata:s:s:0','language=spa','-metadata:s:s:0','title=Español','-metadata:s:s:1','language=eng','-metadata:s:s:1','title=English','-movflags','+faststart',R/'dotfiles-preview-no-voice.mp4'])
print('Preview ready:',R/'dotfiles-preview-no-voice.mp4',flush=True)
