"""Render the selected saved-output evaluation checks in plain language."""
from html import escape as e
import json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]


def load():
    return json.loads((ROOT/'research/s1-evaluation/summary.json').read_text())


def render(t):
    data = load()
    body = '<section class="section" id="software-checks"><h2>First implementation: shared S1 evaluation</h2><ul><li>Extract the spoken answer from model-only playback and keep native model text separately.</li><li>Use verified answer facts and explicit reviews; keyword matches alone cannot certify correctness.</li><li>Count recorded native tokens separately and report missing channels or counts clearly.</li><li>Keep saved records when rerunning, and update progress after each example.</li></ul><p><strong>'+str(data['regression']['tests'])+' script checks pass.</strong> They cover silence, missing or partial outputs, capacity failures, unclear ASR, truncation, stale reviews, token counts and the full-question denominator. Those checks use labeled script fixtures; they are not new model outputs.</p></section>'
    body += '<section class="section" id="examples"><h2>Checks on three earlier real S1 outputs</h2><p>The evaluator processes the actual saved model playback and its stored independent transcript. Codex reviews the transcript against the required facts; no new ASR or judge-model inference ran. These are short software checks, excluded from the 105-question study.</p>'
    body += t('Saved S1 outputs used to check the evaluator; two satisfy the request and one is a task failure.',['Saved example','Actual spoken answer','Evaluator result'],[[e(x['id']),e(x['spoken_answer']),('Complete answer' if x['score']==1 else 'Does not answer the request')+'. '+e(x['reason'])] for x in data['examples']])
    for x in data['examples']:
        body += '<details id="'+e(x['id'],quote=True)+'"><summary>'+e(x['id'])+': question, facts and scoring evidence</summary><ul><li><strong>Request:</strong> '+e(x['question'])+'</li><li><strong>Reference:</strong> '+e(x['reference'])+'</li><li><strong>Native text:</strong> '+e(x['native_text'])+'</li><li><strong>Independent speech transcript:</strong> '+e(x['spoken_answer'])+'</li><li><strong>Judgment:</strong> '+e(x['reason'])+'</li><li><strong>Review:</strong> '+e(x['reviewer'])+'</li><li><strong>Native thinking tokens:</strong> N/A; this S1 output has no separate native thinking channel.</li><li><strong>Native answer/output tokens:</strong> unavailable in these saved recordings; ASR words are not substituted.</li><li><a href="'+e(x['source']['page'],quote=True)+'">Play the saved audio</a> · <a href="'+e(x['source']['json'],quote=True)+'">Inspect recorded fields ('+e(x['source']['trace_id'])+')</a></li></ul>'
        body += t('Required-fact checks for '+x['id']+'; word matching flags possible omissions, while the full-answer review determines correctness.',['Required fact','Fact words found','Contradiction flagged'],[[e(f['fact']),('Yes' if f['pattern_match'] else 'No'),('Yes' if f['contradiction_flag'] else 'No')] for f in x['fact_checks']])
        body += '<p>Historical source job '+e(x['source']['job_id'])+': '+str(x['source']['gpus'])+' × '+e(x['source']['gpu_type'])+'. '+e(x['source']['roles'])+' This is not a new GPU allocation.</p><p><a href="research/s1-evaluation/summary.json">Candidate, reference, audio and source checksums</a></p></details>'
    return body+'</section>'
