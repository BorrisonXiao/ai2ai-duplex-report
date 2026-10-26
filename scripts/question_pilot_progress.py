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
 return '<section class="section" id="pilot-todo"><h2>Current pilot: task list and progress</h2><p>The next pilot keeps the current questions and adds more candidates, earlier question times and selected speaker-matched audio. This list is updated as stages finish.</p><ol class="pilot-todo">'+items+'</ol><p>Last update: '+e(r['updated_utc'])+'. <a href="question-pilot.html">Open the new pilot report</a> · <a href="../research/question-pilot/progress.json">Task-list data</a>.</p></section>'
