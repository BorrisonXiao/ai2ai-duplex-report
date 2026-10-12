'use strict';
(() => {
  const source=document.getElementById('pilot-data');
  if (!source) return;
  const d=JSON.parse(source.textContent), chunks=d.chunks;
  const rate=document.getElementById('pilot-rate'), overhead=document.getElementById('pilot-overhead');
  const policy=document.getElementById('pilot-policy'), view=document.getElementById('pilot-window');
  const selection=document.getElementById('pilot-chunk'), svg=document.getElementById('pilot-svg');
  const ns='http://www.w3.org/2000/svg';
  function node(tag,attrs,text) { const el=document.createElementNS(ns,tag); Object.entries(attrs||{}).forEach(([k,v])=>el.setAttribute(k,String(v))); if(text!==undefined) el.textContent=text; return el; }
  function median(a) { const b=[...a].sort((x,y)=>x-y), n=b.length; return n%2?b[(n-1)/2]:(b[n/2-1]+b[n/2])/2; }
  function groups() {
    const period=Number(policy.value), result=[];
    chunks.forEach(c=> { const at=period?Math.ceil(c.available/period)*period:c.available; const last=result.at(-1); if(last && Math.abs(last.at-at)<1e-8) last.ids.push(c.id); else result.push({at,ids:[c.id]}); });
    return result;
  }
  function choose() {
    const c=chunks.find(x=>x.id===selection.value), g=groups();
    const i=g.findIndex(x=>x.ids.includes(c.id)), current=g[i], next=g[i+1];
    const budget=next?Math.floor(Number(rate.value)*Math.max(0,next.at-current.at-Number(overhead.value))+1e-9):null;
    const box=document.getElementById('pilot-selection'); box.replaceChildren();
    const label=document.createElement('strong'); label.textContent=c.id+' · speaker '+c.speaker+' · audio '+c.start.toFixed(2)+'–'+c.end.toFixed(2)+' s';
    const text=document.createElement('p'); text.textContent=c.text;
    const clock=document.createElement('p'); clock.textContent='Annotation available '+c.available.toFixed(2)+' s; policy delivery '+current.at.toFixed(2)+' s. '+(next?'Next delivery '+next.at.toFixed(2)+' s; potential budget '+budget+' output tokens.':'Final update: no unbounded end-of-recording budget is assumed.');
    box.append(label,text,clock);
  }
  function render() {
    const [lo,hi]=view.value.split(',').map(Number), g=groups();
    const budgets=g.slice(0,-1).map((a,i)=>Math.floor(Number(rate.value)*Math.max(0,g[i+1].at-a.at-Number(overhead.value))+1e-9));
    document.getElementById('pilot-stat').textContent=g.length+' delivered updates; median potential budget '+median(budgets)+' tokens; '+(100*budgets.filter(x=>x===0).length/budgets.length).toFixed(1)+'% have zero budget. Counterfactual rates/setup; teacher replay is a separate recorded experiment.';
    svg.replaceChildren(node('title',{id:'pilot-svg-title'},'Real speaker chunks and assumed token budgets'));
    const x=t=>110+(t-lo)/(hi-lo)*960;
    const y={A:35,B:80,C:125};
    Object.entries(y).forEach(([s,pos])=> {svg.append(node('text',{x:10,y:pos+18},'Speaker '+s));svg.append(node('line',{x1:110,x2:1070,y1:pos+28,y2:pos+28,class:'axis'}));});
    chunks.filter(c=>c.end>=lo&&c.start<=hi).forEach(c=> {
      const el=node('rect',{x:x(Math.max(lo,c.start)),y:y[c.speaker],width:Math.max(2,x(Math.min(hi,c.end))-x(Math.max(lo,c.start))),height:24,rx:2,class:'chunk speaker-'+c.speaker,tabindex:0,role:'button','aria-label':c.id+' speaker '+c.speaker});
      el.append(node('title',{},c.id+' '+c.speaker+': '+c.text));
      function pick(){selection.value=c.id;choose();} el.addEventListener('click',pick);el.addEventListener('keydown',ev=>{if(ev.key==='Enter'||ev.key===' '){ev.preventDefault();pick();}});svg.append(el);
    });
    svg.append(node('text',{x:10,y:188},'Budget'));
    g.slice(0,-1).forEach((a,i)=> {const start=a.at+Number(overhead.value), end=g[i+1].at; if(end<lo||start>hi||end<=start)return; const b=Math.floor(Number(rate.value)*(end-start)+1e-9); const el=node('rect',{x:x(Math.max(lo,start)),y:170,width:Math.max(1,x(Math.min(hi,end))-x(Math.max(lo,start))),height:25,rx:2,class:'budget-band'});el.append(node('title',{},a.at.toFixed(2)+' s delivery; capacity '+b+' tokens'));svg.append(el);if((hi-lo)<120 && (end-start)>4) svg.append(node('text',{x:x(Math.max(lo,start))+3,y:187},String(b)));});
    for(let j=0;j<=4;j++){const at=lo+(hi-lo)*j/4;svg.append(node('line',{x1:x(at),x2:x(at),y1:25,y2:202,class:'axis'}));svg.append(node('text',{x:x(at)-12,y:226},at.toFixed(0)+' s'));}
    const old=selection.value; selection.replaceChildren(...chunks.filter(c=>c.end>=lo&&c.start<=hi).map(c=> {const el=document.createElement('option');el.value=c.id;el.textContent=c.id+' · '+c.speaker+' · '+c.available.toFixed(2)+' s';return el;}));
    if([...selection.options].some(o=>o.value===old)) selection.value=old;
    choose();
  }
  [rate,overhead,policy,view].forEach(el=>el.addEventListener('change',render));selection.addEventListener('change',choose);render();
  document.querySelectorAll('audio[data-source-start]').forEach(audio=>audio.addEventListener('timeupdate',()=> {
    const at=Number(audio.dataset.sourceStart)+audio.currentTime;
    const [lo,hi]=view.value.split(',').map(Number);
    svg.querySelector('#source-playback-cursor')?.remove();
    if(at>=lo&&at<=hi)svg.append(node('line',{id:'source-playback-cursor',x1:110+(at-lo)/(hi-lo)*960,x2:110+(at-lo)/(hi-lo)*960,y1:20,y2:200,stroke:'currentColor','stroke-width':2}));
  }));
})();
