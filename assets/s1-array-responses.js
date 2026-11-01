/* Browse saved response audio and independent ASR; no inference or remote data fetch. */
(() => {
  const root = document.getElementById('array-response-browser');
  if (!root) return;
  const data = JSON.parse(document.getElementById('array-response-data').textContent);
  const cases = new Map(data.cases.map(row => [row.id, row]));
  const setting = document.getElementById('response-setting');
  const context = document.getElementById('response-context');
  const audio = document.getElementById('selected-response-audio');
  const toggle = document.getElementById('show-response-asr');
  const panel = document.getElementById('selected-response-asr-panel');
  const previous = document.getElementById('previous-response-context');
  const next = document.getElementById('next-response-context');
  const text = (id, value) => { document.getElementById(id).textContent = value; };
  function expanded(value) {
    panel.hidden = !value;
    toggle.setAttribute('aria-expanded', String(value));
    toggle.textContent = value ? 'Hide response ASR' : 'Show response ASR';
  }
  function render() {
    const id = `${setting.value}-L${context.value.padStart(2, '0')}`;
    const row = cases.get(id);
    root.dataset.activeCase = id;
    document.getElementById('selected-response-link').href = `#sweep-${id}`;
    audio.pause();
    audio.hidden = !row.response_valid;
    toggle.disabled = !row.response_valid;
    if (row.response_valid) {
      audio.src = row.audio;
      audio.setAttribute('aria-label', `${data.labels[row.condition]} level ${row.index} actual model response`);
    } else {
      audio.removeAttribute('src');
      expanded(false);
    }
    audio.load();
    text('response-case-status', `${data.labels[row.condition]} · level ${row.index} · ${row.context_seconds.toFixed(2)} seconds of preceding audio. ${row.response_valid ? 'Saved model response and independent ASR.' : 'The replay did not complete; no completed response audio or response-content score is available.'}`);
    text('selected-response-asr', row.spoken_transcript || '(empty transcript)');
    let score = 'Response content is unscored: this shorter history does not contain all required source evidence.';
    if (!row.response_valid) score = 'Response content is unscored because the replay did not complete.';
    else if (row.source_evidence_fully_available) {
      const facts = record => record && record.fact_score != null ? `${record.fact_score * 2} / 2` : 'unscored';
      score = `Response facts: LLM ${facts(row.judge)}; Codex source review ${facts(row.source_audit)}. See Figure 4 for response-content evaluation and judge limitations.`;
    }
    text('selected-response-score', score);
    text('selected-response-audit', row.source_audit ? row.source_audit.reason : '');
    text('selected-question-asr', row.WER_valid ? row.question_asr || '(empty question transcript)' : 'Unscored: the question-recognition window was not reached.');
    text('selected-question-wer', row.WER_valid ? `Question WER: ${row.recognition.WER.toFixed(4)}. This is question transcription, not response-content scoring.` : '');
    text('selected-native-response', row.response_valid ? row.speech_text || '(empty intended response text)' : 'No completed response.');
    previous.disabled = Number(context.value) === 0;
    next.disabled = Number(context.value) === 40;
  }
  setting.addEventListener('change', render);
  context.addEventListener('change', render);
  previous.addEventListener('click', () => { context.value = String(Number(context.value) - 1); render(); });
  next.addEventListener('click', () => { context.value = String(Number(context.value) + 1); render(); });
  toggle.addEventListener('click', () => expanded(panel.hidden));
  document.querySelectorAll('[data-open-response]').forEach(button => {
    button.addEventListener('click', () => {
      const row = cases.get(button.dataset.openResponse);
      setting.value = row.condition;
      context.value = String(row.index);
      render();
      if (row.response_valid) expanded(true);
      root.scrollIntoView({block: 'start'});
      root.focus({preventScroll: true});
    });
  });
  const players = document.querySelectorAll('audio');
  players.forEach(player => player.addEventListener('play', () => {
    players.forEach(other => { if (other !== player) other.pause(); });
  }));
  render();
})();
