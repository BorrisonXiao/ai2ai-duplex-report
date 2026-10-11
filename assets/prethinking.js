'use strict';
(() => {
  const step = document.getElementById('arrival-step');
  const kind = document.getElementById('arrival-kind');
  const list = document.getElementById('arrival-events');
  if (!step || !kind || !list) return;
  function render() {
    const arrival = Number(step.value);
    const noteReady = arrival > 2;
    document.getElementById('arrival-value').textContent = String(arrival);
    const events = ['Step 0: S1 starts bounded preparation from the observed group conversation.'];
    if (arrival > 1) events.push('Step 1: S2 extracts evidence; no complete note is ready.');
    if (noteReady) events.push('Step 2: A completed note records Alex’s Friday proposal, with evidence and unconfirmed status.');
    if (arrival > 3) events.push('Steps 3–' + (arrival - 1) + ': S2 continues private analysis. The unfinished trace stays inside S2.');
    events.push('Step ' + arrival + ': The assistant-directed request preempts background decoding. S1 continues listening.');
    if (kind.value === 'correction') {
      events.push(noteReady ? 'The Friday note is invalidated by the Monday correction. S2 checks current evidence before answering.' : 'No completed note is available. S2 starts from observed evidence and the Monday correction.');
    } else if (kind.value === 'other') {
      events.push('S2 selects evidence for the different request. Preparatory guesses do not decide what the user meant.');
    } else {
      events.push(noteReady ? 'S2 rechecks the note against the actual request and clarifies if “it” has two possible referents.' : 'There is no complete note. S2 reasons from causal evidence and any private material it can validly reuse.');
    }
    events.push('Only a grounded request-specific result can enter speech guidance. Late outputs from the old work ID are rejected.');
    list.replaceChildren(...events.map((text, index) => {
      const li = document.createElement('li');
      li.textContent = text;
      if (index === events.length - 2) li.className = 'active';
      return li;
    }));
  }
  step.addEventListener('input', render);
  kind.addEventListener('change', render);
  render();
})();
