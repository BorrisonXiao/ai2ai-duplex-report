"""Freeze nested, sentence-aligned P01 audio suffixes; no model inference."""
import hashlib,json,math
from pathlib import Path
import numpy as np,soundfile as sf
ROOT=Path(__file__).resolve().parents[1]
D=ROOT/'research/s1_context_pressure'
def save(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value,indent=2,ensure_ascii=False)+'\n')
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def main():
    assert not (D/'protocol.json').exists(),'Preserve the frozen pressure protocol'
    row=next(r for r in json.loads((ROOT/'research/s1_meeting_pilot/inputs.json').read_text())['cases'] if r['id']=='P01')
    words_path=ROOT/'data/question_audio_completion/TS3006c/words.json'
    words=json.loads(words_path.read_text());sentences=[]
    for speaker in sorted({w['speaker'] for w in words}):
        current=[]
        def flush(ending):
            if current:sentences.append({'speaker':speaker,'start':current[0]['start'],'end':max(w['end'] for w in current),'text':' '.join(w['text'] for w in current),'boundary':ending})
            current.clear()
        for word in [w for w in words if w['speaker']==speaker and w['end']<=row['source_cutoff_seconds']]:
            if not word['punctuation']:current.append(word)
            elif word['text'] in '.?!':flush('sentence_end')
        flush('past_tail')
    groups=[]
    for sentence in sorted(sentences,key=lambda s:(s['start'],s['end'])):
        if groups and sentence['start']<groups[-1]['end']:
            groups[-1]['end']=max(groups[-1]['end'],sentence['end']);groups[-1]['sentences'].append(sentence)
        else:groups.append({'start':sentence['start'],'end':sentence['end'],'sentences':[sentence]})
    for i,g in enumerate(groups):g['id']='G'+format(i+1,'02')
    starts=[row['source_cutoff_seconds']]+[g['start'] for g in reversed(groups)]+[0.]
    levels=[]
    for index,start in enumerate(starts):
        level={'id':'P01-L'+format(index,'02'),'index':index,'source_start_seconds':start,'context_seconds':row['source_cutoff_seconds']-start,'added_group':None if index in (0,len(starts)-1) else groups[-index]['id'],'groups':min(index,len(groups)),'initial_recording_silence_added':index==len(starts)-1,'source_evidence_fully_available':all(e['start']>=start for e in row['source_evidence']),'source_frames':math.ceil(row['request_end_seconds']/.48)-math.floor(start/.48),'first_packet_zero_padding_seconds':start-math.floor(start/.48)*.48}
        levels.append(level)
    assert len(starts)==len(set(starts)) and all(a>b for a,b in zip(starts,starts[1:]))
    for start in starts:
        assert not any(s['start']<start<s['end'] for s in sentences),'A sentence is cut'
    x,sr=sf.read(ROOT/row['input_audio'],dtype='float32');assert sha(ROOT/row['input_audio'])==row['input_sha256']
    q=x[round(row['source_cutoff_seconds']*sr):]
    gain=min(.05/float(np.sqrt(np.mean(q.astype('float64')**2))),.95/float(abs(q).max()))
    protocol={'status':'prepared_not_run','question':row,'levels':levels,'sentence_groups':groups,'sentence_count':len(sentences),'boundary_rule':'Punctuation-delimited sentences per speaker; merge all overlapping sentences, then prepend one complete group at a time. Each input is a continuous audio suffix, retaining silence and overlap. The final control adds the initial recording silence.','packet_rule':'Keep the original global 480 ms grid; zero-pad only the partial first packet before the selected boundary. Spoken request packets remain bit-identical across levels.','model_input':'Audio and prior native responses only; transcript text, speaker labels, boundaries, question text and source answers are not supplied.','request_level_gain_db':20*math.log10(gain),'pressure_method':'constrained','temperature':0.,'max_tokens_per_call':256,'answer_frames':40,'answer_start':'Known question end; force a nonempty first speech fragment without prescribing words.','history':'Keep every packet in the selected suffix, without trimming or summaries; record capacity failures separately.','recognition_rule':'Question WER <= 0.25, Assistant cue present, and shared folder plus conceptual design both recognized. Recognition is scored separately from meeting-answer correctness.','answer_rule':'Score full meeting-answer correctness only where the listed evidence is present; request-only is not answerable from the recording.','threshold_rule':'Evaluate all levels; report first failure, later recovery and complete curve rather than assuming monotonic failure.','resources':{'gpus_per_job':1,'type_vram':'RTX PRO 6000 Blackwell 96 GB','roles':{'0':'Thinker, Talker, MTP and Code2Wav share GPU 0; independent Parakeet follows after S1 shutdown'},'maximum_active_gpus':4,'dependency':'One short matched job qualifies the pressure recipe before up to four independent one-GPU pressure shards. No S2 service.'},'input_hashes':{row['input_audio']:row['input_sha256'],str(words_path.relative_to(ROOT)):sha(words_path)}}
    save(D/'protocol.json',protocol)
    print(json.dumps({'levels':len(levels),'sentences':len(sentences),'nonoverlapping_sentence_groups':len(groups),'native_calls_planned':sum(l['source_frames']+40 for l in levels),'evidence_first_available_level':next(l['index'] for l in levels if l['source_evidence_fully_available']),'gpus':0}))
if __name__=='__main__':main()
