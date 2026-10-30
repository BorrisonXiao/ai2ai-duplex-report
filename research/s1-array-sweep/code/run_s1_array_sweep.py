"""Run assigned microphone/context pairs with the unchanged qualified native loop."""
import argparse,json,os
from pathlib import Path
from run_s1_context_pressure import ROOT,run_case,save,sha
def run_trial(root,out,config,trace):
    from transformers import AutoProcessor
    snap=ROOT/os.environ['S1_SWEEP_SNAPSHOT'];spec=json.loads((snap/'protocol.json').read_text());conditions={r['id']:r for r in spec['conditions']}
    for name,digest in json.loads((snap/'hashes.json').read_text()).items():assert sha(ROOT/name)==digest,name
    base=ROOT/'exp/s1_array_sweep'/os.environ['SLURM_JOB_ID'];base.mkdir(parents=True,exist_ok=True);processor=AutoProcessor.from_pretrained(ROOT/'models/duplexomni',trust_remote_code=True);results=[]
    for row in config['sweep']['cases']:
        name,index=row['condition'],row['index'];case=dict(id=row['id'],kind='pressure',method='constrained',protocol=conditions[name]['protocol'],level=spec['levels'][index])
        result=run_case(case,config,base,processor,base/'heartbeat.json');result['condition']=name;save(base/row['id']/'run.json',result);results.append(result)
        save(base/'summary.json',dict(status='running',cases=results,gpus=1,maximum_active_gpus=1))
    save(base/'summary.json',dict(status='completed_content_review_required',cases=results,gpus=1,maximum_active_gpus=1))
    assert all(r['status']=='completed_content_review_required' for r in results),'Inspect partial results and capacity/format errors'
    return [dict(name=r['id'],status=r['status'],turns=[],wall_seconds=r['wall_seconds']) for r in results]
def main():
    p=argparse.ArgumentParser();p.add_argument('--config',type=Path,required=True);a=p.parse_args();config=json.loads(a.config.read_text())
    source=(ROOT/'scripts/smoke_duplexomni.py').read_text().replace('from native_interaction import run_native_interaction','from run_s1_array_sweep import run_trial as run_native_interaction').replace('str(root / "scripts/duplex_server_smoke.py")','str(root / "scripts/s1_listening_server.py")').replace('21991',str(config['thinker_port'])).replace('21992',str(config['talker_port']))
    exec(compile(source,str(ROOT/'scripts/smoke_duplexomni.py')+' [array sweep]','exec'),{'__name__':'__main__','__file__':str(ROOT/'scripts/smoke_duplexomni.py')})
if __name__=='__main__':main()
