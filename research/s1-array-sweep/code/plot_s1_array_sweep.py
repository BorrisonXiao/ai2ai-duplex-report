"""Generate two ASR curves and a distinct LLM response-content figure."""
import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
ROOT=Path(__file__).resolve().parents[1];D=ROOT/'research/s1_array_sweep';OUT=ROOT/'site/research/s1-array-sweep'
COLORS={'headset_mix':'#64748b','distant_01':'#2563a6','beamformed_mdm8':'#7851a9'}
LABELS={'headset_mix':'Headset mix','distant_01':'One distant microphone','beamformed_mdm8':'Eight-microphone beamformed audio'}
def finish(fig,name):
    OUT.mkdir(parents=True,exist_ok=True);fig.savefig(OUT/(name+'.svg'),facecolor='white',metadata={'Date':None});fig.savefig(OUT/(name+'.png'),dpi=180,facecolor='white');plt.close(fig)
    p=OUT/(name+'.svg');p.write_text('\n'.join(s.rstrip() for s in p.read_text().splitlines())+'\n')
def main():
    d=json.loads((D/'review.json').read_text());assert d['status']=='completed_source_reviewed';rows=d['cases'];head=[r for r in rows if r['condition']=='headset_mix'];maximum=max(r['recognition']['WER'] for r in rows if r['WER_valid']);limit=max(1.05,maximum*1.07)
    for condition,name in [('distant_01','asr-distant'),('beamformed_mdm8','asr-beamformed')]:
        selected=[r for r in rows if r['condition']==condition];fig,ax=plt.subplots(figsize=(9,4.3),layout='constrained')
        ax.plot([r['context_seconds']/60 for r in head],[r['recognition']['WER'] for r in head],color=COLORS['headset_mix'],ls='--',lw=1.2,alpha=.7,label='Headset mix (original Figure 1)')
        ax.plot([r['context_seconds']/60 for r in selected],[r['recognition']['WER'] if r['WER_valid'] else float('nan') for r in selected],color=COLORS[condition],lw=1.2,label=LABELS[condition])
        for flag,color,label in [(True,'#147d53','Meets strict ASR criterion'),(False,'#bd542a','Misses strict ASR criterion')]:
            subset=[r for r in selected if r['WER_valid'] and r['recognition']['recognized']==flag];ax.scatter([r['context_seconds']/60 for r in subset],[r['recognition']['WER'] for r in subset],c=color,s=29,label=label,zorder=4)
        failed=[r for r in selected if not r['WER_valid']]
        for i,r in enumerate(failed):
            x=r['context_seconds']/60;ax.axvline(x,color='#b43d32',lw=2,alpha=.25,label='Generation failure: no WER' if i==0 else None);ax.text(x,.96-.16*(i%2),'N/A',transform=ax.get_xaxis_transform(),rotation=90,ha='center',va='top',fontsize=7,color='#9c332b')
        ax.axhline(.25,color='#777',ls=':',lw=1,label='WER cutoff (key terms also required)');ax.axvline(198.91/60,color='#5773a8',ls='--',lw=1,label='All reference evidence included')
        ax.set(xlabel='Earlier meeting audio (minutes)',ylabel='Question word error rate (lower is better)',ylim=(0,limit),xlim=(-.06,5.22));ax.grid(alpha=.15);ax.legend(fontsize=8,loc='upper left',bbox_to_anchor=(1.01,1));finish(fig,name)
    fig,axes=plt.subplots(3,1,figsize=(9,7.2),sharex=True,sharey=True,layout='constrained')
    for ax,condition in zip(axes,['headset_mix','distant_01','beamformed_mdm8']):
        selected=[r for r in rows if r['condition']==condition and r['source_evidence_fully_available']];ax.axvspan(0,198.91/60,color='#e9e7e1',alpha=.75);ax.axvline(198.91/60,color='#5773a8',ls='--',lw=1)
        ax.plot([r['context_seconds']/60 for r in selected],[r.get('judge',{}).get('fact_score') for r in selected],marker='o',ms=4,lw=1,color=COLORS[condition],label='LLM fact score on response ASR')
        errors=[r for r in selected if r.get('judge',{}).get('material_error') and r['judge']['fact_score'] is not None];ax.scatter([r['context_seconds']/60 for r in errors],[r['judge']['fact_score'] for r in errors],marker='x',s=65,lw=1.6,color='#b43d32',zorder=5,label='LLM: unsupported/contradicted claim')
        audit_errors=[r for r in selected if r.get('source_audit',{}).get('material_error') and not r.get('judge',{}).get('material_error') and r.get('judge',{}).get('fact_score') is not None];ax.scatter([r['context_seconds']/60 for r in audit_errors],[r['judge']['fact_score'] for r in audit_errors],marker='s',facecolor='none',edgecolor='#b43d32',s=62,lw=1.2,zorder=5,label='Additional Codex unsupported claim')
        corrected=[r for r in selected if r.get('source_audit',{}).get('fact_score') is not None and r['source_audit']['fact_score']!=r.get('judge',{}).get('fact_score')];ax.scatter([r['context_seconds']/60 for r in corrected],[r['source_audit']['fact_score'] for r in corrected],marker='D',facecolor='none',edgecolor='#b07000',s=55,zorder=6,label='Codex source-audit correction')
        for r in selected:
            if not r['response_valid']:ax.axvline(r['context_seconds']/60,color='#b43d32',alpha=.25,lw=2)
        ax.set_title(LABELS[condition],loc='left',fontsize=11);ax.set(ylim=(-.08,1.08),yticks=[0,.5,1],yticklabels=['0 / 2','1 / 2','2 / 2'],ylabel='Facts stated',xlim=(-.06,5.22));ax.grid(alpha=.15)
        ax.text(.15,.85,'Reference evidence incomplete\nNo correctness score',fontsize=9,color='#666')
    legend=[Line2D([0],[0],color=COLORS['headset_mix'],marker='o',lw=1,label='LLM fact score on response ASR'),Line2D([0],[0],color='#b43d32',marker='x',linestyle='none',label='LLM: unsupported/contradicted claim'),Line2D([0],[0],color='#b43d32',marker='s',markerfacecolor='none',linestyle='none',label='Additional Codex unsupported claim'),Line2D([0],[0],color='#b07000',marker='D',markerfacecolor='none',linestyle='none',label='Codex source-audit correction')]
    axes[0].legend(handles=legend,loc='upper left',bbox_to_anchor=(1.01,1),fontsize=8);axes[-1].set_xlabel('Earlier meeting audio (minutes)');finish(fig,'response-content')
if __name__=='__main__':main()
