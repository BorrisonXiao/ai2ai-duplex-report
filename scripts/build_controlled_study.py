"""Build the reviewable setup page; queued work is never presented as results."""
from html import escape
import json
import os
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(Path(os.environ.get('HTML_REPORT_SKILL_DIR',Path.home()/'.codex/skills/html-report'))))
import htmlkit as hk


def table(headers,rows):
    return '<div class="study-table-scroll"><table><thead><tr>'+''.join('<th>'+escape(h)+'</th>' for h in headers)+'</tr></thead><tbody>'+''.join('<tr>'+''.join('<td>'+escape(str(v))+'</td>' for v in row)+'</tr>' for row in rows)+'</tbody></table></div>'


def main():
    plan=json.loads((ROOT/'research/controlled-study-plan.json').read_text())
    assert plan['status']=='queued_no_gpu_results'
    body=hk.hero('Controlled experiment setup · 7 October 2026','Separate S2 handoff from S1 interruption','Four matched conditions isolate system handoff and interruption behavior. CPU preparation checks passed; the GPU study is queued and has no behavioral results yet.')
    body+=hk.section('1 · Study status',body='<p><a href="index.html">All experiments</a> · <a href="trajectory.html">Previous measured trajectory grid</a> · <a href="interaction-review.html">Previous evidence audit</a> · <a href="../research/controlled-study-plan.json">Exact setup record</a></p>'+hk.finding('GPU job <b>'+plan['gpu_job_id']+'</b> is queued for <b>2 × H100 SXM 80 GB</b>. CPU follow-up <b>'+plan['cpu_followup_job_id']+'</b> waits for it to finish. At the recorded status check, zero GPUs were allocated. Queue status is a dated snapshot.',ok=False))
    rows=[('Single request, S2 disabled',plan['cases'][0]['initial_text'],'No S2 requests; reference for S1 response.'),
          ('Same request, S2 forced once',plan['cases'][1]['initial_text'],'Start S2 after the complete request; verify guidance delivery, continuous S1 activity and audible answer uptake.'),
          ('S1 without interruption',plan['cases'][2]['initial_text'],'S2 disabled; reference for the ongoing answer.'),
          ('S1 with user correction',plan['cases'][3]['initial_text']+' Then: '+plan['cases'][3]['interrupt_text'],'S2 disabled. Begin correction after 0.6 s of requested nonquiet playback, while speech is still playing. Check STOP, obsolete audio and the updated answer.')]
    body+=hk.section('2 · Matched controls',body=hk.labeled_asset(table(['Condition','User input','Purpose'],rows),'Table',1,'Four conditions share the same S1 prompt, temperature, decoding and warmed service configuration. The two interruption conditions share the observation horizon. Forced delegation is an explicit test intervention.')+'<p>S2 uses '+escape(plan['system2_model'])+'. A forced THINK state is recorded separately from the model output and retained in bounded history. Only completed final-answer clauses reach S1; private reasoning is counted. For S1-only conditions, S2 dispatch is disabled in the controller.</p>')
    q=plan['qualification_criteria']
    criteria=[('S1 client latency, p95',f"At most {q['max_p95_s1_seconds']:.3f} s"),
              ('Talker client latency, p95',f"At most {q['max_p95_talker_seconds']:.3f} s"),
              ('Input and speech queue delay',f"At most {q['max_queue_delay_seconds']:.3f} s"),
              ('Added p95 latency during S2 load','At most the larger of 30 ms or 25% of the matched baseline'),
              ('S2 request interval coverage','At least 80% of the measured interval'),
              ('Calibration samples','At least 20 S1 and 20 Talker samples after four initial ticks'),
              ('Playback scheduler lateness, p95','At most 40 ms; playback uses 20 ms packets')]
    body+=hk.section('3 · Qualify infrastructure before behavior',body='<p>Compare the same paced request with and without a bounded background S2 load. Keep Thinker TP1, warm lazy kernels separately, enable Thinker/S2 CUDA graphs, reuse bounded decoder context, and cap CPU thread pools. Measure RPC, deserialization, queueing and playback scheduling separately. Complete clauses are dispatched on the next S1 tick, without the randomized presentation cooldown.</p>'+hk.labeled_asset(table(['Check','Required criterion'],criteria),'Table',2,'The 480 ms input cadence defines the latency budget. These gates qualify the tested allocation before the four behavioral conditions execute; they do not score answer correctness.')+'<p>If the two-GPU baseline passes but S2 contention violates the criteria, the CPU follow-up submits a sequential three-H100 retry with S2 on GPU 2. A failed baseline, provider error or incomplete calibration is retained for diagnosis. Behavioral tests remain blocked until a layout qualifies. Maximum allocation is three GPUs, with no overlap between GPU jobs.</p>')
    v=plan['validation'];r=v['cpu_regression']
    checks=[('Independent input transcription','All reference words present in three complete crops; 0 GPUs'),
            ('Real processor preflight',f"{v['processor_audio_items']} audio items; {v['processor_prompt_plus_response_tokens']} tokens including response allowance, below {v['model_context_tokens']}"),
            ('Forced/disabled S2 scheduling',f"Mocked transport: {r['forced_s2_requests']} S2 request, {r['guidance_deliveries']} complete clauses, {r['s1_calls_while_s2_pending']} S1 calls while S2 was pending"),
            ('Interrupted playback','Mocked transport: all 10 correction packets processed; obsolete audio rejected after STOP'),
            ('Failure and history handling','Provider errors propagate; forced THINK survives bounded-history trimming'),
            ('GPU behavior','Pending; speech content and answer correctness require independent review')]
    body+=hk.section('4 · Preparation evidence',body=hk.labeled_asset(table(['Check','Evidence'],checks),'Table',3,'CPU checks verify input integrity, processing and controller behavior under mocks. They establish no GPU throughput or model-quality result.')+'<p>For the real run, review S2 completion and guidance uptake, played audio, interruption-to-STOP timing, stale audio rejection, recognition and the new answer. Transcription and control fields provide complementary evidence; complete relevant speech remains the behavioral criterion.</p>')
    body+=hk.section('5 · Audio provenance and scope',body='<p>User clips are cropped from FD-Bench CosyVoice2 easy conversations 35 and 48, preserving complete requests and margins. No source assistant answer is fed to a model. These event-aligned controls adapt the source recordings rather than report an official benchmark score. Attribution: <a href="'+plan['source']['url']+'">FD-Bench Audio Input</a>, <a href="'+plan['source']['license_url']+'">NTUitive license</a>. Crop hashes and source turn identifiers are in the setup record.</p><p>The planned replay captures software PCM queues and measured client events. Physical microphone/loudspeaker behavior and autonomous S2 delegation need separate validation.</p>')
    style='<style>.study-table-scroll{max-width:100%;overflow-x:auto}.study-table-scroll table{min-width:650px}.study-table-scroll th,.study-table-scroll td{text-align:left!important}</style>'
    full,_=hk.document('Controlled S2 handoff and S1 interruption study',body,head_html=style)
    (ROOT/'experiments/controlled-study.html').write_text(full)
    print('Built queued setup with four conditions and three labeled tables.')


if __name__=='__main__':main()
