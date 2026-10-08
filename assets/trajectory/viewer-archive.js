/* Offline trajectory inspection: no uploads, remote assets or live inference. */
(() => {
  'use strict';
  const $ = id => document.getElementById(id);
  const demo = JSON.parse($('demo-trace').textContent);
  const example = JSON.parse($('recorded-example').textContent);
  const svgNS = 'http://www.w3.org/2000/svg';
  const player = $('clip-player');
  const defaultAuditionScope = $('audition-scope').textContent;
  let trace, events = [], visible = [], media = [], selected = null, clip = null;
  let minimum = 0, maximum = 10, cursor = 0, playing = false, lastFrame = 0;
  let width = 1000, plotLeft = 215, plotRight = 980, height = 550;
  const fmt = value => Number(value).toFixed(3);

  function svg(tag, attributes, parent, text) {
    const node = document.createElementNS(svgNS, tag);
    for (const [key, value] of Object.entries(attributes || {})) node.setAttribute(key, value);
    if (text !== undefined) node.textContent = text;
    if (parent) parent.appendChild(node);
    return node;
  }
  function clear(node) { node.replaceChildren(); }
  function finite(value) { return typeof value === 'number' && Number.isFinite(value); }
  function validate(data) {
    if (!data || data.schema !== 'duplex-trajectory/v1') throw new Error('Expected duplex-trajectory/v1 JSON.');
    if (!['measured', 'illustrative', 'summary_only'].includes(data.evidence)) throw new Error('Missing or invalid evidence label.');
    for (const key of ['lanes', 'events', 'media']) if (!Array.isArray(data[key])) throw new Error(`${key} must be an array.`);
    if (data.events.length > 50000) throw new Error('Trace exceeds the 50,000 event limit.');
    const laneIDs = new Set(data.lanes.map(lane => lane.id));
    const eventIDs = new Set();
    const mediaIDs = new Set();
    if (laneIDs.size !== data.lanes.length) throw new Error('Duplicate lane IDs.');
    for (const lane of data.lanes) if (typeof lane.id !== 'string' || typeof lane.label !== 'string') throw new Error('Invalid lane.');
    for (const event of data.events) {
      if (typeof event.id !== 'string' || eventIDs.has(event.id)) throw new Error('Invalid or duplicate event ID.');
      eventIDs.add(event.id);
      if (!laneIDs.has(event.lane) || !finite(event.start) || !finite(event.end) || event.start < 0 || event.end < event.start) throw new Error('Invalid event lane or time bounds.');
      if (typeof event.label !== 'string' || typeof event.kind !== 'string') throw new Error('Invalid event label or kind.');
      if (event.details != null && (typeof event.details !== 'object' || Array.isArray(event.details))) throw new Error('Event details must be an object.');
    }
    for (const item of data.media) {
      if (typeof item.id !== 'string' || mediaIDs.has(item.id)) throw new Error('Invalid or duplicate media ID.');
      mediaIDs.add(item.id);
      if (typeof item.data_uri !== 'string' || !/^data:audio\/(wav|x-wav|flac);base64,[A-Za-z0-9+/=]+$/.test(item.data_uri)) throw new Error('Audio must be embedded WAV or lossless FLAC; external URLs are unsupported.');
      if (item.anchor != null && (!finite(item.anchor) || item.anchor < 0)) throw new Error('Invalid audio anchor.');
      if (item.duration != null && (!finite(item.duration) || item.duration < 0)) throw new Error('Invalid audio duration.');
      if (item.waveform && (!Array.isArray(item.waveform) || item.waveform.length > 5000 || item.waveform.some(v => !finite(v) || v < 0 || v > 1.001))) throw new Error('Invalid waveform envelope.');
    }
    if (data.limitations && !Array.isArray(data.limitations)) throw new Error('Limitations must be an array.');
    return data;
  }

  function pause() {
    playing = false;
    $('play').textContent = 'Replay timing';
  }
  function load(data, source) {
    validate(data); // Reject invalid input before replacing the current trace.
    pause(); player.pause(); selected = null;
    trace = data;
    events = [...trace.events].sort((a, b) => a.start - b.start || a.end - b.end);
    media = trace.media;
    $('run-title').textContent = trace.title || 'Imported trajectory';
    $('run-metadata').textContent = JSON.stringify(trace.metadata || {}, null, 2);
    $('zoom').value = trace.metadata?.recommended_zoom || (trace.metadata?.content_blocks ? (trace.events.filter(e=>e.lane==='thinker'&&e.kind==='request').length>10?'5':'3') : '1');
    $('audition-scope').textContent = trace.metadata?.audition_description || defaultAuditionScope;
    $('clock-note').textContent = trace.metadata?.clock || 'Client seconds since driver start; see trace metadata.';
    $('warmup').disabled = !trace.lanes.some(lane => lane.id === 'startup');
    if ($('warmup').disabled) $('warmup').checked = false;
    const labels = {illustrative: 'Illustrative demo', measured: 'Measured client events', summary_only: 'Summary only · no aligned event timing'};
    const descriptions = {
      illustrative: 'Invented timings and synthetic tones demonstrate the viewer. These are not local inference measurements.',
      measured: 'Request spans and stream observations use the driver’s shared monotonic clock. Audio audition is a browser replay; GPU kernel execution and acoustic word timing are not measured.',
      summary_only: 'This archive has no captured event timestamps. Audio can be auditioned, but a timeline cannot be reconstructed from its total duration.'
    };
    clear($('evidence-note'));
    const strong = document.createElement('strong'); strong.textContent = labels[trace.evidence];
    const p = document.createElement('p'); p.textContent = descriptions[trace.evidence];
    $('evidence-note').append(strong, p);
    $('evidence-note').classList.toggle('amber', trace.evidence !== 'measured');
    $('load-status').textContent = `${source} · ${events.length} events · ${media.length} embedded audio clips · no upload`;
    clear($('limitations'));
    for (const value of trace.limitations || []) {
      const li = document.createElement('li'); li.textContent = String(value); $('limitations').appendChild(li);
    }
    clear($('clip-select'));
    for (const item of media) {
      const option = document.createElement('option'); option.value = item.id; option.textContent = item.label || item.id;
      $('clip-select').appendChild(option);
    }
    $('clip-select').disabled = !media.length;
    setClip(media[0] || null);
    $('event-search').value = '';
    $('selection-title').textContent = 'Click a bar or event marker.';
    $('event-detail').textContent = 'No event selected.';
    renderTimeline(true); renderLedger();
    if (finite(trace.metadata?.focus_seconds)) setCursor(trace.metadata.focus_seconds);
  }

  function range() {
    const active = events.filter(e => $('warmup').checked || e.lane !== 'startup');
    minimum = $('warmup').checked ? 0 : Math.min(...active.map(e => e.start), ...media.filter(m => m.anchor != null).map(m => m.anchor));
    if (!Number.isFinite(minimum)) minimum = 0;
    maximum = Math.max(minimum + 1, ...active.map(e => e.end), ...media.filter(m => m.anchor != null).map(m => m.anchor + (m.duration || 0)));
    visible = active;
    $('scrub').min = minimum; $('scrub').max = maximum;
    $('play').disabled = !events.length; $('scrub').disabled = !events.length;
  }
  const x = value => plotLeft + (value - minimum) / (maximum - minimum) * (plotRight - plotLeft);
  function actionable(node, event) {
    node.setAttribute('role', 'button'); node.setAttribute('tabindex', '0');
    node.setAttribute('aria-label', `${event.label}, ${fmt(event.start)} to ${fmt(event.end)} seconds`);
    svg('title', {}, node, `${event.label}\n${fmt(event.start)}–${fmt(event.end)} s`);
    node.addEventListener('click', () => chooseEvent(event));
    node.addEventListener('keydown', e => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); chooseEvent(event); } });
  }

  function renderTimeline(rewind = false) {
    range();
    if (rewind) cursor = minimum;
    cursor = Math.min(maximum, Math.max(minimum, cursor));
    const order = ['input', 'thinker', 'system2', 'talker', 'reasoning', 'control', 'audio', 'startup'];
    const rank = lane => order.includes(lane.id) ? order.indexOf(lane.id) : 99;
    const lanes = trace.lanes.filter(lane => $('warmup').checked || lane.id !== 'startup').sort((a,b) => rank(a)-rank(b));
    if (media.some(m => m.anchor != null && m.role !== 'input')) lanes.push({id: 'audition', label: 'Audio audition · replay'});
    width = Math.max(1000, $('timeline-scroll').clientWidth) * Number($('zoom').value);
    plotRight = width - 24; height = Math.max(110, 62 + lanes.length * 80);
    const root = $('timeline');
    root.setAttribute('viewBox', `0 0 ${width} ${height}`);
    root.setAttribute('width', width); root.setAttribute('height', height);
    clear(root);
    svg('title', {id: 'svg-title'}, root, 'Time-aligned layer events');
    svg('desc', {id: 'svg-description'}, root, 'Requests and received observations, an annotated S1 idle interval, and optional browser audition schedules.');
    const defs = svg('defs', {}, root);
    const pattern = svg('pattern', {id: 'hatch', width: 8, height: 8, patternUnits: 'userSpaceOnUse'}, defs);
    svg('path', {d: 'M-2 2L2 -2M0 8L8 0M6 10L10 6', stroke: 'var(--blue)', 'stroke-width': 1, opacity: 0.5}, pattern);
    for (let i = 0; i <= 8; i++) {
      const at = minimum + (maximum - minimum) * i / 8;
      svg('line', {x1: x(at), x2: x(at), y1: 26, y2: height - 15, class: 'axis'}, root);
      svg('text', {x: x(at), y: 18, 'text-anchor': i === 8 ? 'end' : 'middle'}, root, `${at.toFixed(2)} s`);
    }
    lanes.forEach((lane, index) => {
      const y = 54 + index * 80;
      svg('text', {x: 12, y: y + 10, class: 'lane-label'}, root, lane.label);
      svg('line', {x1: 0, x2: width, y1: y + 48, y2: y + 48, class: 'axis'}, root);
      const progress = visible.filter(e => e.lane === lane.id && e.kind === 'reasoning_progress');
      const maxChars = Math.max(1, ...progress.map(e => e.details?.characters || 0));
      const progressY = e => y + 20 - (e.details?.characters || 0) / maxChars * 32;
      if (lane.id === 'reasoning' && progress.length) {
        svg('text', {x: 12, y: y + 26, class: 'progress-scale'}, root, `0 → ${maxChars.toLocaleString()} characters`);
        svg('polyline', {points: progress.map(e => `${x(e.start)},${progressY(e)}`).join(' '),
          fill: 'none', stroke: 'var(--blue)', 'stroke-width': 2}, root);
      }
      for (const event of visible.filter(e => e.lane === lane.id)) {
        const group = svg('g', {'data-event': event.id}, root);
        if (event.end > event.start) {
          const cls = event.kind === 'guidance_state' ? 'guidance' : event.kind === 'input_condition' || event.kind === 'absence' ? 'absence' : event.kind === 'service_check' ? 'service-check' : event.kind === 'incomplete' ? 'incomplete' : lane.id === 'system2' ? 'request s2' : 'request';
          svg('rect', {x: x(event.start), y: y - 17, width: Math.max(3, x(event.end) - x(event.start)), height: 44, rx: 5, class: cls + (event.id === selected ? ' selected' : '')}, group);
          const room = x(event.end) - x(event.start);
          if (room > 25) blockText(group, x(event.start)+6, y-4, room-12, eventContent(event));
          actionable(group, event);
        } else {
          const jitter = event.kind === 'reasoning_progress' ? -5 : event.kind === 'final_delta' ? 7 : 0;
          svg('circle', {cx: x(event.start), cy: lane.id === 'reasoning' ? progressY(event) : y + jitter, r: 5, class: 'dot' + (lane.id === 'system2' || lane.id === 'reasoning' ? ' reason-dot' : '') + (event.id === selected ? ' selected' : '')}, group);
          actionable(group, event);
        }
      }
      if (lane.id === 'input') media.filter(m => m.anchor != null && m.role === 'input').forEach(item => {
        const group = svg('g', {}, root);
        const room = Math.max(3, x(item.anchor+(item.duration||0))-x(item.anchor));
        svg('rect', {x:x(item.anchor),y:y-17,width:room,height:44,fill:'url(#hatch)',stroke:'var(--blue)',rx:5},group);
        if (room>45) blockText(group,x(item.anchor)+6,y-4,room-12,item.text || 'User audio');
        actionable(group,{id:`media-${item.id}`,lane:'input',kind:'audition',start:item.anchor,end:item.anchor+(item.duration||0),label:item.label,details:{media_id:item.id,text:item.text,text_scope:item.text_scope,note:'Recording content duration; browser audition anchored at submission, not measured live microphone speech.'}});
      });
      if (lane.id === 'audition') media.filter(m => m.anchor != null && m.role !== 'input').forEach((item, i) => {
        const group = svg('g', {}, root);
        const yy = y - 11 + (i % 2) * 16;
        svg('rect', {x: x(item.anchor), y: yy, width: Math.max(3, x(item.anchor + (item.duration || 0)) - x(item.anchor)), height: 14, fill: 'url(#hatch)', stroke: 'var(--blue)', rx: 3}, group);
        actionable(group, {id: `media-${item.id}`, label: `Audition: ${item.label || item.id}`, start: item.anchor, end: item.anchor + (item.duration || 0), lane: 'audition', kind: 'audition', details: {media_id: item.id, note: 'Replay schedule; not measured playback'}});
      });
    });
    const labelOverlay=svg('g',{class:'lane-label-overlay'},root);
    svg('rect',{x:0,y:46,width:plotLeft-8,height:height-46,fill:'var(--surface)'},labelOverlay);
    root.querySelectorAll('.lane-label,.progress-scale').forEach(node=>labelOverlay.appendChild(node));
    labelOverlay.setAttribute('transform',`translate(${$('timeline-scroll').scrollLeft},0)`);
    svg('line', {id: 'cursor-line', x1: x(cursor), x2: x(cursor), y1: 25, y2: height - 15, class: 'cursor'}, root);
    if (!events.length) svg('text', {x: plotLeft + 20, y: 70}, root, 'No aligned events captured. Use Audio audition below.');
    renderStats(); setCursor(cursor);
  }

  function messageText(details) {
    const response = details.response;
    let text = details.tts || details.asr || response?.choices?.[0]?.message?.content || '';
    if (typeof text !== 'string') text = JSON.stringify(text);
    return text;
  }
  function eventContent(event) {
    const details = event.details || {};
    if (event.lane === 'thinker') {
      if (event.kind === 'absence') return '(silent · no S1 call)';
      const fields = s1Fields(details);
      return fields ? fields.tts?.trim() || '(silent)' : '(speech text not recorded)';
    }
    if (event.lane === 'system2' && event.kind === 'request') return 'thinking / streaming guidance…';
    if (event.lane === 'talker') {
      const text = details.tts ?? details.source_tts;
      return typeof text === 'string' ? text.trim() || '(silent)' : '(spoken text unverified)';
    }
    return details.command || details.text?.trim() || event.label;
  }
  function blockText(parent,left,top,room,text) {
    const size = room < 70 ? 10 : 12;
    if (/[\u3000-\u9fff]/.test(String(text)) || String(text)==='(silent)') {
      const charWidth=String(text)==='(silent)'?size*.58:size;
      const limit=Math.max(1,Math.floor(room/charWidth)), characters=Array.from(String(text)), lines=[];
      for(let i=0;i<characters.length;i+=limit) lines.push(characters.slice(i,i+limit).join(''));
      const node=svg('text',{x:left,y:top},parent);node.style.fontSize=size+'px';
      lines.slice(0,3).forEach((value,i)=>svg('tspan',{x:left,dy:i?13:0},node,i===2&&lines.length>3?value.slice(0,-1)+'…':value));
      return;
    }
    const limit = Math.max(4,Math.floor(room/(size*.58)));
    const words = String(text).split(/\s+/), lines=[];
    let line='';
    for (let word of words) {
      if (word.length>limit) word=word.slice(0,limit-1)+'…';
      if ((line+' '+word).trim().length>limit && line) {lines.push(line);line=word;} else line=(line+' '+word).trim();
    }
    if (line) lines.push(line);
    const node=svg('text',{x:left,y:top},parent);node.style.fontSize=size+'px';
    lines.slice(0,3).forEach((value,i)=>svg('tspan',{x:left,dy:i?13:0},node,i===2 && lines.length>3 ? value.slice(0,limit-1)+'…':value));
  }
  function s1Fields(details) {
    if (details.fields && typeof details.fields === 'object') return details.fields;
    if (typeof details.tts === 'string' || typeof details.asr === 'string') return details;
    const raw = details.response?.choices?.[0]?.message?.content;
    if (typeof raw === 'string') {
      try { return JSON.parse(raw); } catch (_) { return null; }
    }
    return null;
  }
  function setCursor(value) {
    cursor = Math.min(maximum, Math.max(minimum, value));
    $('scrub').value = cursor; $('time-label').textContent = `${fmt(cursor)} s · selected trace clock`;
    const line = $('cursor-line');
    if (line) { line.setAttribute('x1', x(cursor)); line.setAttribute('x2', x(cursor)); }
    const scroll=$('timeline-scroll'), position=x(cursor);
    if(position<scroll.scrollLeft+plotLeft || position>scroll.scrollLeft+scroll.clientWidth-24)
      scroll.scrollLeft=Math.max(0,position-plotLeft-scroll.clientWidth*.35);
    const labelOverlay=$('timeline').querySelector('.lane-label-overlay');
    if(labelOverlay)labelOverlay.setAttribute('transform',`translate(${scroll.scrollLeft},0)`);
    const active = visible.filter(e => ['request', 'incomplete', 'service_check'].includes(e.kind) && e.end > e.start && e.start <= cursor && e.end > cursor);
    $('active-layers').textContent = active.length ? `In progress: ${active.map(e => e.label).join(' · ')}` : 'No active requests at this cursor.';
    const received = events.filter(e => e.end <= cursor);
    const s1 = received.filter(e => e.lane === 'thinker' && e.kind !== 'absence' && (s1Fields(e.details || {}) || messageText(e.details || {}))).at(-1);
    const fields = s1 ? s1Fields(s1.details || {}) : null;
    $('s1-asr').textContent = fields ? fields.asr?.trim() || 'Empty asr field.' : s1 ? 'Structured transcription unavailable; inspect the raw response.' : 'Not received yet.';
    $('s1-text').textContent = fields ? fields.tts?.trim() || 'Empty tts field — no speech text returned.' : s1 ? 'Structured speech text unavailable; inspect the raw response.' : 'Not received yet.';
    const progress = received.filter(e => e.kind === 'reasoning_progress');
    const counts = new Map();
    for (const e of progress) counts.set(e.details?.request || 'S2', e.details?.characters || 0);
    const requestNames = new Map(events.map(e => [e.id, e.label]));
    $('reasoning-progress').textContent = counts.size ? [...counts].map(([id, count]) => `${requestNames.get(id) || id}: ${count} received characters`).join(' · ') : 'No received reasoning deltas.';
    const final = received.filter(e => e.kind === 'final_delta').at(-1);
    $('s2-text').textContent = final ? final.details?.text || final.details?.delta || '' : 'Not received yet.';
    const delivered = received.filter(e => e.kind === 'command_forwarded').at(-1);
    $('s2-delivered').textContent = delivered ? delivered.details?.command || '' : 'No guidance delivered to S1 yet. Partial streamed text stays in the orchestrator buffer.';
    const control = received.filter(e => e.lane === 'control').at(-1);
    $('control-text').textContent = control ? `${control.label}: ${control.details?.command || control.details?.system2_control || control.details?.status || ''}` : 'None.';
  }

  function chooseEvent(event) {
    pause(); player.pause(); selected = event.id;
    setCursor(event.start);
    $('selection-title').textContent = `${event.label} · ${fmt(event.start)}–${fmt(event.end)} s`;
    $('event-detail').textContent = JSON.stringify({layer: event.lane, kind: event.kind, duration_seconds: event.end - event.start, ...event.details}, null, 2);
    if (event.details?.media_id) setClip(media.find(m => m.id === event.details.media_id) || clip);
    renderTimeline();
  }
  function renderStats() {
    clear($('stats'));
    const requests = events.filter(e => ['request', 'service_check'].includes(e.kind));
    const reasonChars = Math.max(0, ...events.filter(e => e.kind === 'reasoning_progress').map(e => e.details?.characters || 0));
    for (const [number, label] of [[String(events.length), 'Captured events'], [String(requests.length), 'Completed request spans'], [fmt(maximum - minimum) + ' s', 'Visible replay window'], [String(reasonChars), 'Largest S2 character count']]) {
      const box = document.createElement('div'); box.className = 'stat';
      const strong = document.createElement('strong'); strong.textContent = number;
      const span = document.createElement('span'); span.textContent = label; box.append(strong, span); $('stats').appendChild(box);
    }
  }
  function renderLedger() {
    clear($('event-rows'));
    const search = $('event-search').value.trim().toLowerCase();
    const filtered = events.filter(e => JSON.stringify(e).toLowerCase().includes(search));
    $('event-count').textContent = `${filtered.length} of ${events.length} events`;
    const labels = new Map(trace.lanes.map(l => [l.id, l.label]));
    for (const event of filtered) {
      const row = document.createElement('tr');
      for (const value of [labels.get(event.lane) || event.lane, fmt(event.start), fmt(event.end)]) {
        const cell = document.createElement('td'); cell.textContent = value; row.appendChild(cell);
      }
      const cell = document.createElement('td'); const button = document.createElement('button');
      button.type = 'button'; button.textContent = event.label; button.addEventListener('click', () => chooseEvent(event));
      cell.appendChild(button); row.appendChild(cell); $('event-rows').appendChild(row);
    }
  }
  function setClip(item) {
    player.pause(); clip = item;
    clear($('waveform')); svg('title', {id: 'wave-title'}, $('waveform'), 'Selected clip waveform envelope');
    if (!clip) {
      player.removeAttribute('src'); player.load(); $('clip-note').textContent = 'No audio clips in this trace.';
      return;
    }
    $('clip-select').value = clip.id;
    player.src = clip.data_uri;
    $('clip-note').textContent = `${clip.duration == null ? 'Duration not recorded' : fmt(clip.duration) + ' s of audio'} · ${clip.anchor == null ? 'No measured timing anchor; cursor is not linked.' : 'Audition anchor: ' + fmt(clip.anchor) + ' s; cursor follows anchor + clip position.'}`;
    if (clip.text_scope) $('clip-note').textContent += ' ' + clip.text_scope + '.';
    if (clip.automatic_transcript) $('clip-note').textContent += ' Automatic audio transcript: “' + clip.automatic_transcript + '”.';
    const peaks = clip.waveform || [];
    peaks.forEach((peak, i) => svg('line', {x1: i / peaks.length * 800, x2: i / peaks.length * 800, y1: 45 - peak * 40, y2: 45 + peak * 40, 'stroke-width': Math.max(1, 800 / peaks.length * .65)}, $('waveform')));
    if (!peaks.length) svg('text', {x: 15, y: 48, fill: 'currentColor'}, $('waveform'), 'No waveform envelope recorded; audio remains playable.');
  }

  function animate(now) {
    if (playing) {
      const delta = lastFrame ? (now - lastFrame) / 1000 * Number($('speed').value) : 0;
      setCursor(cursor + delta);
      if (cursor >= maximum) pause();
    }
    lastFrame = now;
    requestAnimationFrame(animate);
  }
  $('play').addEventListener('click', () => {
    player.pause(); playing = !playing;
    if (playing && cursor >= maximum) setCursor(minimum);
    lastFrame = 0; $('play').textContent = playing ? 'Pause timing' : 'Replay timing';
  });
  $('reset').addEventListener('click', () => { pause(); player.pause(); setCursor(minimum); });
  $('scrub').addEventListener('input', () => { pause(); player.pause(); setCursor(Number($('scrub').value)); });
  $('warmup').addEventListener('change', () => { pause(); player.pause(); renderTimeline(true); });
  $('zoom').addEventListener('input', () => renderTimeline());
  $('event-search').addEventListener('input', renderLedger);
  $('clip-select').addEventListener('change', () => { pause(); setClip(media.find(m => m.id === $('clip-select').value)); });
  player.addEventListener('play', () => { pause(); if (clip?.anchor != null) setCursor(clip.anchor + player.currentTime); });
  player.addEventListener('timeupdate', () => { if (!player.paused && clip?.anchor != null) setCursor(clip.anchor + player.currentTime); });
  player.addEventListener('seeking', () => { if (clip?.anchor != null) { pause(); setCursor(clip.anchor + player.currentTime); } });
  $('load-demo').addEventListener('click', () => load(demo, 'Hosted demo'));
  $('load-real').addEventListener('click', () => load(example.waiting_trace, 'Recorded run · ' + example.waiting_trace.metadata.job_id));
  $('load-native').addEventListener('click', () => load(example.native_trace, 'Native acknowledgment · ' + example.native_trace.metadata.job_id));
  $('load-full').addEventListener('click', () => load(example.full_loop_trace, 'Full native loop · ' + example.full_loop_trace.metadata.job_id));
  if ($('interactive-case') && example.interactive_traces) {
    for (const [key, value] of Object.entries(example.interactive_traces)) {
      const option = document.createElement('option'); option.value = key;
      option.textContent = `${value.metadata.gpus} × ${value.metadata.gpu_type} · ${value.metadata.case} · ${value.metadata.job_id}`;
      $('interactive-case').appendChild(option);
    }
    $('interactive-case').value = example.interactive_default;
    $('interactive-case').addEventListener('change', () => load(example.interactive_traces[$('interactive-case').value], 'Measured interaction case'));
  }
  $('timeline-scroll').addEventListener('scroll',()=>{
    const overlay=$('timeline').querySelector('.lane-label-overlay');
    if(overlay)overlay.setAttribute('transform',`translate(${$('timeline-scroll').scrollLeft},0)`);
  });
  async function readFile(file) {
    if (!file) return;
    try {
      if (file.size > 100_000_000) throw new Error('Trace exceeds the 100 MB browser import limit.');
      load(JSON.parse(await file.text()), `Local file: ${file.name}`);
    } catch (error) { $('load-status').textContent = `Could not load trace: ${error.message}. Current trace retained.`; }
  }
  $('trace-file').addEventListener('change', e => readFile(e.target.files[0]));
  const zone = $('drop-zone');
  zone.addEventListener('dragover', e => { e.preventDefault(); zone.classList.add('dragging'); });
  zone.addEventListener('dragleave', () => zone.classList.remove('dragging'));
  zone.addEventListener('drop', e => { e.preventDefault(); zone.classList.remove('dragging'); readFile(e.dataTransfer.files[0]); });
  let resizeTimer;
  window.addEventListener('resize', () => { clearTimeout(resizeTimer); resizeTimer = setTimeout(() => renderTimeline(), 120); });
  // Phase B is a separate run. Its cursor is an input-chunk index, never a
  // fabricated continuation of phase A's measured request clock.
  const caseLabels = {
    original_continuation: 'Original history · no added THINK',
    prior_THINK_bracketed: 'Added THINK · bracketed S2 text',
    prior_THINK_plaintext: 'Added THINK · plain S2 text',
    prior_THINK_plaintext_contrast: 'Changed S2 answer · diagnostic control',
    native_prompt_prior_THINK_plaintext: 'Native prompt · added THINK · plain S2 text'
  };
  let replyCase = example.continuation.cases[0], chunkIndex = 23, chunkTimer = null;
  function stopChunks() { clearInterval(chunkTimer); chunkTimer = null; $('chunk-play').textContent = 'Replay text chunks'; }
  function renderChunk(index) {
    chunkIndex = Math.max(0, Math.min(replyCase.turns.length - 1, Number(index)));
    const turn = replyCase.turns[chunkIndex];
    const joined = replyCase.turns.slice(0, chunkIndex + 1).map(t => t.tts).join('');
    $('chunk-cursor').value = chunkIndex;
    $('chunk-label').textContent = `#${chunkIndex} · ${turn.audio_end_seconds.toFixed(2)} s input`;
    $('chunk-fragment').textContent = turn.tts.trim() || 'Empty tts field.';
    $('chunk-transcript').textContent = joined.trim() || 'No generated speech text yet.';
    $('chunk-detail').textContent = `Chunk ${chunkIndex} · ${turn.request_seconds.toFixed(3)} s request + tensor RPC (measured separately from input duration).`;
    $('chunk-fields').textContent = JSON.stringify({asr: turn.asr, tts: turn.tts, tts_control: turn.tts_control, system2_control: turn.system2_control}, null, 2);
    $('answer-status').textContent = joined.includes(replyCase.command) ? 'The complete supplied S2 answer is present in S1’s generated text.' : 'The supplied answer is not complete at this chunk.';
    for (const node of $('chunk-grid').querySelectorAll('[data-chunk]')) {
      const active = Number(node.dataset.chunk) === chunkIndex;
      node.classList.toggle('selected', active); node.setAttribute('aria-pressed', String(active));
    }
  }
  function loadCase(id) {
    stopChunks(); replyCase = example.continuation.cases.find(c => c.id === id);
    $('reply-command').textContent = replyCase.command;
    $('case-note').textContent = replyCase.counterfactual ? 'Diagnostic intervention: assistant control state, system prompt or supplied S2 text was edited. This does not demonstrate automatic delegation.' : 'Captured original history and S2 command. S1 did not issue THINK; delegation was forced in the source functional test.';
    clear($('chunk-grid'));
    for (const [row,title] of [['user','User input'],['s1','S1 output'],['s2','S2 guidance (replayed)'],['talker','Talker']]) {
      const header=document.createElement('div');header.className='matrix-label';header.textContent=title;$('chunk-grid').appendChild(header);
      for (const turn of replyCase.turns) {
        const button = document.createElement('button'); button.type = 'button';
        button.className = 'chunk ' + (row==='s1'?turn.role:row==='s2' && turn.chunk===0?'answer':'empty');
        button.dataset.chunk = turn.chunk; button.dataset.row=row;
        const content=row==='user'?'(silent)':row==='s1'?turn.tts.trim()||'(silent)':row==='s2'?(turn.chunk===0?replyCase.command:'(no new guidance)'):'(not run · no audio)';
        button.setAttribute('aria-label', `${title}, chunk ${turn.chunk}, ${content}`);
        const label = document.createElement('span'); label.className = 'chunk-time'; label.textContent = `#${turn.chunk} · ${turn.audio_end_seconds.toFixed(2)} s`;
        const text = document.createElement('span'); text.textContent = content;
        button.append(label, text); button.addEventListener('click', () => { stopChunks(); renderChunk(turn.chunk); });
        $('chunk-grid').appendChild(button);
      }
    }
    renderChunk(replyCase.turns.length - 1);
  }
  for (const item of example.continuation.cases) {
    const option = document.createElement('option'); option.value = item.id; option.textContent = caseLabels[item.id] || item.id;
    $('reply-case').appendChild(option);
  }
  $('reply-case').addEventListener('change', () => loadCase($('reply-case').value));
  $('chunk-cursor').addEventListener('input', () => { stopChunks(); renderChunk($('chunk-cursor').value); });
  $('chunk-reset').addEventListener('click', () => { stopChunks(); renderChunk(0); });
  $('chunk-play').addEventListener('click', () => {
    if (chunkTimer) { stopChunks(); return; }
    if (chunkIndex === replyCase.turns.length - 1) renderChunk(0);
    $('chunk-play').textContent = 'Pause chunks';
    chunkTimer = setInterval(() => { renderChunk(chunkIndex + 1); if (chunkIndex === replyCase.turns.length - 1) stopChunks(); }, 480);
  });
  loadCase(replyCase.id);
  if (example.interactive_traces && example.interactive_default) {
    load(example.interactive_traces[example.interactive_default], 'Measured interaction reproduction');
  } else {
    load(example.waiting_trace, 'Recorded run · ' + example.waiting_trace.metadata.job_id);
  }
  requestAnimationFrame(animate);
})();
