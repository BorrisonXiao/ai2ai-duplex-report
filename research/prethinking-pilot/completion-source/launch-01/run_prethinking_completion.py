"""Teacher completion and explicit two-round history; token receipt timestamps."""
import argparse
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import subprocess
import threading
import time

ROOT=Path(__file__).resolve().parents[1]

def sha(text):return hashlib.sha256(text.encode()).hexdigest()

def data_for(chunks,at,new_ids,history):
    seen=[{k:c[k] for k in ('id','speaker','start','end','available','text','boundary') if k in c} for c in chunks if c['available']<=at+1e-8]
    by_id={c['id']:c for c in seen}
    assert all(ident in by_id for ident in new_ids)
    assert all(c['end']<=at+1e-8 for c in seen)
    assert all(h['observed_through']<at for h in history)
    return {'observed_through_seconds':at,'participant_perspective':'C','observed_transcript':seen,'new_chunk_ids':new_ids,'retained_private_history':history}

def make_prompt(tokenizer,prompts,data,mode):
    lines=[f"Observed through {data['observed_through_seconds']:.2f} seconds. Perspective: participant C.",
           'Observed transcript, ordered by availability. [partial] marks a capped incomplete sentence:']
    for c in data['observed_transcript']:
        lines.append(c['id']+' '+c['speaker']+(' [partial]' if c.get('boundary')=='15s_cap' else '')+': '+c['text'])
    history=data['retained_private_history']
    lines.append('Earlier private thinking, written before the current input; it is not transcript evidence:')
    if mode=='prefill_continuation' and history:
        lines.append('Its verbatim private text is preserved in the assistant thinking prefix below. Earlier final notes: '+json.dumps([h['final_text'] for h in history],ensure_ascii=False))
    else:lines.append(json.dumps(history,ensure_ascii=False))
    lines.extend(['CURRENT new chunk IDs: '+', '.join(data['new_chunk_ids']),
                  'Continue the analysis for THIS update. Preserve grounded deductions, revise or discard obsolete assumptions, and do not merely repeat earlier analysis. Cite the new evidence IDs. Earlier reasoning can be wrong. Finish the private analysis when enough useful work is done, then return the requested compact JSON notes.'])
    prompt=tokenizer.apply_chat_template([{'role':'system','content':prompts['common']+' '+prompts['variants']['selective']},
                                        {'role':'user','content':'\n'.join(lines)}],tokenize=False,add_generation_prompt=True)
    prefix=''
    if mode=='prefill_continuation' and history:
        # The native template opens <think>. Keep it open; do not copy </think> or EOS.
        assert prompt.endswith('<think>\n')
        prefix='\n\n'.join(h['private_reasoning'] for h in history)
        prefix+='\n\nNew transcript update at '+f"{data['observed_through_seconds']:.2f}"+' seconds. Continue and revise using '+', '.join(data['new_chunk_ids'])+':\n'
        prompt+=prefix
    assert all(h['private_reasoning'] in prompt for h in history)
    return prompt,prefix

def stream_generate(engine,token_ids,params,request_id):
    started=time.perf_counter();engine.add_request(request_id,{'prompt_token_ids':token_ids},params)
    events=[];previous=[];final=None
    while engine.has_unfinished_requests():
        for result in engine.step():
            if not result.outputs:continue
            output=result.outputs[0];ids=list(output.token_ids)
            assert ids[:len(previous)]==previous,'Non-cumulative token output'
            if len(ids)>len(previous):events.append({'seconds':time.perf_counter()-started,'tokens':len(ids),'new_tokens':len(ids)-len(previous)})
            previous=ids
            if result.finished:final=result
    wall=time.perf_counter()-started
    assert final is not None and events
    first=events[0]['seconds'];last=events[-1]['seconds'];n=len(previous)
    # Receipt times include detokenization/driver overhead; these are not kernel timings.
    after_first=n-events[0]['tokens']
    return final,dict(wall_seconds=wall,first_token_seconds=first,last_token_seconds=last,
        output_tokens_per_wall_second=n/wall,decode_tokens_per_second=after_first/(last-first) if last>first else None,
        decode_seconds=last-first,first_receipt_tokens=events[0]['tokens'],receipt_events=events,
        timestamp_semantics='Host receipt after vLLM engine step; may group multiple tokens, includes engine/detokenization/driver overhead. Pretokenized input; no other concurrent request.')

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--config',type=Path,required=True);args=parser.parse_args()
    cfg=json.loads(args.config.read_text());prepared=json.loads((args.config.parent/'prepared.json').read_text())
    for name,h in prepared['files'].items():assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==h,name
    assets=json.loads((ROOT/'.migration/updates/2026-10-12-prethinking-pilot/assets-complete.json').read_text())
    assert assets['repo']==cfg['repo'] and assets['revision']==cfg['revision']
    source=json.loads((ROOT/'.migration/updates/2026-10-12-prethinking-pilot/teacher-source.json').read_text())
    for item in source['files']:
        if item['name'].endswith('.safetensors'):assert (ROOT/cfg['model']/item['name']).stat().st_size==item['bytes']
    assert os.environ.get('SLURM_JOB_ID') and os.environ.get('CUDA_VISIBLE_DEVICES')
    job=os.environ['SLURM_JOB_ID'];out=ROOT/'exp/prethinking_pilot'/('completion_'+job);out.mkdir(parents=True,exist_ok=True)
    from transformers import AutoTokenizer
    from vllm import LLM,SamplingParams
    from vllm.sampling_params import RequestOutputKind
    tokenizer=AutoTokenizer.from_pretrained(ROOT/cfg['model'],local_files_only=True)
    chunks=json.loads((ROOT/cfg['chunks']).read_text());prompts=json.loads((ROOT/cfg['prompts']).read_text());cases=json.loads((ROOT/cfg['cases']).read_text())
    original=[json.loads(line) for line in (ROOT/cfg['original_calls']).read_text().splitlines()][54]
    summary={'job_id':job,'status':'started_content_review_required','model':cfg['repo'],'revision':cfg['revision'],'config':cfg,
             'software':{p:importlib.metadata.version(p) for p in ['vllm','torch','transformers']},'calls':[],'warmups':[],
             'gpus':1,'requested_gpu_type':cfg['gpu_type'],'roles':'Qwen teacher only on GPU 0; no shared model/service','max_gpus_active':1,
             'two_round_semantics':cases['causality'],'speed_semantics':'Output/wall includes prefill; decode speed uses tokens received after first receipt divided by subsequent receipt interval. CPU prompt formatting/tokenization timed separately. Startup/warmups excluded from study speeds.'}
    def save():(out/'summary.json').write_text(json.dumps(summary,indent=2,ensure_ascii=False)+'\n')
    save();stop=threading.Event()
    def sample_memory():
        with (out/'memory.csv').open('w') as h:
            h.write('monotonic_seconds,gpu_uuid,memory_used_mib,memory_total_mib\n')
            while not stop.is_set():
                r=subprocess.run(['nvidia-smi','-i',os.environ['CUDA_VISIBLE_DEVICES'],'--query-gpu=uuid,memory.used,memory.total','--format=csv,noheader,nounits'],capture_output=True,text=True)
                for line in r.stdout.splitlines():h.write(str(time.monotonic())+','+line+'\n')
                h.flush();stop.wait(1)
    worker=threading.Thread(target=sample_memory,daemon=True);worker.start();started=time.perf_counter()
    private=out/'private_calls.jsonl';private.touch();private.chmod(0o600)
    try:
        model=LLM(model=str(ROOT/cfg['model']),dtype='bfloat16',tensor_parallel_size=1,max_model_len=cfg['max_model_len'],
                  gpu_memory_utilization=.9,kv_cache_memory_bytes=cfg['kv_cache_memory_bytes'],max_num_seqs=1,max_num_batched_tokens=2048,
                  enforce_eager=True,enable_prefix_caching=False,disable_log_stats=True)
        summary['startup_seconds']=time.perf_counter()-started;save()
        def run(prompt,data,plan,prefilled=''):
            before=time.perf_counter();ids=tokenizer.encode(prompt,add_special_tokens=False);prepare=time.perf_counter()-before
            budget=min(cfg['max_new_tokens'],cfg['max_model_len']-len(ids)-64)
            assert budget>0 and len(ids)+budget<=cfg['max_model_len']
            params=SamplingParams(max_tokens=budget,temperature=.6,top_p=.95,top_k=20,seed=17,output_kind=RequestOutputKind.CUMULATIVE,skip_special_tokens=False)
            result,timing=stream_generate(model.llm_engine,ids,params,'completion-'+str(len(summary['calls'])))
            output=result.outputs[0];raw=output.text;reasoning,marker,final=raw.partition('</think>')
            final_clean=final.replace('<|im_end|>','').replace('<|endoftext|>','').strip() if marker else ''
            index=len(summary['calls']);row=dict(index=index,**plan,at=data['observed_through_seconds'],new_ids=data['new_chunk_ids'],history_mode=plan['mode'],seed=17,variant='selective',
                input_tokens=len(ids),output_tokens=len(output.token_ids),budget=budget,finish_reason=output.finish_reason,stop_reason=output.stop_reason,
                thinking_closed=bool(marker),natural_response_complete=output.finish_reason=='stop' and bool(marker),
                private_token_count=list(output.token_ids).index(151668) if 151668 in output.token_ids else len(output.token_ids),
                final_text=final_clean,prompt_prepare_seconds=prepare,**timing,prompt_sha256=sha(prompt),generated_sha256=sha(raw),
                retained_history_entries=len(data['retained_private_history']),observed_chunk_count=len(data['observed_transcript']),
                prefilled_characters=len(prefilled),prefilled_sha256=sha(prefilled),prefilled_private_text_is_input_only=True)
            try:row['final_json']=json.loads(final_clean) if final_clean else None
            except json.JSONDecodeError:row['final_json']=None
            full=dict(row,prompt=prompt,input_payload=data,generated_text=raw,generated_token_ids=list(output.token_ids),private_reasoning=reasoning,thinking_sha256=sha(reasoning),prefilled_text=prefilled)
            with private.open('a') as h:h.write(json.dumps(full,ensure_ascii=False)+'\n')
            summary['calls'].append({k:v for k,v in row.items() if k!='receipt_events'});save()
            print(json.dumps({k:row[k] for k in ['index','sample','round','mode','output_tokens','finish_reason','thinking_closed','natural_response_complete','wall_seconds','decode_tokens_per_second','retained_history_entries']}),flush=True)
            if not row['natural_response_complete']:raise RuntimeError('Completion not achieved; preserve this failure and enlarge allowance/inspect before further rounds.')
            return full
        # Engine initialization already profiles kernels. Two explicit bounded generation warmups are recorded separately.
        warm_prompts=[tokenizer.apply_chat_template([{'role':'user','content':'What is 2 + 2?'}],tokenize=False,add_generation_prompt=True),original['prompt']]
        for i,prompt in enumerate(warm_prompts):
            ids=tokenizer.encode(prompt,add_special_tokens=False);params=SamplingParams(max_tokens=64,temperature=.6,top_p=.95,top_k=20,seed=17,output_kind=RequestOutputKind.CUMULATIVE,skip_special_tokens=False)
            result,timing=stream_generate(model.llm_engine,ids,params,'warmup-'+str(i))
            summary['warmups'].append(dict(index=i,input_tokens=len(ids),output_tokens=len(result.outputs[0].token_ids),finish_reason=result.outputs[0].finish_reason,**timing));save()
        single=cases['single_round'];data=data_for(chunks,single['at'],single['new_ids'],[]);prompt,prefill=make_prompt(tokenizer,prompts,data,'reset_control')
        run(prompt,data,dict(stage='single_round',sample='participation',round=0,mode='reset_control',next_arrival=single['next_arrival']),prefill)
        run(original['prompt'],original['input_payload'],dict(stage='archived_prompt_completion',sample='original_call_54',round=0,mode='archived_raw_private',next_arrival=650))
        for sample in cases['two_round']:
            first,second=sample['rounds'];data=data_for(chunks,first['at'],first['new_ids'],[]);prompt,prefill=make_prompt(tokenizer,prompts,data,'reset_control')
            initial=run(prompt,data,dict(stage='two_round',sample=sample['id'],round=0,mode='shared_first_round'),prefill)
            history=[dict(observed_through=first['at'],status='completed',private_reasoning=initial['private_reasoning'],final_text=initial['final_text'],source_call=initial['index'],generated_tokens=initial['output_tokens'],generated_sha256=initial['generated_sha256'])]
            for mode in cases['modes']:
                data=data_for(chunks,second['at'],second['new_ids'],history if mode!='reset_control' else [])
                prompt,prefill=make_prompt(tokenizer,prompts,data,mode)
                run(prompt,data,dict(stage='two_round',sample=sample['id'],round=1,mode=mode,previous_call=initial['index'],review_question=sample['review_question']),prefill)
        summary['status']='completed_content_review_required'
    except BaseException as exc:
        summary.update(status='failed',error=type(exc).__name__+': '+str(exc));raise
    finally:
        stop.set();worker.join(timeout=3);summary['wall_seconds']=time.perf_counter()-started;save()

if __name__=='__main__':main()
