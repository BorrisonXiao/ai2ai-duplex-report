"""CPU checks of nested audio, request identity, evidence and matched PCM."""
import base64,hashlib,io,json,wave
from pathlib import Path
from run_s1_context_pressure import pressure_packets,short_packets,user_packet,recognition
ROOT=Path(__file__).resolve().parents[1]
def main():
    p=json.loads((ROOT/'research/s1_context_pressure/protocol.json').read_text());row=p['question'];speech_start=int(row['request_start_seconds']/.48)
    hashes=None;previous=None
    for level in p['levels']:
        packets,begin,end=pressure_packets(p,level)
        current={i:hashlib.sha256(b).hexdigest() for i,b in packets if i>=speech_start}
        if hashes is None:hashes=current
        else:assert current==hashes,'Request speech packets changed'
        assert len(packets)==end-begin==level['source_frames']
        assert not any(s['start']<level['source_start_seconds']<s['end'] for g in p['sentence_groups'] for s in g['sentences'])
        if previous is not None:assert level['context_seconds']>previous
        previous=level['context_seconds']
    import sys
    sys.path.insert(0,str(ROOT/'external/duplexomni/inference_framework/realtime_serving'))
    import omni_realtime_server as native
    for _,pcm in short_packets():
        packet=user_packet(pcm)
        encoded=packet['content'][1]['input_audio']['data']
        with wave.open(io.BytesIO(base64.b64decode(encoded)),'rb') as f:assert f.getframerate()==24000 and f.readframes(11520)==pcm
        assert base64.b64decode(encoded)==base64.b64decode(native.pcm_to_b64_wav(pcm))
        assert [x.get('text') for x in packet['content'] if x['type']=='text']==["{'audio_input': '","', 'from_s2': ''}"]
    assert recognition(row['question'],row['question'])['recognized']
    assert not recognition('then any then any',row['question'])['recognized']
    assert not p['levels'][0]['source_evidence_fully_available'] and p['levels'][-1]['source_evidence_fully_available']
    result={'status':'pass','gpus':0,'levels_checked':len(p['levels']),'request_speech_packets_identical':len(hashes),'no_sentence_cut':True,'strictly_growing_context':True,'native_DailyTalk_PCM_and_WAV_match':True,'no_question_transcript_in_carrier':True,'recognition_positive_negative_checks':True,'source_answerability_separate':True}
    (ROOT/'research/s1_context_pressure/preflight.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
if __name__=='__main__':main()
