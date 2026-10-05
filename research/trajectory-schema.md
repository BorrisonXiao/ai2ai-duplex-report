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
driver origin. A zero-length event is a received observation. Request intervals
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
