#!/usr/bin/env python3
import json,pathlib,subprocess,sys
from common import R, S
scenes=json.loads((S/'narration.json').read_text())
missing=[f"{s['id']}-{lang}.wav" for s in scenes for lang in ('es','en') if not (R/f"audio/{s['id']}-{lang}.wav").exists()]
if missing: sys.exit('Missing narration: '+', '.join(missing)+'. Run generate-vertex.py after configuring gcloud access.')
subprocess.run([sys.executable,str(S/'edit.py')],check=True)
subprocess.run([sys.executable,str(S/'align-subtitles.py')],check=True)
timeline=json.loads((R/'timeline.json').read_text())
def run(args): subprocess.run(['ffmpeg','-y','-v','error',*map(str,args)],check=True)
for lang in ('es','en'):
 parts=[]
 for s in timeline:
  f=R/f"audio/aligned-{s['id']}-{lang}.wav"
  run(['-i',R/f"audio/{s['id']}-{lang}.wav",'-af','adelay=1000:all=1,apad','-t',s['duration'],'-ar','48000','-ac','1','-c:a','pcm_s16le',f]);parts.append(f)
 concat=R/f'audio/concat-{lang}.txt';concat.write_text(''.join("file '"+str(p)+"'\n" for p in parts))
 run(['-f','concat','-safe','0','-i',concat,'-af','loudnorm=I=-16:TP=-1.5:LRA=11','-ar','48000','-c:a','aac','-b:a','192k',R/f'audio/narration-{lang}.m4a'])
run(['-i',R/'video/picture-lock.mp4','-i',R/'audio/narration-es.m4a','-i',R/'audio/narration-en.m4a','-i',R/'subtitles/es.srt','-i',R/'subtitles/en.srt','-map','0:v','-map','1:a','-map','2:a','-map','3:0','-map','4:0','-c:v','copy','-c:a','copy','-c:s','mov_text','-metadata:s:a:0','language=spa','-metadata:s:a:0','title=Español (México)','-metadata:s:a:1','language=eng','-metadata:s:a:1','title=English (US)','-metadata:s:s:0','language=spa','-metadata:s:s:1','language=eng','-disposition:a:0','default','-disposition:a:1','0','-movflags','+faststart',R/'dotfiles-bilingual.mp4'])
for n,lang in enumerate(('es','en')):
 run(['-i',R/'dotfiles-bilingual.mp4','-map','0:v','-map',f'0:a:{n}','-map',f'0:s:{n}','-c','copy','-movflags','+faststart',R/f'dotfiles-{lang}.mp4'])
print('Bilingual and single-language versions ready.')
