"""Shared report task list; labels name the work and its current evidence."""
from html import escape as e
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def progress_panel():
 p=ROOT/'research/question-pilot/progress.json'
 if not p.exists():return ''
 r=json.loads(p.read_text());labels={'pending':'To do','in_progress':'In progress','complete':'Done'}
 items=''.join('<li><strong>'+e(labels[t['status']])+' · '+e(t['label'])+'</strong>'+('<p>'+e(t['note'])+'</p>' if t['note'] else '')+'</li>' for t in r['tasks'])
 done=sum(t['status']=='complete' for t in r['tasks']);finished=done==len(r['tasks'])
 intro='All pilot stages are complete. The audio clips are ready for your listening review.' if finished else 'This pilot adds questions, early checkpoints and requester-matched audio while preserving the earlier set. Status follows the completed evidence.'
 return '<section class="section" id="pilot-todo"><h2>Pilot task list</h2><p>'+intro+'</p><details'+('' if finished else ' open')+'><summary>'+str(done)+' of '+str(len(r['tasks']))+' stages complete · view steps</summary><ol class="pilot-todo">'+items+'</ol></details><p>Last update: '+e(r['updated_utc'])+'. <a href="question-pilot.html">Open the pilot report</a> · <a href="../research/question-pilot/progress.json">Task-list data</a>.</p></section>'
