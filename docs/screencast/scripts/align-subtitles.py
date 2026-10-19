import json,pathlib,re,unicodedata,difflib,textwrap
from common import R, S
scenes=json.loads((S/'narration.json').read_text());timeline=json.loads((R/'timeline.json').read_text())
def norm(s): return re.sub('[^a-z0-9]','',unicodedata.normalize('NFKD',s.lower()).encode('ascii','ignore').decode())
def stamp(t):
 ms=round(t*1000);h,ms=divmod(ms,3600000);m,ms=divmod(ms,60000);s,ms=divmod(ms,1000)
 return f'{h:02}:{m:02}:{s:02},{ms:03}'
for lang in ('es','en'):
 blocks=[];offset=0
 for scene,chapter in zip(scenes,timeline):
  qa=json.loads((R/f"audio/qa/{scene['id']}-{lang}.json").read_text())
  heard=[w for seg in qa['segments'] for w in seg.get('words',[])]
  words=scene[lang].split();starts={};ends={}
  for match in difflib.SequenceMatcher(None,[norm(w) for w in words],[norm(w['word']) for w in heard],autojunk=False).get_matching_blocks():
   for k in range(match.size):
    starts[match.a+k]=heard[match.b+k]['start'];ends[match.a+k]=heard[match.b+k]['end']
  for i in range(len(words)):
   if i not in starts:
    left=max((k for k in starts if k<i),default=-1);right=min((k for k in starts if k>i),default=len(words))
    a=ends.get(left,0);b=starts.get(right,heard[-1]['end']);step=max(0,b-a)/(right-left)
    starts[i]=a+step*(i-left-1);ends[i]=starts[i]+step
  for i in range(0,len(words),10):
   j=min(i+10,len(words))-1
   a=offset+1+starts[i];b=offset+1+ends[j]
   if b<=a:b=a+0.1
   blocks.append(f'{len(blocks)+1}\n{stamp(a)} --> {stamp(b)}\n'+textwrap.fill(' '.join(words[i:j+1]),56)+'\n')
  offset+=chapter['duration']
 (R/f'subtitles/{lang}.srt').write_text('\n'.join(blocks))
print('Subtitles aligned to locally transcribed speech.')
