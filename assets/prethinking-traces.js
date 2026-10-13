'use strict';
(() => {
  const element = document.getElementById('teacher-trace-data');
  if (!element) return;
  const calls = JSON.parse(element.textContent).calls;
  const chunks = JSON.parse(document.getElementById('pilot-data').textContent).chunks;
  const byCall = new Map(calls.map(c => [c.index, c]));
  const byChunk = new Map(chunks.map(c => [c.id, c]));
  const focus = document.getElementById('thinking-call');
  const windowSelect = document.getElementById('thinking-window');
  const cursor = document.getElementById('thinking-cursor');
  const svg = document.getElementById('thinking-svg');
  const scroll = document.querySelector('.thinking-scroll');
  const encoder = new TextEncoder(), bytes = new Map(), ns = 'http://www.w3.org/2000/svg';
  const rates = [10, 30, 60, 100], left = 130, setup = 0.5;
  let axisWidth = 1000, right = 940;
  let selectedRate = 60;
  calls.forEach(c => {
    const o = document.createElement('option');
    o.value = String(c.index);
    o.textContent = 'Call ' + c.index + ' · ' + c.at.toFixed(2) + ' s · ' + c.history_mode + ' · seed ' + c.seed + ' · original ' + (c.rate ? c.rate + '-rate budget' : 'scout');
    focus.append(o);
  });
  focus.value = '54';
  function node(tag, attrs, text) {
    const el = document.createElementNS(ns, tag);
    Object.entries(attrs || {}).forEach(([k, v]) => el.setAttribute(k, String(v)));
    if (text !== undefined) el.textContent = text;
    return el;
  }
  function html(tag, cls, text) {
    const el = document.createElement(tag);
    if (cls) el.className = cls;
    if (text !== undefined) el.textContent = text;
    return el;
  }
  function prefix(c, n) {
    if (n <= 0) return '';
    if (!bytes.has(c.index)) bytes.set(c.index, encoder.encode(c.generated_text));
    return new TextDecoder().decode(bytes.get(c.index).subarray(0, c.token_byte_ends[n - 1]), {stream: true});
  }
  function nextTime(c) {
    return c.next_arrival ?? chunks.find(x => x.available > c.at + 1e-7)?.available ?? c.at + 20;
  }
  function counts(c, rate, time) {
    const deadline = nextTime(c);
    const capacity = Math.floor(rate * Math.max(0, deadline - c.at - setup) + 1e-9);
    const effective = Math.min(c.output_tokens, capacity);
    const emitted = Math.min(effective, Math.floor(rate * Math.max(0, time - c.at - setup) + 1e-9));
    return {deadline, capacity, effective, emitted, start: c.at + setup, end: c.at + setup + effective / rate};
  }
  function bounds(c) {
    const incoming = c.new_ids.map(id => byChunk.get(id));
    const earliest = Math.min(c.at, ...incoming.map(x => x.start));
    return [Math.floor(Math.max(0, (windowSelect.value === 'thinking' ? c.at : earliest) - 1) * 100) / 100, Math.ceil((nextTime(c) + 1) * 100) / 100];
  }
  function openCall(index, prompt = false) {
    const detail = document.getElementById('appendix-call-' + index);
    // A link should remain usable even after filtering the appendix.
    if (detail.hidden) {document.getElementById('appendix-filter').value = ''; document.getElementById('appendix-filter').dispatchEvent(new Event('input'));}
    detail.open = true;
    if (prompt) detail.querySelector('.trace-prompt-details').open = true;
    detail.scrollIntoView({behavior: 'auto', block: 'start'});
  }
  function inspect(c, time) {
    const box = document.getElementById('thinking-inspector'), n = counts(c, selectedRate, time);
    box.replaceChildren();
    box.append(html('h3', '', 'Selected output: call ' + c.index + ' at ' + selectedRate + ' tokens/s'));
    box.append(html('p', '', 'At ' + time.toFixed(2) + ' s, ' + n.emitted + ' tokens have been emitted. By the next update at ' + n.deadline.toFixed(2) + ' s, ' + n.effective + ' of ' + c.output_tokens + ' captured tokens fit (' + n.capacity + ' tokens of available capacity). Every rate uses this same call.'));
    const link = html('a', '', 'Full captured thinking, original history and exact prompt');
    link.href = '#appendix-call-' + c.index;
    link.addEventListener('click', event => {event.preventDefault(); openCall(c.index, true);});
    box.append(link);
  }
  function eventLines(target, x, c, now, height, labels = false) {
    for (const [t, cls, label] of [[c.at, 'trace-delivery-line', 'Input delivered'], [c.at + setup, 'trace-start-line', 'S2 starts'], [nextTime(c), 'trace-update-line', 'Next input']]) {
      target.append(node('line', {x1: x(t), x2: x(t), y1: labels ? 48 : 12, y2: height, class: cls}));
      if (labels) {
        const offset = label === 'S2 starts' ? 41 : 21;
        target.append(node('text', {x: x(t) + (label === 'Next input' ? -7 : 7), y: offset, 'text-anchor': label === 'Next input' ? 'end' : 'start', class: 'trace-event-label'}, label + ' ' + t.toFixed(2) + ' s'));
      }
    }
    target.append(node('line', {x1: x(now), x2: x(now), y1: labels ? 48 : 12, y2: height, class: 'trace-time-cursor'}));
  }
  function renderTranscripts(c, x, lo, hi, now) {
    const incoming = c.new_ids.map(id => byChunk.get(id)).sort((a, b) => a.start - b.start || a.end - b.end || a.id.localeCompare(b.id));
    const cards = document.getElementById('thinking-transcripts');
    cards.replaceChildren(); cards.style.setProperty('--input-count', String(incoming.length));
    document.getElementById('thinking-input-label').textContent = 'New input for call ' + c.index + ': ' + incoming.length + ' transcript chunks delivered together at ' + c.at.toFixed(2) + ' s';
    incoming.forEach((chunk, i) => {
      const card = html('article', 'trace-transcript-card speaker-' + chunk.speaker);
      card.dataset.chunk = chunk.id;
      card.append(html('h5', '', '#' + (i + 1) + ' · Speaker ' + chunk.speaker + ' · ' + chunk.id));
      card.append(html('p', 'trace-chunk-clock', chunk.start.toFixed(2) + '–' + chunk.end.toFixed(2) + ' s · duration ' + (chunk.end - chunk.start).toFixed(2) + ' s'));
      card.append(html('p', 'trace-chunk-text', chunk.text));
      card.append(html('p', 'trace-chunk-release', 'Transcript available ' + chunk.available.toFixed(2) + ' s → batch ' + c.at.toFixed(2) + ' s'));
      cards.append(card);
    });
    svg.setAttribute('viewBox', '0 0 ' + axisWidth + ' 240');
    svg.replaceChildren(node('title', {id: 'thinking-title'}, 'Speech durations for this input update; numbered text cards above'));
    for (let i = 0; i <= 6; i++) {
      const t = lo + (hi - lo) * i / 6;
      svg.append(node('line', {x1: x(t), x2: x(t), y1: 50, y2: 210, class: 'axis'}));
      svg.append(node('text', {x: x(t), y: 232, 'text-anchor': 'middle'}, t.toFixed(2) + ' s'));
    }
    const laneY = {A: 82, B: 133, C: 184};
    Object.entries(laneY).forEach(([speaker, y]) => svg.append(node('text', {x: 12, y: y + 5}, 'Speaker ' + speaker)));
    incoming.forEach((chunk, i) => {
      if (chunk.end < lo || chunk.start > hi) return;
      const start = Math.max(lo, chunk.start), end = Math.min(hi, chunk.end), y = laneY[chunk.speaker];
      const bar = node('rect', {x: x(start), y, width: x(end) - x(start), height: 15, class: 'trace-speech-span speaker-' + chunk.speaker, 'data-chunk': chunk.id, 'data-start': start, 'data-end': end});
      bar.append(node('title', {}, '#' + (i + 1) + ' · ' + chunk.id + ': ' + chunk.text));
      svg.append(bar);
      svg.append(node('text', {x: x((start + end) / 2), y: y - 6, 'text-anchor': 'middle', class: 'trace-chunk-number'}, '#' + (i + 1)));
    });
    eventLines(svg, x, c, now, 211, true);
  }
  function render() {
    const c = byCall.get(Number(focus.value)), [lo, hi] = bounds(c);
    axisWidth = Math.max(1000, scroll.clientWidth); right = axisWidth - 60;
    scroll.style.setProperty('--thinking-axis-width', axisWidth + 'px');
    scroll.style.setProperty('--thinking-readable-width', scroll.clientWidth + 'px');
    scroll.style.setProperty('--thinking-card-columns', String(scroll.clientWidth >= 900 ? 3 : scroll.clientWidth >= 560 ? 2 : 1));
    cursor.min = String(lo); cursor.max = String(hi);
    const now = Math.min(hi, Math.max(lo, Number(cursor.value))), x = t => left + (t - lo) / (hi - lo) * (right - left);
    cursor.value = String(now);
    document.getElementById('thinking-cursor-label').textContent = now.toFixed(2) + ' s';
    document.getElementById('thinking-method').textContent = 'Fixed source: call ' + c.index + ', ' + c.output_tokens + ' captured tokens, ' + c.history_mode + ', seed ' + c.seed + '. All four rates display prefixes of these identical token IDs. Window ' + lo.toFixed(2) + '–' + hi.toFixed(2) + ' s (' + (hi - lo).toFixed(2) + ' s). Setup: 0.5 s. ' + (c.stage === 'scout' ? 'This scout was not generated as a consecutive timed replay. Its next transcript release supplies the illustrative deadline.' : 'Input delivery and the next batch time are from the recorded replay.') + ' The original prompt/history stay fixed; this view does not regenerate subsequent history under a different rate.';
    renderTranscripts(c, x, lo, hi, now);
    const rows = document.getElementById('thinking-rate-rows'), stats = document.getElementById('thinking-counts');
    rows.replaceChildren(); stats.replaceChildren();
    rates.forEach(rate => {
      const n = counts(c, rate, now), row = html('section', 'thinking-rate-row');
      row.dataset.call = String(c.index); row.dataset.rate = String(rate);
      const heading = html('h4', '', 'S2 ' + rate + ' tokens/s');
      const summary = html('span', 'trace-row-summary', n.emitted + ' tokens at cursor · ' + n.effective + '/' + c.output_tokens + ' fit before next input');
      heading.append(summary); row.append(heading);
      const band = node('svg', {viewBox: '0 0 ' + axisWidth + ' 62', class: 'thinking-rate-band', role: 'img', 'aria-label': rate + ' tokens/s, starts ' + n.start.toFixed(2) + ' s, stops ' + n.end.toFixed(2) + ' s'});
      band.append(node('line', {x1: left, x2: right, y1: 25, y2: 25, class: 'axis'}));
      const capture = node('rect', {x: x(n.start), y: 15, width: x(n.end) - x(n.start), height: 20, class: 'trace-capture', 'data-call': c.index, 'data-rate': rate, 'data-emitted': n.emitted, 'data-fits': n.effective});
      band.append(capture);
      if (n.emitted) band.append(node('rect', {x: x(n.start), y: 15, width: x(n.start + n.emitted / rate) - x(n.start), height: 20, class: 'trace-emitted'}));
      const stride = Math.max(1, Math.ceil(rate * (hi - lo) / (right - left) * 3));
      for (let j = 1; j <= n.effective; j += stride) {
        const t = n.start + j / rate;
        const tick = node('line', {x1: x(t), x2: x(t), y1: 35, y2: 41, class: 'trace-token-tick', 'data-token': j, 'data-token-id': c.generated_token_ids[j - 1]});
        tick.append(node('title', {}, 'Same source call ' + c.index + ': token ' + j + ', ID ' + c.generated_token_ids[j - 1] + ', emission ' + t.toFixed(3) + ' s'));
        band.append(tick);
      }
      band.append(node('text', {x: x(n.end), y: 58, 'text-anchor': 'end'}, n.effective + ' tokens · stop ' + n.end.toFixed(2) + ' s'));
      eventLines(band, x, c, now, 42); row.append(band);
      const output = html('pre', 'trace-prefix trace-row-prefix', n.emitted ? prefix(c, n.emitted) : 'No thinking tokens emitted at this cursor time.');
      output.dataset.call = String(c.index); output.dataset.rate = String(rate); output.dataset.tokens = String(n.emitted);
      output.tabIndex = 0; output.setAttribute('aria-label', 'Exact captured prefix at ' + rate + ' tokens/s; scroll to read all emitted text');
      row.append(output);
      const limit = n.capacity > c.output_tokens ? 'Captured output ends at ' + n.end.toFixed(2) + ' s; extra capacity is unrecorded.' : 'At the next input, the view truncates after token ' + n.effective + '.';
      row.append(html('p', 'trace-row-note', limit + ' Read the complete prefix in the scrollable text panel; inspect the original full call below.'));
      const inspectButton = html('button', 'trace-inspect-button', 'Inspect call ' + c.index + ' at ' + rate + ' tokens/s');
      inspectButton.addEventListener('click', () => {selectedRate = rate; inspect(c, Number(cursor.value));});
      row.append(inspectButton); rows.append(row);
      const tile = html('div', 'trace-count', rate + ' tokens/s: ' + n.emitted + ' emitted at cursor; ' + n.effective + '/' + c.output_tokens + ' captured tokens fit. Available capacity: ' + n.capacity + '.');
      Object.assign(tile.dataset, {rate: String(rate), call: String(c.index), emitted: String(n.emitted), fits: String(n.effective), captured: String(c.output_tokens)});
      stats.append(tile);
    });
    inspect(c, now);
    const sequence = calls.filter(v => v.stage === c.stage && v.history_mode === c.history_mode && v.seed === c.seed && v.rate === c.rate && v.variant === c.variant);
    const position = sequence.findIndex(v => v.index === c.index);
    document.getElementById('thinking-previous').disabled = position <= 0;
    document.getElementById('thinking-next').disabled = position >= sequence.length - 1;
  }
  function focusCall(index) {
    const c = byCall.get(index); focus.value = String(index); selectedRate = 60;
    const [lo, hi] = bounds(c); cursor.min = String(lo); cursor.max = String(hi); cursor.value = String(nextTime(c));
    render();
  }
  cursor.addEventListener('input', () => {const position = scroll.scrollLeft; render(); scroll.scrollLeft = position;});
  windowSelect.addEventListener('change', render);
  window.addEventListener('resize', render);
  focus.addEventListener('change', () => focusCall(Number(focus.value)));
  for (const [id, delta] of [['thinking-previous', -1], ['thinking-next', 1]]) document.getElementById(id).addEventListener('click', () => {
    const c = byCall.get(Number(focus.value));
    const sequence = calls.filter(v => v.stage === c.stage && v.history_mode === c.history_mode && v.seed === c.seed && v.rate === c.rate && v.variant === c.variant);
    const position = sequence.findIndex(v => v.index === c.index);
    if (sequence[position + delta]) focusCall(sequence[position + delta].index);
  });
  document.getElementById('thinking-pan-left').addEventListener('click', () => scroll.scrollTo({left: 0, behavior: 'auto'}));
  document.getElementById('thinking-pan-right').addEventListener('click', () => scroll.scrollTo({left: scroll.scrollWidth, behavior: 'auto'}));
  document.querySelectorAll('a.trace-link').forEach(link => link.addEventListener('click', e => {e.preventDefault(); openCall(Number(link.hash.replace('#appendix-call-', '')), true);}));
  document.querySelectorAll('a.trace-focus-link').forEach(link => link.addEventListener('click', e => {
    e.preventDefault(); focusCall(Number(link.closest('.trace-record').dataset.call));
    document.getElementById('thinking-timeline').scrollIntoView({block: 'start'});
  }));
  const filter = document.getElementById('appendix-filter'), records = [...document.querySelectorAll('.trace-record')];
  filter.addEventListener('input', () => {
    const query = filter.value.trim().toLowerCase();
    records.forEach(r => r.hidden = !r.dataset.search.toLowerCase().includes(query));
    document.getElementById('appendix-count').textContent = records.filter(r => !r.hidden).length + ' of 64 calls';
  });
  document.getElementById('appendix-open-all').addEventListener('click', () => records.filter(r => !r.hidden).forEach(r => r.open = true));
  document.getElementById('appendix-open-prompts').addEventListener('click', () => records.filter(r => !r.hidden).forEach(r => {r.open = true; r.querySelector('.trace-prompt-details').open = true;}));
  document.getElementById('appendix-close-all').addEventListener('click', () => records.forEach(r => r.open = false));
  document.querySelectorAll('audio[data-source-start]').forEach(audio => audio.addEventListener('timeupdate', () => {
    const at = Number(audio.dataset.sourceStart) + audio.currentTime, [lo, hi] = bounds(byCall.get(Number(focus.value)));
    if (at >= lo && at <= hi) {cursor.value = String(at); render();}
  }));
  render();
})();
