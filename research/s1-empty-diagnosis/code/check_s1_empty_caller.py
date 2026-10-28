"""CPU reproduction of the suffixed-condition progress-counter failure."""
import io,json,tempfile
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
import numpy as np,soundfile as sf,torch
import s1_empty_speech_adapter as adapter
with tempfile.TemporaryDirectory() as temp:
 root=Path(temp);sf.write(root/'request.wav',np.ones(1600)*.01,16000,subtype='PCM_16')
 row={'id':'P01-native-original','question_id':'fixture','question':'Fixture request.','input_audio':'request.wav','input_sha256':adapter.pilot.sha(root/'request.wav'),'source_cutoff_seconds':0,'request_end_seconds':.1,'input_method':'CPU fixture, not a model run','progress_index':7}
 b=io.BytesIO();torch.save({'response':{'choices':[{'message':{'content':"{'tts_control': '', 'system2_control': '', 'asr': '', 'tts': 'Fixture.'}"},'finish_reason':'stop'}],'usage':{'completion_tokens':28}}},b)
 def response(content):return SimpleNamespace(content=content,raise_for_status=lambda:None)
 def post(url,**kwargs):return response(b.getvalue() if 'chat_turn' in url else b'')
 seen=[]
 with patch.dict('os.environ',{'SLURM_JOB_ID':'fixture'}),patch.object(adapter.pilot.torch.cuda,'get_device_name',return_value='CPU fixture'),patch.object(adapter.pilot.requests,'post',side_effect=post),patch.object(adapter.pilot.requests,'delete',return_value=response(b'')):
  fn=adapter.make_buffered_case(adapter.pilot.NATIVE,lambda phase,**kwargs:seen.append(kwargs))
  r=fn(root,root/'out',row,{'pilot_continuation_calls':0})
 assert r['status']=='completed',r
 assert r['complete_input'] and r['native_text']=='Fixture.'
 assert seen[0]['completed_pilot_cases']==7
 print(json.dumps({'status':'pass','gpus':0,'scope':'Suffixed diagnostic IDs complete the caller loop and update the explicit progress index; all HTTP/model output is a labeled script fixture.'}))
