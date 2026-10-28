"""Persist Codex's source/native-text/independent-ASR review of all 41 runs."""
import collections,hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];D=ROOT/'research/s1_context_pressure'
def read(p):return json.loads(p.read_text())
def write(p,d):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d,indent=2,ensure_ascii=False)+'\n')
def main():
    protocol=read(D/'protocol.json');records=[]
    meaning=set(range(12))|{16,17,19,20,21,22,26,33}
    unsupported={0,4,5,11,16};other_topic={12,13,14,15,24,25,27,28,36,38,39,40};clarification={26,34}
    expected_packets=None;empty_ASR=0;strict=0;late_core=[]
    for job in read(D/'pressure-submissions.json')['jobs']:
        base=ROOT/job['output']
        for level in job['levels']:
            folder=base/('P01-L'+format(level,'02'));r=read(folder/'run.json');spoken=read(folder/'asr.json')['text']
            assert r['status']=='completed_content_review_required' and r['ASR_text_changes']==r['listening_field_violations']==0
            assert r['frames_completed']==r['listening_frames']+40 and not r['history_trimmed']
            turns=[json.loads(s) for s in (folder/'turns.jsonl').read_text().splitlines()]
            assert all(t['finish_reason']!='length' for t in turns)
            assert all(not t['fields']['tts_control'] and not t['fields']['system2_control'] for t in turns if t['phase']=='answering')
            q_start=int(protocol['question']['request_start_seconds']/.48);q_end=__import__('math').ceil(protocol['question']['request_end_seconds']/.48)
            packets={t['source_frame']:t['packet_pcm_sha256'] for t in turns if q_start<=t['source_frame']<q_end}
            if expected_packets is None:expected_packets=packets
            else:assert packets==expected_packets
            late=''.join(t['fields']['asr'] for t in turns if t['index']>=r['listening_frames']+4)
            if 'folder' in late.lower():late_core.append(level)
            empty_ASR+=not bool(r['question_asr'].strip());strict+=r['recognition']['recognized']
            supported=r['level']['source_evidence_fully_available'];facts=1 if level==30 else 0
            if level in unsupported:kind='Unsupported folder status';reason='The request is recognizable, but the reply asserts a folder/file status absent from the supplied prefix.'
            elif level in other_topic:kind='Earlier or different topic';reason='The reply discusses another topic or task instead of answering the shared-folder question.'
            elif level in clarification:kind='Asks for details';reason='The reply asks for more details; it does not provide the reference facts.'
            elif level==18:kind='Greeting';reason='The reply greets the user and does not address the folder question.'
            elif level==30:kind='Partial source answer';reason='The reply recalls the shared-folder location but does not identify the components-design PowerPoint; access at any time is not established.'
            else:kind='Acknowledgment only';reason='The reply says it will check or retrieve something but supplies neither required reference fact within the captured window.'
            if level==5:reason+=' ASR preserves the core request but adds a new readiness question.'
            if level==33:reason+=' The core question returns in ASR despite 206.11 seconds of earlier audio.'
            if level==36:reason='The reply explains generic conceptual-design components rather than identifying the PowerPoint file discussed in the meeting.'
            if level==38:reason='The reply explains generic PowerPoint slide structure; it does not identify the components-design PowerPoint as the file that was found.'
            if level==40:reason='The full-prefix reply asks what needs translating, returning to an earlier incorrect ASR interpretation instead of answering the folder question.'
            answer_turns=[t for t in turns if t['phase']=='answering'];last_word=max((i for i,t in enumerate(answer_turns) if t['fields']['tts'].strip()),default=-1)
            review={'reviewer':'Codex manual inspection of recorded native text, independent Parakeet speech transcripts and reference evidence; no human listening rating','question_meaning_in_ASR':'Preserved' if level in meaning else 'Missing or unrelated','response_type':kind,'reason':reason,'all_answer_evidence_available':supported,'native_reference_facts_recovered':facts if supported else None,'spoken_reference_facts_recovered':facts if supported else None,'reference_facts_required':2,'native_answer_complete':False if supported else None,'spoken_answer_complete':False if supported else None,'spoken_review_complete':True,'response_window_seconds':19.2,'speech_text_in_last_packet':last_word==39,'trailing_empty_speech_packets':39-last_word,'later_ASR_text':late,'native_text_sha256':hashlib.sha256(r['speech_text'].encode()).hexdigest(),'audio_sha256':r['audio_sha256'],'spoken_transcript_sha256':hashlib.sha256(spoken.encode()).hexdigest(),'source_facts':['Files were reported in the shared folder.','A components-design PowerPoint was identified.'],'scope':'Insufficient-history levels are not scored as complete meeting-answer trials; source-grounded answer checks use the 11 prefixes with all listed evidence.'}
            if review['speech_text_in_last_packet']:review['reason']+=' The last captured packet still contains speech text; the capture window is not a model EOS.'
            write(folder/'source-review.json',review);records.append({'level':level,'job':job['job'],'context_seconds':r['level']['context_seconds'],'strict_ASR_pass':r['recognition']['recognized'],'WER':r['recognition']['WER'],'max_prompt_tokens':r['max_prompt_tokens'],'frames':r['frames_completed'],'wall_seconds':r['wall_seconds'],'spoken_nonempty':bool(spoken.strip()),'native_nonempty':bool(r['speech_text'].strip()),**review})
    assert len(records)==41 and len({r['level'] for r in records})==41
    eligible=[r for r in records if r['all_answer_evidence_available']]
    first_missing=min((r for r in records if r['question_meaning_in_ASR']!='Preserved'),key=lambda r:r['level'])
    recovered=[r for r in records if r['level']>first_missing['level'] and r['question_meaning_in_ASR']=='Preserved']
    summary={'status':'completed_source_reviewed','distinct_pressure_questions':1,'levels':41,'strict_ASR_passes':strict,'ASR_core_question_preserved':len(meaning),'ASR_empty':empty_ASR,'ASR_wrong_repetition':1,'native_replies_nonempty':sum(r['native_nonempty'] for r in records),'speech_transcripts_nonempty':sum(r['spoken_nonempty'] for r in records),'answer_evidence_complete_levels':len(eligible),'complete_native_answers':sum(bool(r['native_answer_complete']) for r in eligible),'complete_spoken_answers':sum(bool(r['spoken_answer_complete']) for r in eligible),'partial_answer_levels':[r['level'] for r in eligible if r['native_reference_facts_recovered']>0],'response_types':dict(collections.Counter(r['response_type'] for r in records)),'first_missing_core_level':first_missing['level'],'first_missing_core_context_seconds':first_missing['context_seconds'],'first_missing_core_max_prompt_tokens':first_missing['max_prompt_tokens'],'later_core_recovery_levels':[r['level'] for r in recovered],'last_core_recovery_context_seconds':max(r['context_seconds'] for r in recovered),'later_ASR_mentions_folder_levels':late_core,'native_calls':sum(r['frames'] for r in records),'summed_case_wall_seconds':sum(r['wall_seconds'] for r in records),'frames_per_case_wall_second':sum(r['frames'] for r in records)/sum(r['wall_seconds'] for r in records),'max_prompt_tokens':max(r['max_prompt_tokens'] for r in records),'engine_context_tokens':49152,'request_speech_packet_hashes_identical':len(expected_packets),'ASR_text_changes':0,'listening_rule_violations':0,'token_limit_stops':0,'context_trimming':0,'nonempty_answer_controls':0,'response_window_seconds':19.2,'last_packet_still_speaking_levels':[r['level'] for r in records if r['speech_text_in_last_packet']],'meaning_score_note':'Added Codex review after observing that the frozen strict key-term rule rejects understandable share/shared variations; original WER and strict flags are unchanged.','meaning_rule':'ASR retains both the shared-folder status request and its reference to missing conceptual-design files; minor word forms/fillers are allowed. This is ASR content, not proof of internal comprehension.','correct_answer_rule':'With all listed evidence supplied, state both the reported folder placement and identified components-design PowerPoint without a material unsupported status/action. Score native text and independent speech transcripts separately.','limitations':'One question, one greedy replay per prefix, controlled answer start and a 19.2-second response window; this is not the full 105-question benchmark or a universal context limit.','cases':sorted(records,key=lambda r:r['level'])}
    write(D/'review.json',summary);write(ROOT/'reports/s1_context_pressure_review.json',summary)
    print(json.dumps({k:v for k,v in summary.items() if k!='cases'}))
if __name__=='__main__':main()
