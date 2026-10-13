'use strict';
(() => {
  const element=document.getElementById('teacher-trace-data');
  if(!element)return;
  const calls=JSON.parse(element.textContent).calls;
  const chunks=JSON.parse(document.getElementById('pilot-data').textContent).chunks;
  const byCall=new Map(calls.map(c=>[c.index,c])), byChunk=new Map(chunks.map(c=>[c.id,c]));
  const history=document.getElementById('thinking-history'),seed=document.getElementById('thinking-seed');
  const windowSelect=document.getElementById('thinking-window'),focus=document.getElementById('thinking-call');
  const cursor=document.getElementById('thinking-cursor'),svg=document.getElementById('thinking-svg');
  const encoder=new TextEncoder(),bytes=new Map(),ns='http://www.w3.org/2000/svg',xhtml='http://www.w3.org/1999/xhtml';
  let selected={type:'thought',call:50,rate:60,projected:false};
  calls.forEach(c=>{const o=document.createElement('option');o.value=String(c.index);o.textContent='Call '+c.index+' · '+c.at.toFixed(2)+' s · '+c.variant+' / '+c.history_mode;focus.append(o);});
  function node(tag,attrs,text){const el=document.createElementNS(ns,tag);Object.entries(attrs||{}).forEach(([k,v])=>el.setAttribute(k,String(v)));if(text!==undefined)el.textContent=text;return el;}
  function prefix(c,n){if(n<=0)return '';if(!bytes.has(c.index))bytes.set(c.index,encoder.encode(c.generated_text));return new TextDecoder().decode(bytes.get(c.index).subarray(0,c.token_byte_ends[n-1]),{stream:true});}
  function nextTime(c){return c.next_arrival??chunks.find(x=>x.available>c.at+1e-7)?.available??c.at+20;}
  function counts(c,rate,time){const deadline=nextTime(c),capacity=Math.floor(rate*Math.max(0,deadline-c.at-.5)+1e-9);const effective=Math.min(c.output_tokens,capacity);const emitted=Math.min(effective,Math.floor(rate*Math.max(0,time-c.at-.5)+1e-9));return {deadline,capacity,effective,emitted,start:c.at+.5,end:c.at+.5+effective/rate};}
  function rows(){
    if(focus.value!=='sequence'){
      const c=byCall.get(Number(focus.value));
      if(c.stage==='scout')return [10,60,30,100].map(rate=>({rate,calls:[c],projected:true,label:'projected scout '+c.index}));
      const matched=rate=>calls.filter(x=>x.stage==='rate_replay'&&x.at===c.at&&x.seed===c.seed&&x.history_mode===c.history_mode&&x.rate===rate);
      return [{rate:10,calls:matched(10),projected:false,label:'archived output'},{rate:60,calls:matched(60),projected:false,label:'archived output'},...[30,100].map(rate=>({rate,calls:matched(60),projected:true,label:'projected 60-rate trace'}))];
    }
    const matched=rate=>calls.filter(c=>c.stage==='rate_replay'&&c.history_mode===history.value&&c.seed===Number(seed.value)&&c.rate===rate);
    return [{rate:10,calls:matched(10),projected:false,label:'archived output'},{rate:60,calls:matched(60),projected:false,label:'archived output'},...[30,100].map(rate=>({rate,calls:matched(60),projected:true,label:'projected 60-rate trace'}))];
  }
  function openCall(index,prompt=false){const detail=document.getElementById('appendix-call-'+index);detail.open=true;if(prompt)detail.querySelector('.trace-prompt-details').open=true;detail.scrollIntoView({behavior:'auto',block:'start'});}
  function inspect(time){
    const box=document.getElementById('thinking-inspector');box.replaceChildren();
    if(selected.type==='chunk'){
      const c=byChunk.get(selected.chunk),h=document.createElement('h3'),p=document.createElement('p'),clock=document.createElement('p');
      h.textContent=c.id+' · speaker '+c.speaker;p.textContent=c.text;clock.textContent='Speech '+c.start.toFixed(2)+'–'+c.end.toFixed(2)+' s ('+(c.end-c.start).toFixed(2)+' s); transcript available '+c.available.toFixed(2)+' s.';box.append(h,p,clock);return;
    }
    const c=byCall.get(selected.call);if(!c)return;
    const n=counts(c,selected.rate,time),h=document.createElement('h3'),info=document.createElement('p'),text=document.createElement('pre');
    h.textContent='Call '+c.index+' · '+selected.rate+' tokens/s · '+(selected.projected?'fixed-trace projection':'archived budgeted generation');
    info.textContent='Input delivered '+c.at.toFixed(2)+' s; new chunks '+c.new_ids.join(', ')+'. At '+time.toFixed(2)+' s: '+n.emitted+' captured tokens emitted. Before next update '+n.deadline.toFixed(2)+' s: '+n.effective+' of '+c.output_tokens+' captured tokens fit; potential capacity '+n.capacity+'.';
    text.className='trace-prefix';text.textContent=n.emitted?prefix(c,n.emitted):'No thinking tokens emitted at this cursor time.';
    const note=document.createElement('p');note.textContent=n.capacity>c.output_tokens?'The captured output ends at its recorded cap. Additional capacity is unrecorded; no continuation is invented.':'Tokens beyond the next update are hidden in this timing view; the appendix preserves the entire captured output.';
    const link=document.createElement('a');link.href='#appendix-call-'+c.index;link.textContent='Full captured thinking and exact prompt';link.addEventListener('click',event=>{event.preventDefault();openCall(c.index,true);});box.append(h,info,text,note,link);
  }
  function card(parent,x,y,width,height,cls,title,text,onClick){
    const obj=node('foreignObject',{x,y,width:Math.max(3,width),height});const div=document.createElementNS(xhtml,'div');div.className=cls;div.tabIndex=0;div.setAttribute('role','button');div.title=title;
    const label=document.createElementNS(xhtml,'strong');label.textContent=title;const body=document.createElementNS(xhtml,'span');body.textContent=text;div.append(label,body);div.addEventListener('click',onClick);div.addEventListener('keydown',e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();onClick();}});obj.append(div);parent.append(obj);
  }
  function render(){
    const [lo,hi]=windowSelect.value.split(',').map(Number),time=Number(cursor.value),viewRows=rows();
    cursor.min=String(lo);cursor.max=String(hi);if(time<lo||time>hi)cursor.value=String((lo+hi)/2);
    const now=Number(cursor.value),x=t=>180+(t-lo)/(hi-lo)*1380;
    document.getElementById('thinking-cursor-label').textContent=now.toFixed(2)+' s';
    document.getElementById('thinking-method').textContent=focus.value!=='sequence'&&byCall.get(Number(focus.value)).stage==='scout'?'Single-scout projection: all rows display prefixes of the same captured output under different assumed rates. The scout was not generated as a timed causal replay.':'10/60 rows are actual separately budgeted generations with simulated uniform emission times. 30/100 rows are projections of recorded 60-rate outputs; their prompts retain original 60-rate history, so these are not new causal histories.';
    svg.replaceChildren(node('title',{id:'thinking-title'},'Transcript spans and actual captured thinking aligned to time'));
    for(let i=0;i<=5;i++){const t=lo+(hi-lo)*i/5;svg.append(node('line',{x1:x(t),x2:x(t),y1:25,y2:635,class:'axis'}));svg.append(node('text',{x:x(t)-16,y:661},t.toFixed(1)+' s'));}
    const transcriptY={A:35,B:115,C:195};
    Object.entries(transcriptY).forEach(([s,y])=>svg.append(node('text',{x:8,y:y+30},'Transcript '+s)));
    chunks.filter(c=>c.end>=lo&&c.start<=hi).forEach(c=>{
      const xx=x(Math.max(lo,c.start)),ww=x(Math.min(hi,c.end))-xx;
      card(svg,xx,transcriptY[c.speaker],ww,68,'trace-transcript-card speaker-'+c.speaker,c.id+' · '+(c.end-c.start).toFixed(2)+' s',c.text,()=>{selected={type:'chunk',chunk:c.id};inspect(Number(cursor.value));});
    });
    const stats=document.getElementById('thinking-counts');stats.replaceChildren();
    viewRows.forEach((row,i)=>{
      const y=285+i*90;svg.append(node('text',{x:8,y:y+22},'S2 '+row.rate+' tokens/s'));svg.append(node('text',{x:8,y:y+43,class:'trace-row-kind'},row.projected?'Projection':'Archived output'));
      let emitted=0,fit=0,captured=0,displayed=0;
      row.calls.forEach(c=>{
        const n=counts(c,row.rate,now);if(n.deadline<lo||n.start>hi)return;displayed++;emitted+=n.emitted;fit+=n.effective;captured+=c.output_tokens;
        const start=Math.max(lo,n.start),end=Math.min(hi,n.end);if(end<=start)return;
        svg.append(node('rect',{x:x(start),y,width:x(end)-x(start),height:72,class:'trace-capture '+(row.projected?'projected':'archived'),rx:5,'data-call':c.index,'data-rate':row.rate,'data-emitted':n.emitted,'data-fits':n.effective}));
        const progress=Math.min(end,n.start+n.emitted/row.rate);if(progress>start)svg.append(node('rect',{x:x(start),y,width:x(progress)-x(start),height:72,class:'trace-emitted',rx:5}));
        const body=n.emitted?prefix(c,n.emitted):'Not emitted at cursor.';
        const inputLabel=c.new_ids.length===1?c.new_ids[0]:c.new_ids[0]+'…'+c.new_ids.at(-1);
        card(svg,x(start)+2,y+2,x(end)-x(start)-4,68,'trace-thinking-card','Call '+c.index+' ← '+inputLabel+' · '+n.emitted+'/'+n.effective+' tokens',body,()=>{selected={type:'thought',call:c.index,rate:row.rate,projected:row.projected};inspect(Number(cursor.value));});
        const stride=Math.max(1,Math.ceil(row.rate*(hi-lo)/1380*3));
        for(let j=1;j<=n.effective;j+=stride){
          const when=n.start+j/row.rate;if(when<lo||when>hi)continue;
          const tick=node('line',{x1:x(when),x2:x(when),y1:y+72,y2:y+79,class:'trace-token-tick','data-token':j,'data-token-id':c.generated_token_ids[j-1]});
          tick.append(node('title',{},'Call '+c.index+' token '+j+' · ID '+c.generated_token_ids[j-1]+' · emission '+when.toFixed(3)+' s'));svg.append(tick);
          if(1380/(hi-lo)/row.rate>=20&&j<=n.emitted){const word=prefix(c,j).slice(prefix(c,j-1).length);svg.append(node('text',{x:x(when-1/row.rate)+2,y:y+85,class:'trace-token-label'},word.replace(/\n/g,'↵')));}
        }
        svg.append(node('line',{x1:x(c.at),x2:x(c.at),y1:270,y2:y,class:'trace-delivery-line'}));
      });
      const tile=document.createElement('div');tile.className='trace-count';tile.dataset.rate=String(row.rate);tile.dataset.projected=String(row.projected);tile.dataset.emitted=String(emitted);tile.dataset.fits=String(fit);tile.dataset.captured=String(captured);
      tile.textContent=row.rate+' tokens/s · '+(row.projected?'projection':'archived')+': '+emitted+' emitted at cursor; '+fit+'/'+captured+' captured tokens fit before updates'+(displayed?'':'; no recorded calls in this view')+'.';stats.append(tile);
    });
    svg.append(node('line',{x1:x(now),x2:x(now),y1:20,y2:639,class:'trace-time-cursor'}));inspect(now);
  }
  function focusCall(index){
    const c=byCall.get(index);focus.value=String(index);history.value=c.history_mode;seed.value=String(c.seed);
    const incoming=c.new_ids.map(id=>byChunk.get(id)),lo=Math.floor(Math.max(0,Math.min(c.at-5,...incoming.map(x=>x.start))-1)*100)/100,hi=Math.ceil((nextTime(c)+3)*100)/100;
    let option=windowSelect.querySelector('option[data-custom]');if(!option){option=document.createElement('option');option.dataset.custom='true';windowSelect.append(option);}option.value=lo+','+hi;option.textContent='Call '+index+' input and next-update window';windowSelect.value=option.value;cursor.min=String(lo);cursor.max=String(hi);cursor.value=String(Math.min(hi,c.at+5));
    selected={type:'thought',call:index,rate:c.rate||60,projected:c.stage==='scout'};render();
  }
  cursor.addEventListener('input',render);windowSelect.addEventListener('change',()=>{const [a,b]=windowSelect.value.split(',').map(Number);cursor.value=String((a+b)/2);render();});
  [history,seed].forEach(el=>el.addEventListener('change',()=>{focus.value='sequence';const c=calls.find(x=>x.stage==='rate_replay'&&x.rate===60&&x.seed===Number(seed.value)&&x.history_mode===history.value);selected={type:'thought',call:c.index,rate:60,projected:false};render();}));
  focus.addEventListener('change',()=>{if(focus.value==='sequence')render();else focusCall(Number(focus.value));});
  document.querySelectorAll('a.trace-link').forEach(link=>link.addEventListener('click',e=>{e.preventDefault();openCall(Number(link.hash.replace('#appendix-call-','')),true);}));
  document.querySelectorAll('a.trace-focus-link').forEach(link=>link.addEventListener('click',e=>{e.preventDefault();focusCall(Number(link.closest('.trace-record').dataset.call));document.getElementById('thinking-timeline').scrollIntoView({block:'start'});}));
  const filter=document.getElementById('appendix-filter'),records=[...document.querySelectorAll('.trace-record')];
  filter.addEventListener('input',()=>{const query=filter.value.trim().toLowerCase();records.forEach(r=>r.hidden=!r.dataset.search.toLowerCase().includes(query));document.getElementById('appendix-count').textContent=records.filter(r=>!r.hidden).length+' of 64 calls';});
  document.getElementById('appendix-open-all').addEventListener('click',()=>records.filter(r=>!r.hidden).forEach(r=>r.open=true));
  document.getElementById('appendix-open-prompts').addEventListener('click',()=>records.filter(r=>!r.hidden).forEach(r=>{r.open=true;r.querySelector('.trace-prompt-details').open=true;}));
  document.getElementById('appendix-close-all').addEventListener('click',()=>records.forEach(r=>r.open=false));
  document.querySelectorAll('audio[data-source-start]').forEach(audio=>audio.addEventListener('timeupdate',()=>{const at=Number(audio.dataset.sourceStart)+audio.currentTime,[lo,hi]=windowSelect.value.split(',').map(Number);if(at>=lo&&at<=hi){cursor.value=String(at);render();}}));
  render();
})();
