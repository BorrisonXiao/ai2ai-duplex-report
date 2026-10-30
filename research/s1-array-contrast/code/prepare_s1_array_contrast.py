"""Prepare a single-level P01 microphone contrast from released AMI signals."""
import copy, hashlib, json, struct, urllib.request
from pathlib import Path
import numpy as np
import soundfile as sf
ROOT=Path(__file__).resolve().parents[1]
D=ROOT/'research/s1_array_contrast'; A=ROOT/'data/s1_array_contrast'; O=ROOT/'exp/s1_array_contrast/assets'
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,x): p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x,indent=2)+'\n')
def download_prefix(name,url,end):
    path=A/(name+'.wav');meta=A/(name+'.json')
    if path.exists(): return path,json.loads(meta.read_text())
    def fetch(a,b):
        req=urllib.request.Request(url,headers={'Range':f'bytes={a}-{b}','User-Agent':'duplex-array-contrast'})
        with urllib.request.urlopen(req,timeout=90) as r:
            assert r.status==206 and r.headers['Content-Range'].startswith(f'bytes {a}-')
            return r.read(),dict(r.headers)
    header,headers=fetch(0,8191);pos=12;fmt=None
    assert header[:4]==b'RIFF'
    while pos+8<=len(header):
        tag=header[pos:pos+4];size=struct.unpack('<I',header[pos+4:pos+8])[0]
        if tag==b'fmt ':fmt=struct.unpack('<HHIIHH',header[pos+8:pos+24])
        if tag==b'data':break
        pos+=8+size+(size%2)
    assert tag==b'data' and fmt[0]==1 and fmt[1]==1 and fmt[2]==16000 and fmt[5]==16,fmt
    raw,h=fetch(pos+8,pos+8+round(end*16000)*2-1);assert h.get('ETag')==headers.get('ETag')
    pcm=np.frombuffer(raw,dtype='<i2');assert len(pcm)==round(end*16000)
    sf.write(path,pcm,16000,subtype='PCM_16')
    record=dict(url=url,etag=h.get('ETag'),samplerate=16000,channels=1,source_frames=size//2,prefix_frames=len(pcm),prefix_sha256=sha(path),source_data_offset=pos+8)
    save(meta,record);return path,record
def main():
    A.mkdir(parents=True,exist_ok=True);O.mkdir(parents=True,exist_ok=True)
    p=json.loads((ROOT/'research/s1_context_pressure/protocol.json').read_text());level=p['levels'][30];q=p['question']
    baseline,rate=sf.read(ROOT/q['input_audio'],dtype='int16');assert rate==16000 and sha(ROOT/q['input_audio'])==q['input_sha256']
    # Keep the packet containing the question start identical, including its short source-audio lead-in.
    # Preserve a 20 ms resampling guard before the common boundary packet as well.
    stop=round((np.floor(q['source_cutoff_seconds']/.48)*.48-.02)*rate);start=round(level['source_start_seconds']*rate)
    target=np.sqrt(np.mean((baseline[start:stop].astype('float64')/32768)**2));rows=[];sources={}
    urls={'distant_01':'https://groups.inf.ed.ac.uk/ami/AMICorpusMirror/amicorpus/TS3006c/audio/TS3006c.Array1-01.wav',
          'beamformed_mdm8':'https://groups.inf.ed.ac.uk/ami/AMICorpusMirror/amicorpus/beamformed/TS3006c/TS3006c_MDM8.wav'}
    for name in ['headset_mix','distant_01','beamformed_mdm8']:
        x=baseline.copy();gain=1.
        if name!='headset_mix':
            source,record=download_prefix(name,urls[name],q['source_cutoff_seconds']);sources[name]=record
            y,sr=sf.read(source,dtype='float64');assert sr==rate
            gain=target/np.sqrt(np.mean(y[start:stop]**2));v=y[:stop]*gain
            assert np.max(abs(v[start:]))<1.,'RMS match would clip; inspect rather than silently limit'
            x[:stop]=np.rint(np.clip(v,-1,1)*32768).clip(-32768,32767).astype('int16')
        path=O/(name+'.wav');sf.write(path,x,rate,subtype='PCM_16');assert np.array_equal(x[stop:],baseline[stop:])
        protocol=copy.deepcopy(p);protocol['question'].update(input_audio=str(path.relative_to(ROOT)),input_sha256=sha(path))
        rows.append(dict(id=name,protocol=protocol,level=level,gain_db=float(20*np.log10(gain)),context_rms=float(np.sqrt(np.mean((x[start:stop].astype('float64')/32768)**2))),context_peak=float(np.max(abs(x[start:stop].astype('float64')/32768)))))
    save(D/'protocol.json',dict(status='prepared_not_run',meeting='TS3006c',level=30,cases=rows,sources=sources,
        matched=dict(source_start_seconds=level['source_start_seconds'],context_seconds=level['context_seconds'],contrast_end_seconds=stop/rate,source_cutoff_seconds=q['source_cutoff_seconds'],request_and_boundary_packet_identical=True,request_gain_db=p['request_level_gain_db'],temperature=0,answer_frames=40,S2=False,history_trimmed=False),
        limitations=['One meeting, one question, one context level and one greedy replay per condition.','Released MDM8 beamforming is offline; full-recording preprocessing may use later-audio statistics. No streaming beamformer claim.','No per-speaker oracle steering or transcript-driven enhancement.','Raw and beamformed distant audio are RMS matched to headset audio over the selected context; gain is recorded.','The final partial source packet shares the original headset signal to keep all question-containing packets identical.']))
    print(json.dumps({'status':'prepared','context_seconds':level['context_seconds'],'cases':[{k:v for k,v in r.items() if k not in ['protocol','level']} for r in rows]}))
if __name__=='__main__':main()
