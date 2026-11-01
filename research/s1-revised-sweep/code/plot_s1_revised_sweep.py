"""Current question-recognition curves and separate generated-response fact scores."""
import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parents[1];D=ROOT/'research/s1_revised_sweep';OUT=ROOT/'site/research/s1-revised-sweep'
COLORS={'headset_mix':'#52647d','distant_01':'#2563a6','beamformed_mdm8':'#7851a9'}
LABELS={'headset_mix':'Headset mix','distant_01':'One distant microphone','beamformed_mdm8':'Eight-microphone beamformed audio'}
def finish(fig,name):
 OUT.mkdir(parents=True,exist_ok=True);fig.savefig(OUT/(name+'.svg'),facecolor='white',metadata={'Date':None});fig.savefig(OUT/(name+'.png'),dpi=180,facecolor='white');plt.close(fig);p=OUT/(name+'.svg');p.write_text('\n'.join(s.rstrip() for s in p.read_text().splitlines())+'\n')
def main():
 d=json.loads((D/'review.json').read_text());assert d['status']=='completed_source_reviewed';rows=d['cases'];old=json.loads((ROOT/'research/s1_array_sweep/review.json').read_text())['cases'];limit=max(1.05,max(r['recognition']['WER'] for r in rows+old if r['WER_valid'])*1.07)
 for name,label in LABELS.items():
  selected=[r for r in rows if r['condition']==name];original=[r for r in old if r['condition']==name];fig,ax=plt.subplots(figsize=(9,4.3),layout='constrained')
  ax.plot([r['context_seconds']/60 for r in original],[r['recognition']['WER'] if r['WER_valid'] else float('nan') for r in original],color='#8e9298',ls=':',lw=1.3,label=label+' original input')
  if name!='headset_mix':
   head=[r for r in rows if r['condition']=='headset_mix'];ax.plot([r['context_seconds']/60 for r in head],[r['recognition']['WER'] if r['WER_valid'] else float('nan') for r in head],color=COLORS['headset_mix'],ls='--',lw=1,alpha=.65,label='Revised headset input')
  ax.plot([r['context_seconds']/60 for r in selected],[r['recognition']['WER'] if r['WER_valid'] else float('nan') for r in selected],color=COLORS[name],lw=1.2,label=label+' revised input')
  for flag,color,label2 in [(True,'#147d53','Meets strict ASR criterion'),(False,'#bd542a','Misses strict ASR criterion')]:
   subset=[r for r in selected if r['WER_valid'] and r['recognition']['recognized']==flag];ax.scatter([r['context_seconds']/60 for r in subset],[r['recognition']['WER'] for r in subset],c=color,s=26,zorder=4,label=label2)
  for i,r in enumerate(r for r in selected if not r['WER_valid']):ax.axvline(r['context_seconds']/60,color='#b43d32',alpha=.3,label='Generation failure; WER unscored' if i==0 else None)
  ax.axhline(.25,color='#777',ls=':',lw=1,label='WER cutoff; key terms also required');ax.axvline(198.91/60,color='#5773a8',ls='--',lw=1,label='All reference evidence included');ax.set(xlabel='Earlier meeting audio (minutes)',ylabel='Question word error rate (lower is better)',ylim=(0,limit),xlim=(-.06,5.22));ax.grid(alpha=.15);ax.legend(loc='upper left',bbox_to_anchor=(1.01,1),fontsize=8);finish(fig,'asr-'+name)
 # Preserve the established response figure semantics while reading only fresh outputs.
 source=(ROOT/'scripts/plot_s1_array_sweep.py').read_text();section=source[source.index('    fig,axes='):source.index("if __name__=='__main__':")]
 scope=dict(rows=rows,plt=plt,finish=finish,COLORS=COLORS,LABELS=LABELS)
 from matplotlib.lines import Line2D
 scope['Line2D']=Line2D
 exec(compile('def response_figure():\n'+section+'\nresponse_figure()','response-score-plot','exec'),scope)
if __name__=='__main__':main()
