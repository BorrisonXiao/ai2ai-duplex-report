"""Require grammar compatibility with actual prior working native ASR responses."""
import ast,json,re
from pathlib import Path
import xgrammar as xgr
from transformers import AutoTokenizer
from s1_listening_rules import NATIVE_REGEX,LISTEN_REGEX,ANSWER_REGEX,saved_listening_response
from s1_listening_prefix import fields_from_prefix
ROOT=Path(__file__).resolve().parents[1]
def main():
    tokenizer=AutoTokenizer.from_pretrained(ROOT/'models/duplexomni',trust_remote_code=True)
    compiler=xgr.GrammarCompiler(xgr.TokenizerInfo.from_huggingface(tokenizer))
    patterns={'native':NATIVE_REGEX,'listening':LISTEN_REGEX,'answering':ANSWER_REGEX}
    compiled={name:compiler.compile_regex(pattern) for name,pattern in patterns.items()}
    prior=json.loads((ROOT/'exp/s1_empty_diagnosis/1318396/sky-native-control/result.json').read_text())
    checked=[]
    for turn in prior['turns']:
        raw=turn['raw_text'];fields=ast.literal_eval(raw)
        for name in ['native','answering']:
            assert xgr.GrammarMatcher(compiled[name]).accept_string(raw),(name,raw)
        saved=saved_listening_response(fields)
        assert list(ast.literal_eval(saved))==list(fields)
        assert ast.literal_eval(saved)['asr']==fields['asr']
        assert xgr.GrammarMatcher(compiled['listening']).accept_string(saved),saved
        prefix=raw.split(", 'tts': ",1)[0]
        parsed,audit=fields_from_prefix(prefix)
        assert parsed['asr']==fields['asr']
        assert list(ast.literal_eval(saved_listening_response(parsed)))==list(fields)
        checked.append({'asr':fields['asr'],'field_order':list(fields)})
    for text in ['literal, \'tts\': text', 'A "quote" and \\ backslash', "I'm sure"]:
        for order in [['asr','tts','tts_control','system2_control'],['tts_control','system2_control','asr','tts']]:
            fields={k:text if k=='asr' else '' for k in order};raw=repr(fields)
            assert xgr.GrammarMatcher(compiled['listening']).accept_string(raw)
            # Stop marker inside a quoted ASR must never be accepted as a complete prefix.
            for prefix in [repr({'asr':text})[:-1],repr({'tts_control':'','system2_control':'','asr':text})[:-1]]:
                assert fields_from_prefix(prefix)[0]['asr']==text
    result={'status':'pass','gpus':0,'actual_recorded_turns_accepted':len(checked),'native_field_orders_preserved':True,'ASR_unchanged':True,'source':'Earlier successful sky control; no new inference or evaluation score.','examples':checked[:8]}
    p=ROOT/'research/s1_listening/recorded-format-preflight.json';p.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k!='examples'}))
if __name__=='__main__':main()
