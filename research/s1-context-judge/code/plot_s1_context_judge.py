"""Continuous question WER and separate context-aware response-quality dimensions."""
import argparse,json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap, BoundaryNorm
from matplotlib.patches import Rectangle
from matplotlib.cm import ScalarMappable
ROOT=Path(__file__).resolve().parents[1];P=ROOT/'site/research/s1-context-judge'
COLORS={'headset_mix':'#52647d','distant_01':'#2563a6','beamformed_mdm8':'#7851a9'}
LABELS={'headset_mix':'Headset mix','distant_01':'One distant microphone','beamformed_mdm8':'Eight-microphone beamformed audio'}
def finish(fig,name):
 P.mkdir(parents=True,exist_ok=True);fig.savefig(P/(name+'.svg'),facecolor='white',metadata={'Date':None});fig.savefig(P/(name+'.png'),facecolor='white',dpi=180);plt.close(fig);q=P/(name+'.svg');q.write_text('\n'.join(s.rstrip() for s in q.read_text().splitlines())+'\n')
def main():
 p=argparse.ArgumentParser();p.add_argument('--asr-only',action='store_true');p.add_argument('--quality-only',action='store_true');args=p.parse_args();old=json.loads((ROOT/'research/s1_revised_sweep/review.json').read_text());head=[r for r in old['cases'] if r['condition']=='headset_mix'];limit=max(1.05,max(r['recognition']['WER'] for r in old['cases'] if r['WER_valid'])*1.07)
 if not args.quality_only:
  for name,label in LABELS.items():
   rows=[r for r in old['cases'] if r['condition']==name];fig,ax=plt.subplots(figsize=(9,4.3),layout='constrained')
   if name!='headset_mix':ax.plot([r['context_seconds']/60 for r in head],[r['recognition']['WER'] for r in head],color=COLORS['headset_mix'],ls='--',lw=1.2,alpha=.8,label='Headset baseline (Figure 1)')
   ax.plot([r['context_seconds']/60 for r in rows],[r['recognition']['WER'] if r['WER_valid'] else float('nan') for r in rows],color=COLORS[name],marker='o',ms=4,lw=1.4,label=label)
   for i,r in enumerate(r for r in rows if not r['WER_valid']):ax.axvline(r['context_seconds']/60,color='#bd542a',alpha=.35,lw=1,label='Generation stopped; WER unscored' if i==0 else None)
   ax.set(xlabel='Earlier meeting audio (minutes)',ylabel='Question word error rate (lower is better)',ylim=(-.03,limit),xlim=(-.06,5.22));ax.grid(alpha=.15);ax.legend(loc='upper left',bbox_to_anchor=(1.01,1),fontsize=9);finish(fig,'asr-'+name)
 if args.asr_only:return
 d=json.loads((ROOT/'research/s1_context_judge/review.json').read_text());assert d['status']=='completed_content_reviewed'
 rows={r['id']:r for r in d['cases']};durations={r['index']:r['context_seconds']/60 for r in head}
 cmap=ListedColormap(['#f0f5fa','#c5dcec','#87b9d8','#458bb9','#185982']);norm=BoundaryNorm([.5,1.5,2.5,3.5,4.5,5.5],cmap.N)
 fig=plt.figure(figsize=(12.6,6.5));grid=fig.add_gridspec(4,1,height_ratios=[.34,1,1,1],left=.17,right=.885,top=.90,bottom=.18,hspace=.54)
 evidence=fig.add_subplot(grid[0]);evidence.set(xlim=(-.5,46.7),ylim=(0,1));evidence.axis('off')
 for start,width,color,label in [(-.5,28,'#e7e5e1','No earlier folder-status evidence'),(27.5,1,'#f2d68b','P'),(28.5,12,'#cee0d6','Full evidence')]:
  evidence.add_patch(Rectangle((start,0),width,1,facecolor=color,edgecolor='white'));evidence.text(start+width/2,.5,label,ha='center',va='center',fontsize=9 if width>1 else 8)
 evidence.set_title('Available folder-status evidence  (P = partial)',loc='left',fontsize=10,pad=9)
 names=list(LABELS);row_labels=['Headset mix','Distant microphone','Beamformed (8 mics)'];axes=[]
 for panel,(key,label) in enumerate([('relevance','Question relevance'),('support','Factual support'),('adequacy','Answer adequacy')]):
  ax=fig.add_subplot(grid[panel+1]);axes.append(ax)
  for y,name in enumerate(names):
   scored=[]
   for i in range(41):
    c=rows.get(name+'-L'+str(i).zfill(2));value=c['quality']['scores'][key] if c and c['quality']['valid'] else None
    state='score-'+str(value) if value is not None else 'na' if c and c['quality']['valid'] else 'failed'
    color=cmap(norm(value)) if value is not None else '#d9d9d9' if state=='na' else '#fff7e8'
    patch=Rectangle((i-.5,y-.5),1,1,facecolor=color,edgecolor='white',linewidth=.8,hatch='////' if state=='failed' else None);patch.set_gid('quality-'+key+'-'+name+'-L'+str(i).zfill(2)+'-'+state);ax.add_patch(patch)
    ax.text(i,y,str(value) if value is not None else '–' if state=='na' else '×',ha='center',va='center',fontsize=7.5,color='white' if value is not None and value>=4 else '#273b4a')
    if value is not None:scored.append(value)
   ax.text(42.7,y,format(sum(scored)/len(scored),'.2f')+' / '+str(len(scored)) if scored else 'N/A / 0',ha='center',va='center',fontsize=9)
  ax.text(42.7,-.86,'Mean / count',ha='center',va='center',fontsize=8.5,color='#4b5963')
  ax.axvline(28.5,color='#657b70',lw=1.1,ls=':');ax.set(xlim=(-.5,46.7),ylim=(2.5,-.5),yticks=[0,1,2],yticklabels=row_labels);ax.set_title(label,loc='left',fontsize=11,pad=14,fontweight='bold');ax.tick_params(axis='y',length=0,pad=8,labelsize=10)
  for spine in ax.spines.values():spine.set_visible(False)
  if panel<2:ax.set_xticks([])
  else:
   ticks=[0,6,12,18,24,29,35,39,40];ax.set_xticks(ticks,[format(durations[i],'.2f') for i in ticks],rotation=45,ha='right',fontsize=8.5);ax.tick_params(axis='x',length=3,color='#a4adb5');ax.set_xlabel('Earlier audio (minutes) — one equally spaced column per tested history',fontsize=10,labelpad=9)
 bar=fig.colorbar(ScalarMappable(norm=norm,cmap=cmap),cax=fig.add_axes([.92,.20,.016,.59]),ticks=[1,2,3,4,5]);bar.set_label('Local judge rating (higher is better)',fontsize=10,labelpad=9);bar.ax.tick_params(labelsize=9)
 fig.text(.17,.035,'–  Judge support N/A     ×  Generation failed     Counts exclude N/A and failures. No interpolation or smoothing.',fontsize=9,color='#42515d');finish(fig,'response-quality')
if __name__=='__main__':main()
