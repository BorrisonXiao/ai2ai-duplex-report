# Duplex trajectory schema v1

The [trajectory viewer](../experiments/trajectory.html) accepts a portable JSON
file with no remote audio dependencies. Local files are read in the browser.

```json
{
  "schema": "duplex-trajectory/v1",
  "title": "An audio-only run",
  "evidence": "measured",
  "lanes": [{"id": "thinker", "label": "S1 Thinker"}],
  "events": [{
    "id": "turn-1", "lane": "thinker", "kind": "request",
    "start": 12.0, "end": 13.5,
    "label": "Audio-conditioned turn", "details": {}
  }],
  "media": [],
  "metadata": {"status": "pass"},
  "limitations": ["Client request timestamps; no GPU kernel timing."]
}
```

## Event clock

`start` and `end` are finite, nonnegative seconds since one shared monotonic
origin named in `metadata.clock` (driver start by default; the reviewed example
rebases to whole-input submission). A zero-length event is a received observation. Request intervals
end when their client receives a response. Missing request endings are
`incomplete`; their displayed end is the last captured event, not a measured
completion. Threaded foreground synthesis and asynchronous S2 use the same clock.

Kinds include `request`, `reasoning_progress`, `final_delta`, `s1_control`,
`command_ready`, `command_forwarded`, `media`, `error`, and `run_end`.
Reasoning deltas store a cumulative `characters` count per `request`, never
internal reasoning text. Final deltas can store final answer `text`.

## Audio

Each media object has a unique `id`, `label`, `role` (`input` or `generated`),
`duration` in audio seconds, `data_uri` (embedded base64 WAV) and optional
`waveform` array of normalized absolute sample peaks. `anchor` is seconds on
the driver clock when the input file was submitted or output waveform became
available. An absent anchor is `null`. Remote media URLs are rejected.

Audio audition uses **anchor + audio position**. The hatched interval is a
browser replay schedule, not evidence of live audio arrival, codec streaming
or speaker playback. No word timing is inferred from a text response.

## Evidence and export

- `measured`: directly captured client events, with their limitations.
- `illustrative`: invented timestamps/messages, clearly labeled.
- `summary_only`: archived summary/audio with no captured aligned events.

The local DuplexOmni driver flushes `events.jsonl` during the run and exports
`trajectory.json` on exit. Re-export with the dependency-free command:

```bash
python scripts/trajectory.py exp/inference/duplexomni/audio_turn_system2_JOB_ID
```

The exporter embeds clips, excludes internal base64 request bodies, and does
not copy local absolute paths, GPU UUIDs or configuration secrets into the
portable trace. It imposes a 25 MB clip limit; browser imports have a 100 MB
file limit. Published demo tones are generated deterministically by
`site/scripts/build_trajectory.py`; they contain no dataset or private speech.


## Recorded example update (6 October 2026)

The hosted example uses `research/trajectory-example.json`, a reviewed
`duplex-html-example/v1` manifest. Its `waiting_trace` retains the v1 trace
shape with client timestamps rebased to whole-input submission. An event
kind `absence` annotates a period with no S1 request, verified against the
request inventory; it is not an active request or measured generation.
The `reasoning` lane plots received character counts sampled at half-second
bins. No internal reasoning or audio is published.

The separate `continuation` payload has cases and per-turn generated tts,
asr/control fields, 480 ms input-audio progress and measured request-plus-RPC
durations. Its chunk axis is not a wall clock or acoustic alignment. There
is no fabricated time bridge between the two jobs. S1 transcription and
speech text are displayed separately, including empty tts fields.


## Content blocks and guidance delivery (7 October 2026)

Rows are ordered User, S1, S2, Talker, followed by reasoning progress and control observations. Request blocks show the returned speech text at the response boundary; empty tts is labeled `(silent)`. That label is a text state, not an acoustic measurement. User recording bars represent browser audition duration at submission, with an explicitly labeled ASR excerpt rather than word-level timing. Buffered `final_delta` text is distinct from `command_forwarded` guidance delivered to S1. The older continuation matrix has silent user input, replayed S2 guidance once, and no Talker invocation; its missing waveform is explicitly labeled.


## Continuous run 1816185

The default trace now shows the completed one-A100 continuous experiment.
A dashed User band denotes the interval whose submitted test packets were
all digital silence; it is not a measured continuous microphone interval.
`guidance_state` bands show the latest delivered S2 clause retained in S1
context, not continued S2 computation. Raw `final_delta` text remains distinct
from `command_forwarded`. Actual user, full Talker and pre-guidance audio are
included; their text descriptions are intended tts or automatic ASR, never
assumed acoustic word alignment. The recorded pre-guidance tts is empty even
though S1 was called; this is not evidence of a spoken acknowledgment.
