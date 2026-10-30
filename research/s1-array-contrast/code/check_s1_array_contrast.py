"""Check actual 24 kHz packets and the unchanged pressure inference interface."""
import ast,hashlib,json
from pathlib import Path
from run_s1_context_pressure import ROOT,pressure_packets,save
def main():
    d=ROOT/'research/s1_array_contrast';spec=json.loads((d/'protocol.json').read_text());original=json.loads((ROOT/'research/s1_context_pressure/protocol.json').read_text())
    baseline,begin,end=pressure_packets(original,original['levels'][30]);rows=[]
    # The first packet touching the insertion also contains the last partial source frame.
    request_tick=int(original['question']['source_cutoff_seconds']/.48)
    reference={tick:pcm for tick,pcm in baseline if tick>=request_tick}
    for row in spec['cases']:
        frames,a,b=pressure_packets(row['protocol'],row['level']);assert (a,b)==(begin,end) and len(frames)==len(baseline)
        assert {tick:pcm for tick,pcm in frames if tick>=request_tick}==reference
        different=sum(pcm!=baseline[i][1] for i,(tick,pcm) in enumerate(frames))
        assert different==0 if row['id']=='headset_mix' else different>0
        assert abs(row['context_rms']/spec['cases'][0]['context_rms']-1)<.001
        rows.append(dict(id=row['id'],listening_frames=len(frames),question_boundary_and_request_packets_identical=True,changed_context_packets=different,pcm_sha256=hashlib.sha256(b''.join(pcm for _,pcm in frames)).hexdigest()))
    for name in ['prepare_s1_array_contrast','run_s1_array_contrast','run_s1_array_contrast_job','postprocess_s1_array_contrast']:
        ast.parse((ROOT/'scripts'/f'{name}.py').read_text())
    smoke=(ROOT/'scripts/smoke_duplexomni.py').read_text()
    assert smoke.count('from native_interaction import run_native_interaction')==1
    assert smoke.count('str(root / "scripts/duplex_server_smoke.py")')==1
    save(d/'preflight.json',dict(status='pass',cases=rows,levels=[30],model_inference_performed=False,gpus=0,scope='Actual packet identity, changed context, RMS matching and native caller interface; not a model-accuracy result.'))
    print((d/'preflight.json').read_text())
if __name__=='__main__':main()
