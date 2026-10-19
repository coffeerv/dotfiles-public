import os,pathlib,json,subprocess,urllib.request,urllib.error,base64,wave,sys,ssl
from common import R, S
project=os.environ.get('GOOGLE_CLOUD_PROJECT')
if not project: sys.exit('Set GOOGLE_CLOUD_PROJECT explicitly before generating billable audio.')
model=os.environ.get('TTS_MODEL','gemini-3.8-flash-tts')
voice=os.environ.get('TTS_VOICE','Kore')
styles={'es':'Narración técnica clara y cercana en español de México, acento mexicano discreto, ritmo tranquilo de 135 palabras por minuto. Sin música. Pronuncia mise como miz, chezmoi como she mua y fnox como ef nocks.', 'en':'Warm, clear technical tutorial narration in US English, calm pace around 135 words per minute. No music. Pronounce mise as meez, chezmoi as shay mwa, fnox as eff nocks.'}
token=subprocess.check_output(['gcloud','auth','print-access-token'],text=True).strip()
scenes=json.loads((S/'narration.json').read_text())
for scene in scenes:
 for lang in ('es','en'):
  out=R/f'audio/{scene["id"]}-{lang}.wav'
  if out.exists(): continue
  body={'contents':[{'role':'user','parts':[{'text':scene[lang],'speechMetadata':{'style':styles[lang]}}]}], 'generationConfig':{'responseModalities':['AUDIO'],'speechConfig':{'voiceConfig':{'voice':voice}}}}
  req=urllib.request.Request(f'https://aiplatform.googleapis.com/v1/projects/{project}/locations/global/publishers/google/models/{model}:generateContent',json.dumps(body).encode(),headers={'Authorization':'Bearer '+token,'Content-Type':'application/json'})
  try:
   with urllib.request.urlopen(req,timeout=180,context=ssl.create_default_context()) as response: result=json.load(response)
  except urllib.error.HTTPError as e:
   print(e.read().decode()[:2500]);sys.exit(1)
  parts=result.get('candidates',[{}])[0].get('content',{}).get('parts',[])
  raw=b''.join(base64.b64decode(p['inlineData']['data']) for p in parts if 'inlineData' in p)
  if not raw: sys.exit('No audio returned: '+str(result)[:1000])
  out.parent.mkdir(exist_ok=True,parents=True)
  if raw.startswith(b'RIFF'): out.write_bytes(raw)
  else:
   with wave.open(str(out),'wb') as w: w.setnchannels(1);w.setsampwidth(2);w.setframerate(24000);w.writeframes(raw)
  with wave.open(str(out)) as w: print(out.name,round(w.getnframes()/w.getframerate(),2),'seconds',flush=True)
  (R/'audio/voice-settings.json').write_text(json.dumps({'provider':'Vertex AI','project':project,'model':model,'voice':voice,'styles':styles},ensure_ascii=False,indent=2))
