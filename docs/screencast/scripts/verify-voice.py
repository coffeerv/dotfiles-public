import os,sys,pathlib,json,mlx_whisper,difflib,re,unicodedata
from common import R, S
scenes=json.loads((S/'narration.json').read_text())
Q=R/'audio/qa';Q.mkdir(exist_ok=True,parents=True)
def norm(s):
 return re.sub(r'[^a-z0-9 ]','',unicodedata.normalize('NFKD',s.lower()).encode('ascii','ignore').decode()).split()
for s in scenes:
 for lang in ('es','en'):
  f=R/f"audio/{s['id']}-{lang}.wav";out=Q/(f.stem+'.json')
  if not f.exists(): sys.exit(f'Missing narration: {f}. Run generate-vertex.py first.')
  if out.exists(): continue
  result=mlx_whisper.transcribe(str(f),path_or_hf_repo=os.environ.get('WHISPER_MODEL','mlx-community/whisper-large-v3-turbo'),language=lang,word_timestamps=True,temperature=0)
  out.write_text(json.dumps(result,ensure_ascii=False,indent=2))
  score=difflib.SequenceMatcher(None,norm(s[lang]),norm(result['text'])).ratio()
  print(f.stem,round(score,3),result['text'],flush=True)
