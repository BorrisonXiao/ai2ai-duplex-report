"""Standalone standard-depth review from the measured interaction grid."""
from html import escape
import json
from pathlib import Path
import sys
import os

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(Path(os.environ.get('HTML_REPORT_SKILL_DIR',Path.home()/'.codex/skills/html-report'))))
import htmlkit as hk


def table(headers, rows):
    return '<table><thead><tr>'+''.join('<th>'+escape(h)+'</th>' for h in headers)+'</tr></thead><tbody>'+''.join('<tr>'+''.join('<td>'+escape(str(v))+'</td>' for v in row)+'</tr>' for row in rows)+'</tbody></table>'


def main():
    grid=json.loads((ROOT/'research/interactive-review.json').read_text())['rows']
    review=json.loads((ROOT/'research/interactive-progress-review.json').read_text())
    body=hk.hero('Standard evidence audit · 7 October 2026','Interactive speech: timing improved, quality still limited','Complete paced input, bounded decoding and warmed H100/CUDA-graph execution recover follow-up recognition and prevent a growing input queue. Some spoken replies remain incomplete or unsupported.')
    body+=hk.section('1 · Scope and evidence',body='<p><a href="trajectory.html">Measured trajectory viewer</a> · <a href="../research/interactive-review.json">Exact grid and transcripts</a></p><p>Published DailyTalk audition, raw CLSP native-loop evidence and six representative local cases. Independent CPU Whisper transcripts and matched-code decodes corroborate saved model fields. Recorded software PCM queues do not establish physical microphone/speaker timing, word alignment or always-on deployment performance.</p>')
    claims=table(['Claim','Verdict','Primary evidence / finding'],[(c['claim'],c['verdict'],c['finding']+' '+ '; '.join(c['evidence'])) for c in review['claims']])
    body+=hk.section('2 · Claims and verdicts',body=hk.labeled_asset(claims,'Table',1,'Evidence-backed verdicts. Recognition, transport and answer correctness are distinct checks.'))
    metrics=table(['Case / job','Allocation','Mean S1 (s)','Packet RTF','Decoder loss (s)'],[(c['name']+' / '+c['job_id'],str(c['gpus'])+' × '+c['hardware'],f"{c['mean_s1_seconds']:.3f}",f"{c['input_packet_rtf']:.3f}",f"{c['codec_duration_loss_seconds']:.6f}") for c in grid])
    body+=hk.section('3 · Derived metrics',body=hk.labeled_asset(metrics,'Table',2,'S1 is client request time. Packet RTF includes intentionally paced silent tail and playback drain. Hardware and graph settings changed together, so their individual contributions are unresolved.')+'<p>Evidence-backed: over 100 chunks, decoder duration loss falls from 2.3125 to 0.023125 seconds. The H100 capability control returns the first requested nonquiet speech after 1.405 seconds; maximum input queue delay is 0.000267 seconds. Whole-case RTF near 1 includes feeder pacing and final drain.</p>')
    chosen=[next(c for c in grid if c['name']=='dailytalk_10s_stock'),next(c for c in grid if c['name']=='dailytalk_full_english_context'),next(c for c in grid if 'capabilities' in c['name'])]
    examples=''
    for number,c in enumerate(chosen,3):
        steps=table(['Step','Observed result'],[('Input',f"{c['input_seconds']:.2f} seconds; actual 480 ms packets"),('S1 ASR',c['generated_asr']),('Generated tts',c['generated_tts']),('Independent audio transcript',c['independent_output_transcript'])])
        examples+=hk.labeled_asset(steps,'Table',number,'Job '+c['job_id']+', '+c['name']+'. Expected: recognize and answer current questions. Actual errors are retained. Automatic transcripts provide content evidence, not word alignment.')
    body+=hk.section('4 · Three representative traces',body=examples)
    body+=hk.section('5 · Failure synthesis',body='<p>Evidence-backed: three of six cases recover all working/budget/money terms. The old recording truncates the money question; whole-file submission cannot test progressive listening. Reset decoding loses duration, while eager A100 Thinker calls exceed the packet interval. Corrected input/decoding and the faster configuration address those mechanisms.</p><p>Evidence-backed: generic prompting invents finance access and unrelated color advice. Capability prompting reduces those claims but leaves partial or unsupported replies. This is a model-quality limitation, not proof that later input was absent.</p><p>Inferred: remaining silence mixes listening states, decoder output and buffer-empty waits. A single amplitude threshold does not identify their individual prevalence. Open questions: sustainable live-device behavior and separate hardware-versus-graph contributions need matched controls.</p>')
    body+=hk.section('6 · Prioritized next steps',body='<ol><li>Keep complete paced input, bounded context and the warmed graph-enabled configuration. Require bounded input queue delay and retain measured gaps in the replay.</li><li>Require complete relevant audible responses for every question, with no invented external capabilities. Check interruption/STOP behavior and text/audio alignment before claiming conversational quality.</li><li>Use matched hardware/graph controls for causal performance claims; the current evidence demonstrates the joint configuration.</li></ol>')
    full,_=hk.document('Interactive speech evidence review',body)
    (ROOT/'experiments/interaction-review.html').write_text(full)
    print('Built standard review with primary claims, three examples and failure synthesis')


if __name__=='__main__': main()
