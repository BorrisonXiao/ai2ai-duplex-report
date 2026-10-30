"""Collect actual native/ASR results and validate shared request packets."""
import argparse,hashlib,json,math
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];D=ROOT/'research/s1_array_sweep'
def read(p):return json.loads(p.read_text())
def save(p,x):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x,indent=2,ensure_ascii=False)+'\n')
def main():
    p=argparse.ArgumentParser();p.add_argument('--partial',action='store_true');a=p.parse_args();spec=read(D/'resolved-protocol.json');rows=[];reference=None
    for case in spec['cases']:
        row=case.copy();folder=ROOT/case['source'];path=folder/'run.json'
        if not path.exists():row['status']='not_started';rows.append(row);continue
        r=read(path);row.update({k:r.get(k) for k in ['status','speech_text','question_asr','recognition','frames_completed','listening_frames','answer_frames','max_prompt_tokens','wall_seconds','history_trimmed','error']})
        if (folder/'asr.json').exists():row['spoken_transcript']=read(folder/'asr.json')['text']
        if r['status'] in ['completed_content_review_required','failed','capacity_failure']:
            row['audio_sha256']=hashlib.sha256((folder/'response.wav').read_bytes()).hexdigest();assert row['audio_sha256']==r['audio_sha256']
        row['response_valid']=r['status']=='completed_content_review_required'
        row['WER_valid']=r['status'] in ['completed_content_review_required','failed','capacity_failure'] and r['frames_completed']>=r['listening_frames']+4
        if row['WER_valid']:
            assert not r['history_trimmed'] and r['ASR_text_changes']==r['listening_field_violations']==0
            if row['response_valid']:assert r['frames_completed']==r['listening_frames']+40
            digest=hashlib.sha256((folder/'response.wav').read_bytes()).hexdigest();assert digest==r['audio_sha256'];row['audio_sha256']=digest
            turns=[json.loads(t) for t in (folder/'turns.jsonl').read_text().splitlines()];assert len(turns)==r['frames_completed'] and all(t['finish_reason']!='length' for t in turns)
            packets={str(t['source_frame']):t['packet_pcm_sha256'] for t in turns if int(309.21/.48)<=t['source_frame']<math.ceil(314.5886875/.48)}
            assert len(packets)==12
            if reference is None:reference=packets
            else:assert reference==packets,case['id']
            row['last_answer_packet_speaking']=bool(turns[-1]['fields']['tts'])
        rows.append(row)
    completed=sum(r['status']=='completed_content_review_required' and 'spoken_transcript' in r for r in rows);new_done=sum(not r['reused'] and r['status']=='completed_content_review_required' and 'spoken_transcript' in r for r in rows)
    terminal=sum(r['status'] in ['completed_content_review_required','failed','capacity_failure'] and 'spoken_transcript' in r for r in rows)
    result=dict(status='completed_content_review_required' if terminal==123 else 'partial',terminal_signal_levels=terminal,completed_signal_levels=completed,new_completed_cases=new_done,new_s1_completed=sum(not r['reused'] and r['status']=='completed_content_review_required' for r in rows),new_s1_failed=sum(not r['reused'] and r['status'] in ['failed','capacity_failure'] for r in rows),new_planned_cases=78,plotted_signal_levels=123,cases=rows,shared_request_packet_hashes=reference)
    save(D/'aggregate.json',result)
    if not a.partial:assert terminal==123,'Wait for all attempts and independent ASR; keep execution failures distinct from WER'
    print(json.dumps({k:v for k,v in result.items() if k not in ['cases','shared_request_packet_hashes']}))
if __name__=='__main__':main()
