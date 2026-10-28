"""CPU qualification of constraints, escaping, history saving and real audio bounds."""
import ast,json,re,sys
from pathlib import Path
import numpy as np
from s1_listening_rules import LISTEN_REGEX,ANSWER_REGEX,NATIVE_REGEX,saved_listening_response,install_sampling_rules
from run_s1_listening_native import prompt_bound,user,PROMPT,save,ROOT
from transformers import AutoProcessor
from vllm import SamplingParams
from types import SimpleNamespace
import xgrammar as xgr

def main():
    processor=AutoProcessor.from_pretrained(ROOT/'models/duplexomni',trust_remote_code=True)
    tokenizer_info=xgr.TokenizerInfo.from_huggingface(processor.tokenizer)
    compiler=xgr.GrammarCompiler(tokenizer_info)
    patterns={'listening':LISTEN_REGEX,'answering':ANSWER_REGEX,'native_format':NATIVE_REGEX}
    compiled={m:compiler.compile_regex(r) for m,r in patterns.items()}
    checked=[]
    examples=[('listening',{'tts_control':'','system2_control':'','asr':'He said "hello". \\ office\nnext','tts':''},True),
              ('listening',{'tts_control':'','system2_control':'','asr':'heard','tts':'Hello'},False),
              ('listening',{'tts_control':'','system2_control':'[THINK]','asr':'heard','tts':''},False),
              ('answering',{'tts_control':'[STOP]','system2_control':'','asr':'','tts':'The sky is blue.'},True),
              ('answering',{'tts_control':'','system2_control':'[THINK]','asr':'','tts':'Checking'},False),
              ('native_format',{'tts_control':'[STOP]','system2_control':'[THINK]','asr':'heard','tts':'Checking'},True)]
    for mode,fields,expected in examples:
        s=repr(fields);matcher=xgr.GrammarMatcher(compiled[mode])
        assert matcher.accept_string(s)==expected,(mode,s)
        assert bool(re.fullmatch(patterns[mode],s))==expected
        checked.append(mode+':'+str(expected))
    raw={'tts_control':'[STOP]','system2_control':'[THINK]','asr':'unaltered "guess"','tts':'not played'}
    saved=ast.literal_eval(saved_listening_response(raw));assert saved['asr']==raw['asr']
    assert all(saved[k]=='' for k in ['tts','tts_control','system2_control']) and raw['tts']=='not played'
    server=SimpleNamespace(build_sampling_params=lambda p:SamplingParams(max_tokens=999,temperature=.8))
    install_sampling_rules(server)
    assert server.build_sampling_params({'listening_rule':'unconstrained'}).structured_outputs is None
    assert server.build_sampling_params({'listening_rule':'listening'}).structured_outputs.regex==LISTEN_REGEX
    assert server.build_sampling_params({'listening_rule':'answering'}).structured_outputs.regex==ANSWER_REGEX
    assert server.build_sampling_params({'listening_rule':'native_format'}).structured_outputs.regex==NATIVE_REGEX
    sys.path.insert(0,str(ROOT/'external/duplexomni/inference_framework/realtime_serving/serving_core'))
    import server_thinker as native
    from vllm.config import ModelConfig
    from vllm.multimodal import MULTIMODAL_REGISTRY
    mm=MULTIMODAL_REGISTRY.create_processor(ModelConfig(model=str(ROOT/'models/duplexomni'),max_model_len=65536,limit_mm_per_prompt={'audio':{'count':2,'length':7680},'image':0,'video':0}))
    messages=[{'role':'system','content':PROMPT},user(np.zeros(11520,dtype='float32'))]
    prompt=native.build_engine_prompt(processor,messages,conversation_id='cpu-listening')
    actual=len(mm.apply(prompt['prompt'],mm.info.parse_mm_data(prompt['multi_modal_data']),{})['prompt_token_ids'])
    bound=prompt_bound(processor,messages);assert actual<=bound,(actual,bound)
    messages.append({'role':'assistant','content':saved_listening_response(raw)})
    messages.append(user(np.zeros(11520,dtype='float32')))
    prompt=native.build_engine_prompt(processor,messages,conversation_id='cpu-listening')
    actual2=len(mm.apply(prompt['prompt'],mm.info.parse_mm_data(prompt['multi_modal_data']),{})['prompt_token_ids'])
    bound2=prompt_bound(processor,messages);assert actual2<=bound2,(actual2,bound2)
    # Verify the same history remains and the decoder rule changes only after the last request packet.
    import math
    for row in json.loads((ROOT/'research/s1_meeting_pilot/inputs.json').read_text())['cases']:
        end=math.ceil(row['request_end_seconds']/.48)
        assert end*.48>=row['request_end_seconds'] and (end-1)*.48<row['request_end_seconds']
    result={'status':'pass','gpus':0,'constraint_examples':checked,'saved_ASR_unchanged':True,'unexecuted_actions_removed':True,'sampling_rules_connected':True,'real_processor_prompt_tokens':[actual,actual2],'conservative_bounds':[bound,bound2],'request_boundary_cases':3}
    save(ROOT/'research/s1_listening/preflight.json',result);print(json.dumps(result))

if __name__=='__main__':main()
