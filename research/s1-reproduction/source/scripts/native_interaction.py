"""Replay native 480 ms audio/control semantics through the actual GPU services.

Uses released System2Agent control methods and S1 control parser, a clocked
input feeder and the released AudioBuffer. Websocket/browser/device transport
is replaced by recorded PCM queues. S2 is the local 4B substitute, not the
paper's Gemini. Stock Talker audio is returned; paired decoding is deferred to CPU diagnostics.
"""
from __future__ import annotations
import asyncio
import base64
import io
import json
import os
from pathlib import Path
import random
import re
import sys
import time

import librosa
import numpy as np
from openai import AsyncOpenAI
import requests
import soundfile as sf
import torch
from system2_smoke import parse_s1
from s1_response_parser import parse_s1_with_audit
from trajectory import Trajectory, export_trace
from controlled_runtime import DisabledReasoner, TaggedAudioBuffer, qualify_runtime, qualify_s1_runtime, s2_control_for_test


def run_native_interaction(root, out, config, trace):
    cfg = config.get('system2', {})
    if cfg:
        os.environ.update(S2_THINK_BASE_URL=f"http://127.0.0.1:{cfg['port']}/v1",
                          S2_MODEL_NAME=cfg['served_model_name'], S2_API_KEY='EMPTY')
    else:
        assert not config.get('runtime_qualification'), 'S2 contention calibration requires an S2 service'
        assert all(c.get('s2_policy') == 'off' for c in config['native_loop']['cases']), 'Missing S2 service requires dispatch-disabled cases'
    sys.path.insert(0, str(root / 'external/duplexomni/inference_framework/realtime_serving'))
    import omni_realtime_server as native
    random.seed(7)

    async def one_case(case):
        random.seed(case.get('seed', 7))
        name = case['name']
        folder = out / name
        folder.mkdir(exist_ok=True)
        capture = Trajectory(folder, origin=trace.origin)
        origin = time.monotonic()
        policy = case.get('s2_policy', 'model')
        controlled = 's2_policy' in case
        result = {'name': name, 'gpus': config['gpus'], 'gpu_type': config.get('gpu_type','A100 80 GB'), 'turns': [], 's2_requests': [],
                  'audio_chunks': [], 'deliveries': [], 'controls': [], 'delegation': policy,
                  's2_loaded': bool(cfg),
                  'history_serialization': config['native_loop'].get('history_serialization','json'),
                  'temperature': case.get('temperature',config['native_loop'].get('temperature',.8)),
                  'scope': 'Native audio/control replay with stock Talker; simulated PCM transport, no physical playback recording. '+('Local 4B S2 service loaded.' if cfg else 'No S2 service loaded or called.')}
        x, sr = sf.read(root / case['audio'], dtype='float32')
        if x.ndim != 1:
            raise ValueError('Native input must be mono')
        if sr != 24000:
            x = librosa.resample(x, orig_sr=sr, target_sr=24000)
        frames = [np.pad(x[i:i+11520], (0, max(0,11520-len(x[i:i+11520])))) for i in range(0,len(x),11520)]
        gated = [native.apply_noise_gate((np.clip(f,-1,1)*32767).astype('<i2').tobytes(), native.SILENCE_THRESHOLD) for f in frames]
        correction = []
        processing_bound = case.get('max_turns',len(gated)+case['silent_tail_chunks'])
        if case.get('interrupt_audio'):
            y, rate = sf.read(root / case['interrupt_audio'], dtype='float32')
            assert y.ndim == 1 and rate == 24000
            correction = [native.apply_noise_gate((np.clip(np.pad(y[i:i+11520], (0,max(0,11520-len(y[i:i+11520])))),-1,1)*32767).astype('<i2').tobytes(),native.SILENCE_THRESHOLD) for i in range(0,len(y),11520)]
            result['interruption'] = {'status': 'not_triggered', 'required_nonsilent_playback_seconds': case.get('interrupt_after_speech_seconds', .6)}
        sf.write(folder/'input.wav', np.concatenate([np.frombuffer(p,dtype='<i2') for p in gated]), 24000, subtype='PCM_16')
        capture.media('user',folder/'input.wav','User packets after native noise gate',role='input',duration=len(gated)*.480)
        queue = asyncio.Queue()
        speech_queue = asyncio.Queue()
        input_packets, output_packets = [], []
        source_parts = []
        playback_records = []
        spoken_seconds = 0.0
        last_speech_played = float('-inf')
        input_content_end = len(gated)*.480
        running = True
        session_id = f"native_{os.environ.get('SLURM_JOB_ID','local')}_{name}"

        class Reasoner(native.System2Agent):
            def get_new_commands(self, chunk):
                if controlled:
                    # One complete clause per S1 tick; no randomized 0.5–1 s
                    # presentation cooldown in the controlled handoff test.
                    return self.output_commands.popleft() if self.output_commands else ''
                return super().get_new_commands(chunk)

            async def _continuous_thinking(self):
                number = len(result['s2_requests'])
                request = {'index': number, 'status': 'running', 'start_seconds': time.monotonic()-capture.origin,
                           'reasoning_characters': 0, 'commands': [], 'final_text': '', 'model': cfg['repo']}
                result['s2_requests'].append(request)
                span = f's2-{number}'
                capture.begin('system2',span,'S2 request from native THINK',{'index': number})
                full = ''
                match_end = 0
                stream = None
                try:
                    stream = await self.client.chat.completions.create(model=cfg['served_model_name'], messages=self.history,
                        stream=True, stream_options={'include_usage':True}, temperature=cfg.get('temperature',1.0),
                        extra_body={'top_k':20}, max_tokens=cfg['max_tokens'])
                    async for chunk in stream:
                        if self.should_stop:
                            request['status'] = 'stopped_by_control'
                            break
                        if chunk.usage:
                            request['usage'] = chunk.usage.model_dump()
                        if not chunk.choices:
                            continue
                        delta = chunk.choices[0].delta.model_dump()
                        if chunk.choices[0].finish_reason:
                            request['finish_reason']=chunk.choices[0].finish_reason
                        thought = delta.get('reasoning') or delta.get('reasoning_content') or ''
                        if thought:
                            request['reasoning_characters'] += len(thought)
                            capture.mark('system2','reasoning_progress','S2 private reasoning count',
                                {'request':span,'characters':request['reasoning_characters']})
                        content = chunk.choices[0].delta.content or ''
                        if content:
                            full += content
                            if '<think>' in full or '</think>' in full:
                                full = '[Unexpected reasoning marker redacted]'
                                raise RuntimeError('Reasoning exposed in content channel')
                            capture.mark('system2','final_delta','S2 streamed final text',{'request':span,'text':full})
                            for match in re.finditer(r'【([^【】]+)】',full[match_end:]):
                                command = '【'+match.group(1).strip()+'】'
                                if command == '【】':
                                    continue
                                self.output_commands.append(command)
                                request['commands'].append(command)
                                ready_at = capture.mark('control','command_ready','Complete clause queued',{'request':span,'command':command})
                                request.setdefault('command_ready_records',[]).append({'command':command,'ready_seconds':ready_at})
                            matches = list(re.finditer(r'【([^【】]+)】',full))
                            if matches:
                                match_end = matches[-1].end()
                    if request['status'] == 'running':
                        request['status'] = ('no_guidance_token_limit' if request.get('finish_reason')=='length' and not request['commands']
                                             else 'completed_with_guidance' if request['commands'] else 'completed_without_guidance')
                    if full:
                        self.history.append({'role':'assistant','content':full})
                except asyncio.CancelledError:
                    request['status'] = 'cancelled_by_control'
                    raise
                except Exception as exc:
                    request.update(status='failed',error=f'{type(exc).__name__}: {exc}')
                    raise
                finally:
                    if stream is not None:
                        await stream.close()
                    request.update(final_text=full,end_seconds=time.monotonic()-capture.origin)
                    request['wall_seconds'] = request['end_seconds']-request['start_seconds']
                    capture.end('system2',span,'S2 stream ended',request)
                    self.is_thinking = False
                    self.should_stop = False

        controller = native.RealtimeSession.__new__(native.RealtimeSession)
        controller.s2_agent = DisabledReasoner() if policy == 'off' else Reasoner()
        if controller.s2_agent.client is not None and cfg.get('system_prompt'):
            controller.s2_agent.history = [{'role':'system','content':cfg['system_prompt']}]
        controller.drop_agent_audio = False
        controller.playback_buffer = TaggedAudioBuffer() if controlled else native.AudioBuffer()
        async def send_json(data):
            capture.mark('control','native_event','Native control/text event',data)
        controller._send_json = send_json

        # Warm lazy audio/codec kernels with a separate silent session. No
        # warmup assistant history or reference response enters the user case.
        for warm_index in range(config['native_loop'].get('warmup_turns', 0)):
            before = time.monotonic()
            payload = {'model': str(root/'models/duplexomni'), 'session_id': session_id+'_warmup',
                'messages': [{'role': 'system', 'content': case.get('system_prompt',native.S1_SYSTEM_PROMPT)},
                    {'role': 'user', 'content': [
                        {'type':'text','text':"{'audio_input': '"},
                        {'type':'input_audio','input_audio':{'data':native.pcm_to_b64_wav(bytes(23040)),'format':'wav'}},
                        {'type':'text','text':"', 'from_s2': ''}"}]}], 'max_tokens':256, 'temperature':0}
            reply = await asyncio.to_thread(requests.post,'http://127.0.0.1:21991/internal/chat_turn',json=payload,timeout=600)
            reply.raise_for_status()
            wave = await asyncio.to_thread(requests.post,f'http://127.0.0.1:21992/internal/talker/turn/{session_id}_warmup',
                data=reply.content,headers={'content-type':'application/octet-stream'},timeout=600)
            wave.raise_for_status()
            result.setdefault('warmup', []).append({'index':warm_index,'wall_seconds':time.monotonic()-before})
        origin = time.monotonic()

        background_task = None
        load_ready = asyncio.Event()
        async def background_s2_load():
            client = AsyncOpenAI(base_url=f"http://127.0.0.1:{cfg['port']}/v1", api_key='EMPTY')
            result['calibration_s2_load'] = []
            try:
                while running:
                    record = {'start_seconds':time.monotonic()-capture.origin,'tokens':0}
                    result['calibration_s2_load'].append(record)
                    stream = await client.chat.completions.create(model=cfg['served_model_name'],stream=True,
                        stream_options={'include_usage':True},max_tokens=256,temperature=0,
                        messages=[{'role':'user','content':'Briefly work out 17 times 23, then subtract 42. Explain your calculation.'}])
                    try:
                        async for chunk in stream:
                            if chunk.choices:
                                load_ready.set()
                            if chunk.usage:
                                record['usage'] = chunk.usage.model_dump()
                    finally:
                        await stream.close()
                        record['end_seconds'] = time.monotonic()-capture.origin
            finally:
                await client.close()
        if case.get('calibration_s2_load'):
            background_task = asyncio.create_task(background_s2_load())
            ready_task = asyncio.create_task(load_ready.wait())
            done, _ = await asyncio.wait([background_task,ready_task],timeout=60,return_when=asyncio.FIRST_COMPLETED)
            if background_task in done:
                await background_task
                raise RuntimeError('Calibration S2 load exited before first streamed token')
            if ready_task not in done:
                ready_task.cancel()
                background_task.cancel()
                await asyncio.gather(ready_task,background_task,return_exceptions=True)
                raise TimeoutError('Calibration S2 load produced no streamed token')
            origin = time.monotonic()

        async def feeder():
            nonlocal input_content_end
            i = 0
            correction_index = None
            while running:
                part = 'initial' if i < len(gated) else 'silence'
                packet = gated[i] if i < len(gated) else bytes(23040)
                if correction and i >= len(gated):
                    can_finish_correction = i+len(correction)+case.get('min_post_interrupt_chunks',16) <= processing_bound
                    if correction_index is None and can_finish_correction and spoken_seconds >= case.get('interrupt_after_speech_seconds',.6) and time.monotonic()-last_speech_played < .12:
                        correction_index = 0
                        result['interruption'].update(status='triggered_during_playback',input_packet=i,
                            start_seconds=time.monotonic()-capture.origin,played_speech_seconds=spoken_seconds,
                            epoch_before_input=controller.playback_buffer.epoch)
                        capture.mark('input','user_interruption','User correction begins during requested speech playback',result['interruption'])
                    if correction_index is not None and correction_index < len(correction):
                        packet = correction[correction_index]
                        part = 'interruption'
                        correction_index += 1
                        input_content_end = (i+1)*.480
                now = time.monotonic()
                input_packets.append((now-origin,packet))
                source_parts.append(part)
                await queue.put((i,packet,now-capture.origin,part))
                i += 1
                await asyncio.sleep(max(0,origin+i*.480-time.monotonic()))

        async def playback():
            nonlocal spoken_seconds, last_speech_played
            step = config['native_loop'].get('playback_packet_seconds',.480)
            count = round(step*24000)*2
            next_due = origin
            while running:
                packet = await controller.playback_buffer.pop(count)
                now = time.monotonic()
                emitted_at = max(now-origin,output_packets[-1][0]+step) if output_packets else now-origin
                output_packets.append((emitted_at,packet))
                if controlled:
                    tags = controller.playback_buffer.last_pop_tags
                    rms = float(np.sqrt(np.mean((np.frombuffer(packet,dtype='<i2').astype('float32')/32768)**2)))
                    requested = any(t['chunk'] < len(result['turns']) and result['turns'][t['chunk']]['fields'].get('tts','').strip() for t in tags)
                    if requested and rms > 1e-3:
                        spoken_seconds += step
                        last_speech_played = now
                    playback_records.append({'at':now-capture.origin,'replay_at':emitted_at,'rms':rms,'requested_speech':bool(requested),
                        'tags':tags,'scheduler_lateness_seconds':max(0,now-next_due)})
                next_due += step
                # A stall leaves a measured gap. Ordinary sub-packet scheduling
                # jitter does not make the replay overwrite previously emitted PCM.
                if next_due < now:
                    next_due = now+step
                await asyncio.sleep(max(0,next_due-time.monotonic()))

        async def speech():
            index = 0
            while True:
                item = await speech_queue.get()
                if item is None:
                    return
                chunk, blob, fields, queued_at, epoch = item
                if controlled and epoch != controller.playback_buffer.epoch:
                    result['audio_chunks'].append({'chunk':chunk,'tts':fields.get('tts',''),'epoch':epoch,
                        'queued_seconds':queued_at,'start_seconds':time.monotonic()-capture.origin,
                        'end_seconds':time.monotonic()-capture.origin,'dropped_by_STOP':True,'status':'obsolete_queued_work_skipped'})
                    continue
                span = f'talker-{chunk}'
                capture.begin('talker',span,'Stock Talker chunk',{'chunk':chunk,'tts':fields.get('tts','')})
                before = time.monotonic()
                response = await asyncio.to_thread(requests.post,f'http://127.0.0.1:21992/internal/talker/turn/{session_id}',
                    data=blob,headers={'content-type':'application/octet-stream'},timeout=600)
                response.raise_for_status()
                meta = json.loads(response.headers.get('X-Talker-Meta','{}'))
                record = {'chunk':chunk,'tts':fields.get('tts',''),'start_seconds':before-capture.origin,
                          'end_seconds':time.monotonic()-capture.origin,'meta':meta,
                          'queued_seconds':queued_at,'queue_delay_seconds':before-capture.origin-queued_at,
                          'epoch':epoch,'dropped_by_STOP':controller.drop_agent_audio or (controlled and epoch != controller.playback_buffer.epoch)}
                if response.content:
                    path = folder / f'talker_{index:03d}.wav'
                    path.write_bytes(response.content)
                    wave,rate = sf.read(path,dtype='float32')
                    record.update(file=path.name,seconds=len(wave)/rate,rms=float(np.sqrt(np.mean(wave**2))))
                    if not record['dropped_by_STOP']:
                        record['buffer_bytes_before_push'] = await controller.playback_buffer.bytes_len()
                        pcm = native.stretch_pcm_to_chunk(native.wav_bytes_to_pcm(response.content))
                        if controlled:
                            accepted = await controller.playback_buffer.push_tagged(pcm,epoch,chunk)
                            record['dropped_by_STOP'] = not accepted
                        else:
                            await controller.playback_buffer.push(pcm)
                        record['buffer_bytes_after_push'] = await controller.playback_buffer.bytes_len()
                result['audio_chunks'].append(record)
                capture.end('talker',span,'Stock Talker waveform returned',record)
                index += 1

        tasks = [asyncio.create_task(feeder()),asyncio.create_task(playback()),asyncio.create_task(speech())]
        messages = [{'role':'system','content':case.get('system_prompt',native.S1_SYSTEM_PROMPT)}]
        forced_anchor_pair = None
        try:
            max_turns = processing_bound
            for index in range(max_turns):
                thinking_task = controller.s2_agent.thinking_task
                if thinking_task is not None and thinking_task.done() and not thinking_task.cancelled():
                    await thinking_task  # Provider failures are not successful handoff.
                if background_task is not None and background_task.done():
                    await background_task
                    raise RuntimeError('S2 calibration load exited unexpectedly')
                if tasks[2].done():
                    await tasks[2]
                    raise RuntimeError('Talker worker exited early')
                packet_index,packet,submitted,part = await queue.get()
                command = controller.s2_agent.get_new_commands(index)
                ready_command = command
                if controlled:
                    command = command.removeprefix('【').removesuffix('】')
                if command:
                    result['deliveries'].append({'chunk':index,'command':command,'at':time.monotonic()-capture.origin})
                    if controlled:
                        ready = next((r for request in result['s2_requests'] for r in request.get('command_ready_records',[])
                                      if r['command']==ready_command and not r.get('delivered')),None)
                        if ready is not None:
                            ready['delivered'] = True
                            result['deliveries'][-1].update(ready_seconds=ready['ready_seconds'],
                                dispatch_delay_seconds=result['deliveries'][-1]['at']-ready['ready_seconds'])
                    capture.mark('control','command_forwarded','S2 clause delivered to S1',result['deliveries'][-1])
                messages.append({'role':'user','content':[
                    {'type':'text','text':"{'audio_input': '"},
                    {'type':'input_audio','input_audio':{'data':native.pcm_to_b64_wav(packet),'format':'wav'}},
                    {'type':'text','text':"', 'from_s2': "+repr(command)+"}"}]})
                keep = config['native_loop']['history_turns']
                if len(messages) > 2*keep:
                    messages = messages[:1]+messages[-(2*keep-1):]
                    if forced_anchor_pair is not None and not any('[THINK]' in m['content'] for m in messages if m['role']=='assistant'):
                        # Preserve the actual intervened user/assistant pair;
                        # discard two extra old ticks rather than lose the
                        # required THINK state while S2 is still working.
                        messages = messages[:1]+forced_anchor_pair+messages[-(2*keep-3):]
                        capture.mark('control','preserve_think_state','Retain forced THINK pair in bounded history',{'keep_turns':keep})
                    capture.mark('control','history_trim','Bounded 4096-token replay history',{'keep_turns':keep})
                before = time.monotonic()
                pending = controller.s2_agent.is_thinking
                span = f's1-{index}'
                capture.begin('thinker',span,'Native 480 ms S1 request',{'chunk':index,'from_s2':command,'s2_pending':pending,
                    'input_submitted_seconds':submitted,'input_queue_delay_seconds':before-capture.origin-submitted})
                response = await asyncio.to_thread(requests.post,'http://127.0.0.1:21991/internal/chat_turn',timeout=600,
                    json={'model':str(root/'models/duplexomni'),'session_id':session_id,'messages':messages,
                          'max_tokens':config['native_loop'].get('max_new_tokens',999),
                          'temperature':case.get('temperature',config['native_loop'].get('temperature',.8))})
                response.raise_for_status()
                rpc_finished = time.monotonic()
                internal = await asyncio.to_thread(torch.load,io.BytesIO(response.content),map_location='cpu',weights_only=False) if controlled else torch.load(io.BytesIO(response.content),map_location='cpu',weights_only=False)
                raw = internal['response']['choices'][0]['message']['content']
                try:
                    fields, parser_audit = parse_s1_with_audit(raw)
                except ValueError:
                    with (folder/'response_parse.jsonl').open('a') as handle:
                        handle.write(json.dumps({'chunk':index,'method':'rejected','raw_model_response':raw},ensure_ascii=False)+'\n')
                    raise
                if parser_audit['repaired_keys']:
                    with (folder/'response_parse.jsonl').open('a') as handle:
                        handle.write(json.dumps({'chunk':index,**parser_audit,'raw_model_response':raw,'parsed_fields':fields},ensure_ascii=False)+'\n')
                    capture.mark('control','response_format_repair','Known S1 field-key quote repaired',{'chunk':index,**parser_audit})
                record = {'chunk':index,'fields':fields,'from_s2':command,'s2_pending_at_start':pending,
                          's2_pending_at_response':controller.s2_agent.is_thinking,
                          'start_seconds':before-capture.origin,'end_seconds':time.monotonic()-capture.origin,
                          'input_submitted_seconds':submitted,
                          'input_part':part,'parser':parser_audit,'rpc_seconds':rpc_finished-before,
                          'deserialize_seconds':time.monotonic()-rpc_finished,
                          'input_rms':float(np.sqrt(np.mean((np.frombuffer(packet,dtype='<i2').astype('float32')/32768)**2)))}
                result['turns'].append(record)
                capture.end('thinker',span,'Native S1 fields returned',fields|record)
                effective = s2_control_for_test(fields,policy,index,len(gated)-1)
                effective_raw = json.dumps(effective,ensure_ascii=False) if controlled or parser_audit['repaired_keys'] else raw
                if controlled:
                    record['effective_control_fields'] = effective
                    if effective.get('system2_control') != fields.get('system2_control'):
                        capture.mark('control','test_intervention','Explicit S2 policy intervention',{
                            'chunk':index,'policy':policy,'model_control':fields.get('system2_control',''),
                            'effective_control':effective.get('system2_control','')})
                # Released inference retains the original response in history.
                # Dispatch suppression is a controller action; its altered JSON
                # must not silently replace the model's conversation context.
                history_raw = raw if config['native_loop'].get('history_serialization','json') == 'raw' else effective_raw
                messages.append({'role':'assistant','content':history_raw})
                if policy == 'force_once_after_input' and index == len(gated)-1:
                    forced_anchor_pair = messages[-2:]
                epoch_before = controller.playback_buffer.epoch if controlled else 0
                await controller._parse_and_execute_s1(effective_raw,index)
                record['control_completed_seconds'] = time.monotonic()-capture.origin
                if controlled and controller.playback_buffer.epoch != epoch_before:
                    controller.playback_buffer.clear_events[-1].update(chunk=index,at=record['control_completed_seconds'])
                    capture.mark('control','stop_buffer_invalidation','STOP clears buffered and invalidates older synthesis',
                        controller.playback_buffer.clear_events[-1] | {'chunk':index})
                if fields.get('tts_control') or fields.get('system2_control'):
                    result['controls'].append({'chunk':index,'tts_control':fields.get('tts_control',''),
                                               'system2_control':fields.get('system2_control','')})
                await speech_queue.put((index,response.content,fields,time.monotonic()-capture.origin,
                                        controller.playback_buffer.epoch if controlled else 0))
                if index % config['native_loop'].get('save_every_n_turns',1) == 0:
                    (folder/'native_summary.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
            await speech_queue.put(None)
            await tasks[2]
            # Capture the remaining simulated playback instead of truncating it.
            while await controller.playback_buffer.bytes_len():
                await asyncio.sleep(.480)
            result['status'] = 'completed_content_review_required'
        except BaseException as exc:
            result.update(status='failed',error=f'{type(exc).__name__}: {exc}')
            raise
        finally:
            await controller.s2_agent.trigger_wait()
            if controller.s2_agent.thinking_task:
                await asyncio.gather(controller.s2_agent.thinking_task,return_exceptions=True)
            if controller.s2_agent.client is not None:
                await controller.s2_agent.client.close()
            running = False
            if background_task is not None:
                background_task.cancel()
                await asyncio.gather(background_task,return_exceptions=True)
            for task in tasks:
                if not task.done():
                    task.cancel()
            await asyncio.gather(*tasks,return_exceptions=True)
            result['wall_seconds'] = time.monotonic()-origin
            if correction:
                result['interruption'].update(expected_packets=len(correction),processed_packets=sum(t['input_part']=='interruption' for t in result['turns']))
            if policy == 'off' and result['s2_requests']:
                raise AssertionError('Disabled S2 test unexpectedly dispatched S2')
            result['generated_asr'] = ''.join(t['fields'].get('asr','') for t in result['turns'])
            result['generated_tts'] = ''.join(t['fields'].get('tts','') for t in result['turns'])
            result['tts_while_s2_pending'] = ''.join(t['fields'].get('tts','') for t in result['turns'] if t['s2_pending_at_start'])
            # Replay exactly the packets emitted by the simulated output buffer.
            length = max((round(at*24000)+len(packet)//2 for at,packet in input_packets+output_packets),default=0)
            combined = np.zeros((length,2),dtype='int16')
            for channel,packets in enumerate((input_packets,output_packets)):
                for at,packet in packets:
                    pos = round(at*24000)
                    combined[pos:pos+len(packet)//2,channel] = np.frombuffer(packet,dtype='<i2')
            sf.write(folder/'conversation_replay.wav',combined,24000,subtype='PCM_16')
            sf.write(folder/'playback.wav',combined[:,1],24000,subtype='PCM_16')
            if controlled:
                sf.write(folder/'input.wav',combined[:,0],24000,subtype='PCM_16')
                result['playback_packets'] = playback_records
                result['stop_events'] = controller.playback_buffer.clear_events
                result['input_parts'] = source_parts
            capture.media('conversation',folder/'conversation_replay.wav','User left + stock Talker right · simulated transport replay',duration=length/24000)
            capture.media('playback',folder/'playback.wav','Exact packets from simulated Talker playback buffer',duration=length/24000)
            waves = [sf.read(folder/a['file'],dtype='float32')[0] for a in result['audio_chunks'] if a.get('file')]
            if waves:
                sf.write(folder/'stock_concatenated.wav',np.concatenate(waves),24000,subtype='PCM_16')
            result.update(input_seconds=input_content_end,source_initial_audio_seconds=len(x)/sr,playback_seconds=length/24000,
                generated_audio_seconds=sum(a.get('seconds',0) for a in result['audio_chunks']))
            (folder/'native_summary.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
            (folder/'summary.json').write_text(json.dumps({'model':'DuplexOmni','job_id':os.environ.get('SLURM_JOB_ID'),
                'gpus':config['gpus'],'mode':'native_audio_control_replay','status':result.get('status','failed'),'wall_seconds':result['wall_seconds']})+'\n')
            capture.close()
            portable=export_trace(folder)
            for media in portable['media']:
                if media['id'] in ('user','conversation','playback'):
                    media['anchor']=origin-capture.origin
                    media['text_scope']='Recorded simulated PCM transport, not a physical microphone or loudspeaker recording'
            portable['lanes'].append({'id':'reasoning','label':'S2 reasoning progress'})
            for event in portable['events']:
                if event['kind']=='reasoning_progress':event['lane']='reasoning'
            for turn in result['turns']:
                portable['events'].append({'id':f"input-{turn['chunk']}",'lane':'input','kind':'input_span',
                    'start':turn['input_submitted_seconds'],'end':turn['input_submitted_seconds']+.480,
                    'label':'User packet · ASR returned later',
                    'details':{'text':turn['fields'].get('asr','').strip() or ('(silent)' if not turn['input_rms'] else '(audio; no ASR text)'),
                               'scope':'ASR returned for this request; not acoustic word alignment','rms':turn['input_rms']}})
            if controlled:
                for i, packet in enumerate(playback_records):
                    if packet['requested_speech'] and packet['rms'] > 1e-3:
                        portable['events'].append({'id':f'played-{i}','lane':'audio','kind':'playback_packet',
                            'start':packet['at'],'end':packet['at']+config['native_loop'].get('playback_packet_seconds',.480),
                            'label':'Requested speech emitted by software playback buffer',
                            'details':{'rms':packet['rms'],'source_chunks':packet['tags'],
                                       'scope':'Software PCM dequeue, not physical loudspeaker timing'}})
            portable['metadata'].update(content_blocks=True,output_text=result['generated_tts'],gpu_type=result['gpu_type'])
            speech_gpu = 0 if config['gpus'] == 1 else config.get('thinker_tp',1)
            for lane in portable['lanes']:
                if lane['id'] == 'thinker': lane['label'] = f"S1 · Thinker · GPU(s) {list(range(config.get('thinker_tp',1)))}"
                if lane['id'] == 'talker': lane['label'] = f"Talker + codec · GPU {speech_gpu}"
                if lane['id'] == 'system2': lane['label'] = f"S2 · GPU {config.get('s2_gpu',speech_gpu)}"
            if not cfg:
                portable['lanes'] = [lane for lane in portable['lanes'] if lane['id'] not in ('system2','reasoning')]
            portable['limitations']=['480 ms user input and simulated output-buffer packets use a measured client clock; no physical microphone or speaker was recorded.',
                (f"Local S2 backend {cfg['repo']} differs from the paper backend; graph settings are recorded in configuration." if cfg else
                 'S2 service absent and dispatch disabled; this case tests S1 only.'),
                'ASR shown for a packet is returned after processing and can contain delayed transcription; no word alignment is claimed.',
                f"S2 policy: {policy}. Explicit forced/disabled controls are logged separately from model outputs; source assistant answers are never supplied.",
                (f"Allocation: {config['gpus']} {result['gpu_type']}; Thinker GPU(s) {list(range(config.get('thinker_tp',1)))}, speech GPU {speech_gpu}" +
                 (f", S2 GPU {config.get('s2_gpu',speech_gpu)}." if cfg else '; S2 absent.') +
                 ' Decoder mode is recorded in configuration; saved codes support a later matched comparison.'),
                'History is bounded to 40 turns for the 4096-token context; no paper realtime-speed claim.']
            portable['events'].sort(key=lambda e:(e['start'],e['id']))
            (folder/'trajectory.json').write_text(json.dumps(portable,ensure_ascii=False,indent=2)+'\n')
        return result

    async def all_cases():
        results = []
        if config.get('runtime_qualification'):
            client = AsyncOpenAI(base_url=f"http://127.0.0.1:{cfg['port']}/v1", api_key='EMPTY')
            before = time.monotonic()
            try:
                reply = await client.chat.completions.create(model=cfg['served_model_name'],max_tokens=64,temperature=0,
                    messages=[{'role':'user','content':'Reply with the word ready.'}])
                (out/'system2_warmup.json').write_text(json.dumps({'wall_seconds':time.monotonic()-before,
                    'usage':reply.usage.model_dump() if reply.usage else None,'scope':'Separate warmup; no content delivered to S1'})+'\n')
            finally:
                await client.close()
            for case in config['native_loop']['calibration_cases']:
                results.append(await one_case(case))
            qualification = qualify_runtime(results[0],results[1],config['runtime_qualification'])
            qualification.update(job_id=os.environ.get('SLURM_JOB_ID'),gpus=config['gpus'],
                s2_gpu=config.get('s2_gpu',config.get('thinker_tp',1)),
                scope='Matched client-observed S1/speech timing under bounded synthetic S2 load; no behavioral pass.')
            (out/'runtime_qualification.json').write_text(json.dumps(qualification,indent=2)+'\n')
            print(json.dumps({'runtime_qualification':qualification}),flush=True)
            if not qualification['qualified']:
                return results
        for case in config['native_loop']['cases']:
            result = await one_case(case)
            results.append(result)
            if case.get('qualify_s1_runtime'):
                qualification = qualify_s1_runtime(result,config['s1_runtime_qualification'])
                qualification.update(job_id=os.environ.get('SLURM_JOB_ID'),gpus=config['gpus'],
                    scope='Measured S1-only pacing before interruption; no S2 service and no behavioral pass inferred.')
                (out/'runtime_qualification.json').write_text(json.dumps(qualification,indent=2)+'\n')
                if not qualification['qualified']:
                    return results
                has_speech = bool(result['generated_tts'].strip() and any(p['requested_speech'] and p['rms']>1e-3 for p in result['playback_packets']))
                gate = {'qualified':has_speech,'status':'audible_baseline' if has_speech else 'initial_s1_response_missing',
                    'scope':'Requires actual requested nonquiet playback before a barge-in can be scored; content still needs review.'}
                (out/'initial_response_gate.json').write_text(json.dumps(gate,indent=2)+'\n')
                if not has_speech:
                    return results
        return results

    return asyncio.run(all_cases())
