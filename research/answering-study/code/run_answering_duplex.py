"""Paired answering pilot on the qualified DuplexOmni native packet runner."""
import argparse,json,os
from pathlib import Path
import run_s1_context_pressure as native
from run_answering_native import MEETING
ROOT=Path(__file__).resolve().parents[1]
def trial(root,out,config,trace):
 from transformers import AutoProcessor
 snap=ROOT/os.environ['ANSWERING_SNAPSHOT']
 for path,h in json.loads((snap/'hashes.json').read_text()).items():assert native.sha(ROOT/path)==h,path
 spec=json.loads((ROOT/'research/answering_study_20261101/pilot-audio.json').read_text());base=ROOT/'exp/answering_native'/os.environ['SLURM_JOB_ID'];base.mkdir(parents=True,exist_ok=True);processor=AutoProcessor.from_pretrained(ROOT/'models/duplexomni',trust_remote_code=True);results=[]
 results.append(native.run_case(dict(id='native-control',kind='short',method='native',answer_frames=125),config,base,processor,base/'heartbeat.json'))
 native.PROMPT=native.PROMPT+'\n'+MEETING
 for row in sorted(spec['cases'],key=lambda r:(r['variant']=='full',r['id'])):
  protocol=dict(question=row,request_level_gain_db=0);level=dict(id=row['id'],index=0,source_start_seconds=0,context_seconds=row['source_cutoff_seconds']);case=dict(id=row['id'],kind='pressure',method='constrained',level=level,protocol=protocol,answer_frames=125)
  result=native.run_case(case,config,base,processor,base/'heartbeat.json');result.update(question_id=row['question_id'],variant=row['variant'],system_prompt=native.PROMPT);native.save(base/row['id']/'run.json',result);results.append(result);native.save(base/'summary.json',dict(model='duplexomni',status='running',cases=results,GPUs=1))
 native.save(base/'summary.json',dict(model='duplexomni',status='completed_content_review_required',cases=results,GPUs=1));return [dict(name=r['id'],status=r['status'],turns=[],wall_seconds=r.get('wall_seconds',0)) for r in results]
def main():
 p=argparse.ArgumentParser();p.add_argument('--config',type=Path,required=True);a=p.parse_args();c=json.loads(a.config.read_text());source=(ROOT/'scripts/smoke_duplexomni.py').read_text().replace('from native_interaction import run_native_interaction','from run_answering_duplex import trial as run_native_interaction').replace('str(root / "scripts/duplex_server_smoke.py")','str(root / "scripts/s1_listening_server.py")').replace('21991',str(c['thinker_port'])).replace('21992',str(c['talker_port']))
 exec(compile(source,str(ROOT/'scripts/smoke_duplexomni.py')+' [answering pilot]','exec'),{'__name__':'__main__','__file__':str(ROOT/'scripts/smoke_duplexomni.py')})
if __name__=='__main__':main()
