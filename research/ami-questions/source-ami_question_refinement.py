"""Review-driven prompt iteration; preserve the complete initial frozen pilot."""
import argparse
import json
import os
from pathlib import Path
import time
import ami_question_pilot as pilot

ROOT = Path(__file__).resolve().parents[1]
SNAP = ROOT / '.migration/updates/2026-10-16-ami-questions/launch-02'
REFINED = pilot.COMMON + '''
The first pilot produced three recurring defects: quoting huge spans rather than necessary evidence; asking questions that already give away the answer; and reviving an early suggestion after speakers replace it. Prevent those defects explicitly.

Read the observed prefix in time order. Work out the latest supported state of each relevant decision. If a later statement simplifies, withdraws or replaces an earlier option, that old option is not current guidance. Never turn a joking or tentative warning into a requirement. Do not treat a proposed maximum as a confirmed booking or use calendar metadata to invent missing dates. Do not invent the contents of a future email. Do not confuse the person reading a quoted message with its author.

Select TWO distinct reminder requests serving the supplied requester's current task. Each must need at least two separate facts, including an essential fact older than the newest 60 seconds. Ask about recorded decisions or commitments and their recorded rationale, not what would be the 'best' policy in general. Avoid single-fact retrieval, trivial yes/no confirmation, broad summaries, academic wording and questions that list answer choices. In at most 27 words each, ask naturally and directly for help from the assistant. The answer must not appear in the question. Use first-person task framing only if this participant actually volunteered for the task before the cutoff.

Give a concise reference answer of at most 50 words, and at most three atomic claims. Cite at most SIX essential transcript chunks per question and never cite an acknowledgment or punctuation-only chunk as factual support. Every claim must be entailed by its own citations, and the union evidence_ids must contain every claim citation. Keep uncertainty explicit. If two valid history-dependent questions are not supported, return fewer questions rather than fabricate facts. No timestamps, chunk IDs, dataset terminology or speaker-letter trivia in the question.
''' + pilot.SCHEMA.replace('Return exactly TWO distinct questions.', 'Return up to TWO distinct questions, only if all requirements can be met.')

CAPS={'instruct':4096,'thinking':16384}
MAX_LEN=49152

def optimized_engine(model):
    from vllm import LLM
    return LLM(model=str(ROOT/pilot.MODELS[model]),dtype='bfloat16',tensor_parallel_size=1,
        max_model_len=MAX_LEN,gpu_memory_utilization=.92,kv_cache_memory_bytes=8589934592,
        max_num_seqs=1,max_num_batched_tokens=2048,enforce_eager=False,enable_prefix_caching=True)

def generate(model,job):
    from transformers import AutoTokenizer
    from vllm import SamplingParams
    out=pilot.BASE/('job_'+job);out.mkdir(parents=True,exist_ok=True)
    private=out/(model+'_private.jsonl');private.touch(mode=0o600,exist_ok=False)
    tok=AutoTokenizer.from_pretrained(ROOT/pilot.MODELS[model],local_files_only=True)
    engine=optimized_engine(model)
    candidates=[]
    for w in json.loads((pilot.SNAP/'windows.json').read_text()):
        prompt=tok.apply_chat_template(pilot.gen_messages(w,'review_v3'),tokenize=False,add_generation_prompt=True)
        assert len(tok.encode(prompt,add_special_tokens=False))+CAPS[model]<=MAX_LEN
        before=time.monotonic()
        result=engine.generate([prompt],SamplingParams(max_tokens=CAPS[model],temperature=.6,top_p=.95,top_k=20,seed=17),use_tqdm=False)[0]
        output=result.outputs[0];obj,final=pilot.parse_final(output.text,thinking=model=='thinking')
        call=dict(model=model,window_id=w['id'],variant='review_v3',input_tokens=len(result.prompt_token_ids),output_tokens=len(output.token_ids),
            max_output_tokens=CAPS[model],max_model_len=MAX_LEN,kv_cache_memory_bytes=8589934592,enforce_eager=False,
            wall_seconds=time.monotonic()-before,finish_reason=output.finish_reason,final_text=final,parse_ok=obj is not None,
            output_sha256=pilot.hashlib.sha256(output.text.encode()).hexdigest())
        pilot.append(private,dict(call,prompt=prompt,generated_text=output.text));pilot.append(out/'generation_calls.jsonl',call)
        qs=obj.get('questions',[]) if obj else []
        if not isinstance(qs,list):qs=[]
        for i,q in enumerate(qs):
            if not isinstance(q,dict):continue
            row=dict(q,id=f'{model}-review_v3-{w["id"]}-{i+1}',window_id=w['id'],at=w['at'],requester=w['requester'],
                origin='local_model',model=model,prompt_variant='review_v3',job_id=job,validation_errors=pilot.validate(q,w),review_status='pending_assistant_content_review')
            if output.finish_reason=='length':row['validation_errors'].append('generation_truncated')
            candidates.append(row)
        pilot.write(out/(model+'_candidates.json'),candidates)
        print(json.dumps(dict(model=model,window=w['id'],variant='review_v3',parsed=len(qs),tokens=call['output_tokens'],seconds=call['wall_seconds'],cap=CAPS[model])),flush=True)
    pilot.write(out/(model+'_generation_summary.json'),dict(status='completed_content_review_required',job_id=job,model=model,candidates=len(candidates),
        max_output_tokens=CAPS[model],max_model_len=MAX_LEN,gpus=1,gpu_type='H100 SXM 80 GB',gpu_role='text generator only, GPU 0',max_gpus_active=1))

def inclusive_reader_messages(q,w,condition):
    # Include whole utterances that overlap the last minute. Requiring their
    # start to be inside the window can artificially discard recently heard facts.
    prefix=w['prefix']
    if condition=='recent_60s':prefix=[c for c in prefix if c['end']>=w['at']-60]
    elif condition=='question_only':prefix=[]
    elif condition=='evidence_removed':prefix=[c for c in prefix if c['id'] not in q.get('evidence_ids',[])]
    # Shared transcript first allows vLLM prefix-cache reuse across questions.
    # The proposed reference/evidence selection/role description stay withheld.
    return [{'role':'system','content':pilot.READER},{'role':'user','content':
        f"Observed through {w['at']} seconds.\nAVAILABLE TRANSCRIPT:\n"+pilot.render(prefix)+
        f"\nQuestion from participant {w['requester']}: {q['question']}"}]

def read_all(job):
    from transformers import AutoTokenizer
    from vllm import SamplingParams
    out=pilot.BASE/('job_'+job)
    candidates=[]
    for source_job in ['1110768',job]:
        for model in pilot.MODELS:
            candidates+=json.loads((pilot.BASE/('job_'+source_job)/(model+'_candidates.json')).read_text())
    candidates+=json.loads((ROOT/'research/ami_questions/authored.json').read_text())
    candidates.sort(key=lambda q:(q['window_id'],q['id']))
    windows={w['id']:w for w in json.loads((pilot.SNAP/'windows.json').read_text())}
    tok=AutoTokenizer.from_pretrained(ROOT/pilot.MODELS['instruct'],local_files_only=True)
    engine=optimized_engine('instruct')
    for q in candidates:
        for condition in ['full_prefix','recent_60s','question_only','evidence_removed']:
            messages=inclusive_reader_messages(q,windows[q['window_id']],condition)
            prompt=tok.apply_chat_template(messages,tokenize=False,add_generation_prompt=True)
            assert len(tok.encode(prompt,add_special_tokens=False))+512<=MAX_LEN
            before=time.monotonic()
            result=engine.generate([prompt],SamplingParams(max_tokens=512,temperature=0,seed=17),use_tqdm=False)[0]
            output=result.outputs[0];obj,final=pilot.parse_final(output.text)
            pilot.append(out/'readback.jsonl',dict(question_id=q['id'],condition=condition,reader_model='Qwen3-4B-Instruct-2507',
                independent_model=q.get('model')!='instruct',proposed_answer_hidden=True,role_description_hidden=True,
                evidence_ids_hidden=True,recent_window_semantics='include_complete_available_chunks_overlapping_last_60s',
                prompt_sha256=pilot.hashlib.sha256(prompt.encode()).hexdigest(),response=obj,final_text=final,
                input_tokens=len(result.prompt_token_ids),output_tokens=len(output.token_ids),finish_reason=output.finish_reason,
                wall_seconds=time.monotonic()-before))
        print(json.dumps(dict(readback_complete=q['id'],recent_window='overlap_inclusive')),flush=True)
    pilot.write(out/'completion.json',dict(status='completed_content_review_required',job_id=job,questions=len(candidates),reader_conditions=4,
        gpus=1,gpu_type='H100 SXM 80 GB',roles='Sequential 4B/30B text models on GPU 0; no audio',max_gpus_active=1,
        recent_window_semantics='include_complete_available_chunks_overlapping_last_60s',rereads_initial_job='1110768'))

def main():
    p=argparse.ArgumentParser();p.add_argument('stage',choices=['preflight','generate','read']);p.add_argument('--model',choices=list(pilot.MODELS));p.add_argument('--job',default=os.environ.get('SLURM_JOB_ID','local'));a=p.parse_args()
    pilot.check_inputs()
    if a.stage!='preflight':
        for name,expected in json.loads((SNAP/'prepared.json').read_text())['files'].items():
            assert pilot.digest(ROOT/name)==expected, 'Changed refinement input: '+name
    pilot.PROMPTS={'review_v3':REFINED}
    if a.stage=='preflight':
        from transformers import AutoTokenizer
        rows=[]
        for model,path in pilot.MODELS.items():
            tok=AutoTokenizer.from_pretrained(ROOT/path,local_files_only=True)
            for w in json.loads((pilot.SNAP/'windows.json').read_text()):
                n=len(tok.apply_chat_template(pilot.gen_messages(w,'review_v3'),tokenize=True,add_generation_prompt=True))
                assert n+CAPS[model]<=MAX_LEN
                rows.append(dict(model=model,window=w['id'],input_tokens=n,output_cap=CAPS[model],max_model_len=MAX_LEN))
        # BF16 KV: layers * KV heads * head dimension * K/V * bytes.
        kv_checks=[]
        for model,path in pilot.MODELS.items():
            cfg=json.loads((ROOT/path/'config.json').read_text())
            needed=cfg['num_hidden_layers']*cfg['num_key_value_heads']*cfg['head_dim']*2*2*MAX_LEN
            assert needed<=8589934592,(model,needed)
            kv_checks.append(dict(model=model,required_kv_bytes=needed,configured_kv_bytes=8589934592))
        pilot.write(SNAP/'preflight.json',dict(status='pass',gpus=0,calls=rows,kv_checks=kv_checks,enforce_eager=False))
        print(json.dumps(dict(status='pass',calls=len(rows),largest_input=max(r['input_tokens'] for r in rows))))
    elif a.stage=='generate':generate(a.model,a.job)
    else:read_all(a.job)

if __name__=='__main__':main()
