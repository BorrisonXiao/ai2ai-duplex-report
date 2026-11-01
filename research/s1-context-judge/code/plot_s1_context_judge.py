"""Continuous question WER and separate context-aware response-quality dimensions."""
import argparse,json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parents[1];P=ROOT/'site/research/s1-context-judge'
COLORS={'headset_mix':'#52647d','distant_01':'#2563a6','beamformed_mdm8':'#7851a9'}
LABELS={'headset_mix':'Headset mix','distant_01':'One distant microphone','beamformed_mdm8':'Eight-microphone beamformed audio'}
def finish(fig,name):
 P.mkdir(parents=True,exist_ok=True);fig.savefig(P/(name+'.svg'),facecolor='white',metadata={'Date':None});fig.savefig(P/(name+'.png'),facecolor='white',dpi=180);plt.close(fig);q=P/(name+'.svg');q.write_text('\n'.join(s.rstrip() for s in q.read_text().splitlines())+'\n')
def main():
 p=argparse.ArgumentParser();p.add_argument('--asr-only',action='store_true');args=p.parse_args();old=json.loads((ROOT/'research/s1_revised_sweep/review.json').read_text());head=[r for r in old['cases'] if r['condition']=='headset_mix'];limit=max(1.05,max(r['recognition']['WER'] for r in old['cases'] if r['WER_valid'])*1.07)
 for name,label in LABELS.items():
  rows=[r for r in old['cases'] if r['condition']==name];fig,ax=plt.subplots(figsize=(9,4.3),layout='constrained')
  if name!='headset_mix':ax.plot([r['context_seconds']/60 for r in head],[r['recognition']['WER'] for r in head],color=COLORS['headset_mix'],ls='--',lw=1.2,alpha=.8,label='Headset baseline (Figure 1)')
  ax.plot([r['context_seconds']/60 for r in rows],[r['recognition']['WER'] if r['WER_valid'] else float('nan') for r in rows],color=COLORS[name],marker='o',ms=4,lw=1.4,label=label)
  for i,r in enumerate(r for r in rows if not r['WER_valid']):ax.axvline(r['context_seconds']/60,color='#bd542a',alpha=.35,lw=1,label='Generation stopped; WER unscored' if i==0 else None)
  ax.set(xlabel='Earlier meeting audio (minutes)',ylabel='Question word error rate (lower is better)',ylim=(-.03,limit),xlim=(-.06,5.22));ax.grid(alpha=.15);ax.legend(loc='upper left',bbox_to_anchor=(1.01,1),fontsize=9);finish(fig,'asr-'+name)
 if args.asr_only:return
 d=json.loads((ROOT/'research/s1_context_judge/review.json').read_text());assert d['status']=='completed_content_reviewed';rows=d['cases'];fig,axes=plt.subplots(3,1,figsize=(9,8.8),sharex=True,layout='constrained')
 for ax,key,label in zip(axes,['relevance','support','adequacy'],['Question relevance','Factual support','Answer adequacy']):
  ax.axvspan(0,166.4/60,color='#e9e7e1',alpha=.7);ax.axvspan(166.4/60,193.17/60,color='#f4e6c7',alpha=.65);ax.axvline(193.17/60,color='#777',ls=':',lw=1)
  for name,marker in zip(LABELS,['o','s','^']):
   by={r['index']:r for r in rows if r['condition']==name};xs=[r['context_seconds']/60 for r in old['cases'] if r['condition']==name];ys=[by[i]['quality']['scores'][key] if i in by and by[i]['quality']['valid'] and by[i]['quality']['scores'][key] is not None else float('nan') for i in range(41)]
   ax.plot(xs,ys,color=COLORS[name],marker=marker,ms=3.8,lw=1,alpha=.8,label=LABELS[name])
  ax.set_title(label,loc='left',fontsize=11);ax.set(ylim=(.7,5.3),yticks=[1,2,3,4,5],ylabel='Judge rating (higher is better)',xlim=(-.06,5.22));ax.grid(alpha=.15)
 axes[0].legend(loc='upper left',bbox_to_anchor=(1.01,1),fontsize=9);axes[-1].set_xlabel('Earlier meeting audio (minutes)');finish(fig,'response-quality')
if __name__=='__main__':main()
