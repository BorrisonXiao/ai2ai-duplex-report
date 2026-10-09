"""Small, independently testable controls for causal audio replay experiments."""
from collections import deque
import asyncio
import statistics


def percentile(values, fraction):
    values = sorted(values)
    if not values:
        raise ValueError('No timing samples')
    position = (len(values)-1)*fraction
    low = int(position)
    return values[low] + (values[min(low+1,len(values)-1)]-values[low])*(position-low)


def qualify_s1_runtime(case, settings):
    """Check S1/speech pacing before an S1-only interruption test."""
    skip = settings.get('skip_initial_turns',4)
    turns = case['turns'][skip:]
    audio = [a for a in case['audio_chunks'] if a['chunk'] >= skip and a.get('file')]
    if not turns or not audio:
        return {'qualified':False,'status':'insufficient_samples','criteria':settings}
    metrics = {
        's1_samples':len(turns),'talker_samples':len(audio),
        'mean_s1_seconds':statistics.mean(t['end_seconds']-t['start_seconds'] for t in turns),
        'p95_s1_seconds':percentile([t['end_seconds']-t['start_seconds'] for t in turns],.95),
        'p95_talker_seconds':percentile([a['end_seconds']-a['start_seconds'] for a in audio],.95),
        'max_input_queue_delay_seconds':max(t['start_seconds']-t['input_submitted_seconds'] for t in turns),
        'max_speech_queue_delay_seconds':max(a.get('queue_delay_seconds',0) for a in audio),
        'p95_playback_scheduler_lateness_seconds':percentile([p['scheduler_lateness_seconds'] for p in case['playback_packets']],.95),
    }
    qualified = (metrics['s1_samples'] >= settings.get('min_samples',20)
        and metrics['talker_samples'] >= settings.get('min_samples',20)
        and metrics['p95_s1_seconds'] <= settings.get('max_p95_s1_seconds',.384)
        and metrics['p95_talker_seconds'] <= settings.get('max_p95_talker_seconds',.384)
        and metrics['max_input_queue_delay_seconds'] <= settings.get('max_queue_delay_seconds',.48)
        and metrics['max_speech_queue_delay_seconds'] <= settings.get('max_queue_delay_seconds',.48)
        and metrics['p95_playback_scheduler_lateness_seconds'] <= settings.get('max_playback_scheduler_p95_seconds',.04))
    return {'qualified':qualified,'status':'qualified' if qualified else 's1_pacing_failed',
        'baseline':metrics,'criteria':settings,'s2_loaded':False}


def qualify_runtime(baseline, loaded, settings):
    """Require pacing headroom and limited contention before behavior tests."""
    skip = settings.get('skip_initial_turns',4)
    def metrics(case):
        turns = case['turns'][skip:]
        audio = [a for a in case['audio_chunks'] if a['chunk'] >= skip and a.get('file')]
        return {
            's1_samples':len(turns),'talker_samples':len(audio),
            'mean_s1_seconds':statistics.mean(t['end_seconds']-t['start_seconds'] for t in turns),
            'p95_s1_seconds':percentile([t['end_seconds']-t['start_seconds'] for t in turns],.95),
            'p95_talker_seconds':percentile([a['end_seconds']-a['start_seconds'] for a in audio],.95),
            'max_input_queue_delay_seconds':max(t['start_seconds']-t['input_submitted_seconds'] for t in turns),
            'max_speech_queue_delay_seconds':max(a.get('queue_delay_seconds',0) for a in audio),
            'p95_playback_scheduler_lateness_seconds':percentile([p['scheduler_lateness_seconds'] for p in case['playback_packets']],.95),
        }
    base, busy = metrics(baseline), metrics(loaded)
    first, last = loaded['turns'][skip]['start_seconds'], loaded['turns'][-1]['end_seconds']
    intervals = sorted((max(first,r['start_seconds']),min(last,r.get('end_seconds',last))) for r in loaded.get('calibration_s2_load',[]))
    coverage, cursor = 0.0, first
    for start, end in intervals:
        start = max(start,cursor)
        if end > start:
            coverage += end-start
            cursor = end
    load_fraction = coverage/(last-first)
    def absolute_pass(m):
        return (m['s1_samples'] >= settings.get('min_samples',20)
            and m['talker_samples'] >= settings.get('min_samples',20)
            and m['p95_s1_seconds'] <= settings.get('max_p95_s1_seconds',.384)
            and m['p95_talker_seconds'] <= settings.get('max_p95_talker_seconds',.384)
            and m['max_input_queue_delay_seconds'] <= settings.get('max_queue_delay_seconds',.480)
            and m['max_speech_queue_delay_seconds'] <= settings.get('max_queue_delay_seconds',.480)
            and m['p95_playback_scheduler_lateness_seconds'] <= settings.get('max_playback_scheduler_p95_seconds',.040))
    base_ok, busy_ok = absolute_pass(base), absolute_pass(busy)
    ratios = {}
    overhead_ok = True
    for key in ['p95_s1_seconds','p95_talker_seconds']:
        ratios[key] = busy[key]/base[key]
        allowance = max(settings.get('max_absolute_extra_latency_seconds',.030),base[key]*settings.get('max_relative_extra_latency',.25))
        overhead_ok &= busy[key]-base[key] <= allowance
    load_ok = load_fraction >= settings.get('min_s2_load_fraction',.80)
    qualified = base_ok and busy_ok and overhead_ok and load_ok
    status = ('qualified' if qualified else 'baseline_infrastructure_failed' if not base_ok
              else 'insufficient_s2_load' if not load_ok else 's2_contention')
    return {'qualified':qualified,'status':status,'baseline':base,'with_s2_load':busy,
            'relative_latency_ratios':ratios,'s2_load_interval_fraction':load_fraction,
            'criteria':settings,'baseline_pass':base_ok,'loaded_absolute_pass':busy_ok,
            'overhead_pass':bool(overhead_ok),'load_coverage_pass':load_ok}


def s2_control_for_test(fields, policy, chunk, final_input_chunk):
    """Return explicit controller/history intervention, preserving model fields."""
    if policy == "model":
        return dict(fields)
    if policy not in ("off", "force_once_after_input"):
        raise ValueError(f"Unknown S2 policy: {policy}")
    effective = dict(fields)
    effective["system2_control"] = "[THINK]" if policy == "force_once_after_input" and chunk == final_input_chunk else ""
    return effective


class TaggedAudioBuffer:
    """PCM queue with atomic STOP invalidation of queued and in-flight audio.

    Every synthesis request carries an epoch captured when it was queued.
    STOP increments the epoch, so an old request cannot be re-enabled by a
    later response's tts. Tags follow the bytes actually emitted by playback.
    """
    def __init__(self):
        self.epoch = 0
        self.blocks = deque()
        self.lock = asyncio.Lock()
        self.last_pop_tags = []
        self.clear_events = []

    async def bytes_len(self):
        async with self.lock:
            return sum(len(data) for data, _ in self.blocks)

    async def clear(self):
        async with self.lock:
            dropped = sum(len(data) for data, _ in self.blocks)
            self.clear_events.append({"old_epoch": self.epoch, "new_epoch": self.epoch + 1, "dropped_bytes": dropped})
            self.epoch += 1
            self.blocks.clear()

    async def push_tagged(self, data, epoch, chunk):
        async with self.lock:
            if epoch != self.epoch:
                return False
            data = data[:len(data) - len(data) % 2]
            if data:
                self.blocks.append((bytes(data), {"epoch": epoch, "chunk": chunk}))
            return True

    async def pop(self, num_bytes):
        async with self.lock:
            output = bytearray()
            tags = []
            while self.blocks and len(output) < num_bytes:
                data, tag = self.blocks.popleft()
                count = min(len(data), num_bytes - len(output))
                offset = len(output)
                output.extend(data[:count])
                tags.append(tag | {"byte_offset": offset, "byte_count": count})
                if count < len(data):
                    self.blocks.appendleft((data[count:], tag))
            self.last_pop_tags = tags
            output.extend(bytes(num_bytes - len(output)))
            return bytes(output)


class DisabledReasoner:
    """Dispatch-disabled S2; preserve S1 parsing without constructing a client."""
    is_thinking = False
    thinking_task = None
    client = None

    def add_context(self, source, text):
        pass

    def get_new_commands(self, chunk):
        return ""

    async def trigger_think(self):
        raise RuntimeError("S2 dispatch disabled: a THINK control escaped the test policy")

    async def trigger_wait(self):
        pass
