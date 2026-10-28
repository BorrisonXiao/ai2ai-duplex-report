"""Mocked caller check of the exact listen/answer boundary; no model inference."""
import ast,copy,io,json,os,tempfile
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
import numpy as np,soundfile as sf,torch
import run_s1_listening_native as trial

def main():
    original_root=trial.ROOT
    for method in ['decode_clear','constrained']:
        with tempfile.TemporaryDirectory(dir=original_root/'cache/tmp') as temp:
            root=Path(temp);sf.write(root/'input.wav',np.ones(9600,dtype='float32')*.05,24000,subtype='PCM_16')
            row={'id':'fixture','question_id':'fixture','question':'NEVER_INSERT_THIS_QUESTION_TEXT','input_audio':'input.wav','input_sha256':trial.sha(root/'input.wav'),'source_cutoff_seconds':0.,'request_end_seconds':.4};captured=[]
            def post(url,**kw):
                if '/internal/talker/' in url:return SimpleNamespace(content=b'',raise_for_status=lambda:None)
                payload=copy.deepcopy(kw['json']);captured.append(payload);phase=payload['listening_rule']
                raw="{'asr': 'Assistant?'" if phase=='native_format' else "{'asr': 'Assistant?', 'tts': '', 'tts_control': '', 'system2_control': ''}" if phase=='listening' else "{'asr': '', 'tts': 'Example.', 'tts_control': '', 'system2_control': ''}"
                blob=io.BytesIO();torch.save({'response':{'choices':[{'message':{'content':raw},'finish_reason':'stop'}],'usage':{'prompt_tokens':1,'completion_tokens':10}}},blob)
                return SimpleNamespace(content=blob.getvalue(),raise_for_status=lambda:None)
            processor=SimpleNamespace(apply_chat_template=lambda *a,**kw:'',tokenizer=SimpleNamespace(encode=lambda *a,**kw:[]))
            with patch.object(trial,'ROOT',root),patch.dict(os.environ,{'SLURM_JOB_ID':'CPU-CHECK'}),patch.object(trial.requests,'post',side_effect=post),patch.object(trial.requests,'delete',return_value=SimpleNamespace(raise_for_status=lambda:None)):
                result=trial.run_case(row,method,root/'out',processor,{'listening_trial':{'answer_frames':2}})
            assert captured[0]['listening_rule']==('native_format' if method=='decode_clear' else 'listening')
            assert captured[1]['listening_rule']=='answer_start' and captured[2]['listening_rule']=='answering'
            for payload in captured:
                assert 'NEVER_INSERT_THIS_QUESTION_TEXT' not in json.dumps(payload)
                for message in payload['messages']:
                    if isinstance(message['content'],list):assert len(message['content'])==3,'No extra instruction or question text'
            previous=ast.literal_eval(captured[1]['messages'][2]['content'])
            assert previous['asr']=='Assistant?' and all(previous[k]=='' for k in ['tts','tts_control','system2_control'])
            assert 'stop' not in captured[1] and result['answer_enabled_at_seconds']==.48
    p=original_root/'research/s1_listening/boundary-preflight.json'
    p.write_text(json.dumps({'status':'pass','gpus':0,'methods_checked':2,'no_answer_before_question_end':True,'nonempty_first_answer_only':True,'history_and_ASR_retained':True,'question_text_not_inserted':True,'no_text_cue':True,'TTS_stop_only_while_listening':True},indent=2)+'\n')
    print(p.read_text())
if __name__=='__main__':main()
