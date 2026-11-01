"""Current acoustic revisions over the preserved original question library."""
import copy,json
from pathlib import Path
from html import escape as e
ROOT=Path(__file__).resolve().parents[1]
def apply(clips):
 p=ROOT/'research/question-acoustic-bank/review.json'
 if not p.exists():return clips,None
 d=json.loads(p.read_text());assert d['status']=='validated';by={c['catalog_id']:c for c in d['cases'] if c['primary']};out=[]
 for clip in clips:
  c=copy.deepcopy(clip);r=by[c['catalog_id']];c.update(base='../research/question-acoustic-bank/',public_matched=r['question_audio'],public_injected=r['injected_audio'],processed_asr=dict(text=r['asr']['revised']['text'],normalized_wer=r['asr']['revised']['WER']),current_acoustic_revision=True,revision_note=r.get('paired_ASR_review',{}).get('note'))
  # Original speaker references retain their original public location.
  c['public_reference']='../'+clip['base'].strip('/').split('/')[-1]+'/'+clip['public_reference'];c.pop('whisper_text',None);out.append(c)
 return out,d

def alternatives(d,player):
 body='<section class="section" id="alternate-voices"><h2>Six additional published voice versions</h2><p>The three original AMI questions also have Qwen and Chatterbox versions. These receive the same acoustic checks and do not increase the count of 105 distinct questions. All players below use the revised audio.</p>'
 for c in d['cases']:
  if c['primary']:continue
  body+='<article class="catalog-question" id="'+e(c['revision_id'])+'"><h3>'+e(c['meeting']+' · '+c['revision_id'].rsplit('--',1)[-1])+'</h3><p>'+e(c['question'])+'</p>'+player('../research/question-acoustic-bank/'+c['injected_audio'],'Revised inserted question '+c['revision_id'])+'<button class="jump-question" data-start="'+str(c['synthetic_speech_playback_start_seconds'])+'">Play from the question</button><details><summary>Question alone and ASR check</summary>'+player('../research/question-acoustic-bank/'+c['question_audio'],'Revised question alone '+c['revision_id'])+'<p><strong>Parakeet question transcript:</strong> '+e(c['asr']['revised']['text'])+'</p></details></article>'
 return body+'</section>'

def revise_prose(body,d):
 body=body.replace('92 missing question recordings are now added to the existing 13.','The acoustic revision now covers all 105 primary questions and six additional published voice versions.')
 start=body.index('<li><strong>Acoustic matching and insertion.')
 end=body.index('</ol>',start)
 body=body[:start]+'<li><strong>Acoustic matching and insertion.</strong> The current audio uses the requester’s earlier recording level, continuous background texture and bounded spectral equalization (EQ), which adjusts frequency balance, where past paired speech is available. Original PCM before and after each insertion is unchanged. Some clips use actual past room tone; where gap-based background failed screening, stationary noise matches the quietest past-frame spectrum and root-mean-square (RMS) audio level without replaying source words. EQ is reduced or omitted when needed to preserve intelligibility. Sparse-speaker cases are labeled in the data. No room impulse response or added reverberation is used; acoustic matching measurements use only earlier audio.</li><li><strong>Revision verification.</strong> Parakeet transcribes every revised question, its preserved original and the background-only control. These checks guide acoustic selection and are not independent human listening ratings. Old ECAPA values shown below describe the original synthesis, not this acoustic processing.</li>'+body[end:]
 a=body.index('<section class="section" id="checks">');b=body.index('<section class="section" id="listen">',a)
 s=d['summary'];body=body[:a]+'<section class="section" id="checks"><h2>Revised-audio checks</h2><p>All 111 published speech versions preserve the intended wording, insertion timing and original source audio. Parakeet starts with Assistant in '+str(s['revised_cue_first'])+'/111 and gives an exact normalized transcript in '+str(s['revised_exact'])+'/111, compared with '+str(s['original_exact'])+'/111 for the preserved originals. The original proper-name and pronunciation limitations remain visible. Case-by-case paired transcripts and processing fallbacks are recorded below and in the <a href="../research/question-acoustic-bank/review.json">revision data</a>.</p><p>These are ASR-guided acoustic checks. They do not certify human naturalness or the full downstream model evaluation.</p></section>'+body[b:]
 body=body.replace('ECAPA similarity to the separate requester recording:', 'Original-synthesis ECAPA similarity to the separate requester recording:')
 body=body.replace('The same proxy guided selection; human voice review is still required.','The same proxy guided the original selection; it was not rerun after the acoustic revision. Human voice review is still required.')
 body=body.replace('Parakeet transcript:</strong>','Revised-question Parakeet transcript:</strong>')
 body=body.replace('Answer generation remains deferred.','Full-bank model-answer generation remains deferred; the separate stress sweep and pilot responses are in the progress report.')
 body=body.replace('Case, punctuation, common number forms and contractions are normalized. Compare the displayed transcripts for recognizer disagreements.','Case, punctuation and apostrophes are normalized. Spelled numbers, acronym spacing and contraction expansions can still differ; compare the displayed transcripts for recognizer disagreements.')
 body=body.replace('<h2>Resources, source audio and limitations</h2>','<h2>Resources, source audio and limitations</h2><p><strong>Acoustic-revision checks:</strong> jobs 1401058, 1401073, 1401086 and 1401134 each use one L40S 48 GB, with Parakeet alone on GPU 0, sequentially. Their combined allocation is 147 seconds / 0.040833 GPU hours. The overall rerun has a maximum of four GPUs, enforced through job dependencies. <a href="../study-progress.html">Current S1 experiment results and resources</a>. The following cost records describe the preserved original speech-synthesis stage.</p>')
 return body
