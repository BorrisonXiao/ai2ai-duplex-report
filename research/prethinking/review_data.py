"""Proposal discussion as of 10 October 2026; no new inference results."""
DATE = '2026-10-10'
INSTRUCTION = 'Review a tentative dual-brain duplex system for long multi-speaker conversations: interaction-controlled <pre_think> before a request, transition to <think>, partial-result sharing, and causal training-data construction including MultiTalkFT. A powerful text-only teacher generates private CoT from causally aligned transcripts to supervise an audio-conditioned thinking student p(z | x, c), with teacher p(z | x_text, c). Discuss overlooked details, using readable explanations and mathematical probability notation, in an HTML report sub-tab.'
SCOPE = 'Background preparation before an assistant-directed request, followed by interruptible request reasoning in a continuous multi-speaker conversation.'
QUESTIONS = [
    'What can be prepared usefully before the actual request is known?',
    'When should the interaction layer start, update, stop or resume background work?',
    'What happens when a request or correction arrives during unfinished reasoning?',
    'Which information should be private to S2 and which should reach S1?',
    'How can existing dialogue data become causal scheduling and revision supervision?',
    'How can causal transcript-conditioned teacher reasoning supervise the audio-conditioned student without future or speaker-information leakage?',
    'How can evaluation separate background reasoning gains from memory, extra compute and easier input?'
]

def paper(ident, problem, method, results, relevance, limitations, venue='arXiv preprint'):
    return dict(id=ident, problem=problem, method=method, results=results, relevance=relevance, limitations=limitations, venue=venue)

PAPERS = [
    paper('proactive', 'Reactive reasoning adds delay after each reply.', 'Precompute likely next-turn reasoning; interrupt on arrival, then reuse or extend suitable work.', 'Training-free evaluation in three time-aware dialogue environments.', 'Closest precedent for the central idea.', 'Predicting a next reply differs from maintaining a long, changing group conversation.'),
    paper('lts', 'Sequential voice processing delays reasoning.', 'Semantic prefix triggers, background state updates and concurrent response generation.', 'Streaming QA and Pause-and-Repair evaluation.', 'Close precedent for trigger selection and structured notes.', 'Does not establish long multi-party preparation or speaker-scoped memory.'),
    paper('asyncio', 'New input can invalidate ongoing reasoning and tools.', 'Interruptible event input, editable tool calls and clock-based training.', 'Reported speedups on asynchronous agent tasks.', 'Useful training and cancellation design.', 'Tool-centric evaluation is not continuous multi-speaker speech.'),
    paper('duplex', 'Deep reasoning must coexist with immediate interaction.', 'Asynchronous interaction/thinking layers and Writer-Director data construction.', 'Streaming results support real-time interaction in the reported system.', 'Our existing backbone and control-data recipe.', 'Its request-driven interface does not establish this preparation policy.'),
    paper('talker', 'Conversation and planning have different timing needs.', 'A fast Talker uses state updated by a slower Reasoner.', 'Architecture discussion grounded in sleep coaching.', 'Precedent for sharing state rather than every reasoning token.', 'Not a long multi-speaker duplex evaluation.'),
    paper('convfill', 'Reasoner delay makes voice responses slow.', 'Train a small talker to incorporate streamed reasoner information.', 'Released synthetic conversational-infill training recipe.', 'Supports explicit supervision for using late information.', 'Immediate speech and infill do not establish silent pre-request reasoning.'),
    paper('multitalk', 'Full-duplex models struggle with long group conversations.', 'Synthetic dialogue scripts, parallel speech and aligned text; staged Moshi-style training.', '54.4k-hour MultiTalkPT and 3.2k-hour MultiTalkFT reported.', 'Closest speech-data ingredient for this proposal.', 'Does not supply our pre-thinking scheduling or reuse labels.'),
    paper('groupmem', 'Question interpretation depends on the asker.', 'Speaker-conditioned queries over synthetic group history.', 'Tests updates, ambiguity and abstention.', 'Motivates speaker-specific memory and controls.', 'Text-only benchmark; not an interactive speech training set.'),
    paper('msi', 'Voice agents must attribute context and requests correctly.', 'Group audio followed by assistant-directed tasks.', '1,152 bilingual evaluation cases.', 'Useful held-out speaker/context evaluation.', 'Mostly short scripted speech; does not test our live scheduling.'),
    paper('ask', 'A spoken question may have several meanings.', 'ASK-QA renders ambiguity/clarification dialogues from Abg-CoQA.', 'Reported spoken clarification evaluation and model customization.', 'Ingredient for answer-versus-clarify supervision.', 'Dedicated ASK-QA release not verified; underlying text repository is reachable.', 'Findings of ACL 2025'),
    paper('mised', 'Meeting-grounded answers need attributable evidence.', 'Generated dialogues with human verification and evidence spans.', 'Released Meeting Information Seeking Dialogs (MISeD).', 'Meeting QA and grounded-note supervision.', 'Completed-meeting context needs causal prefix filtering.', 'Findings of EMNLP 2024'),
    paper('qmsum', 'Meeting queries need relevant evidence selected.', 'Query-focused summaries with relevant transcript spans.', '1,808 query-summary pairs over 232 meetings.', 'Evidence selection and original meeting links.', 'Summary targets may require speech not yet heard.', 'NAACL 2021'),
    paper('speak', 'Participation depends on conversational context.', 'Context-based SPEAK/SILENT prediction with supervised adaptation.', 'Released multi-party decision data and recipe.', 'Useful inspiration for separate addressing decisions.', 'The next human speaker is not an optimal assistant or pre-thinking label.'),
    paper('muppet', 'Useful group history may be inappropriate to disclose.', 'Evaluate assistance together with contextual privacy.', '562 synthetic workplace conversations.', 'Audience-sensitive use of background notes.', 'Text-only; does not establish audio consent or live disclosure control.'),
    paper('longmem', 'Long histories require updates and selective recall.', 'Evaluate extraction, temporal reasoning, updates and abstention.', '500 curated long-memory questions.', 'Memory-only baseline and knowledge-update tests.', 'Dyadic text histories; background reasoning remains a separate question.', 'ICLR 2025'),
    paper('audio-kd', 'Audio models lag text models on reasoning.', 'Transfer from a text teacher with source- and layer-wise distillation.', 'Audio reasoning framework and evaluation.', 'Direct precedent for text-to-audio reasoning transfer.', 'Does not establish causal group prefixes or request-time preemption.'),
    paper('audio-opd', 'Teacher-written traces can diverge from student acoustic perception.', 'Audio-conditioned student rollouts receive matched-text teacher guidance.', 'Reasoning benchmarks and preservation analyses.', 'Close precedent for the proposed conditional distributions and a later on-policy stage.', 'Uses matched text and verified answers; our pre-request teacher must not see the future request or answer.'),
    paper('step-r1', 'Reasoning must remain grounded in acoustic evidence.', 'Modality-grounded reasoning distillation for audio tasks.', 'Speech, sound and music reasoning evaluation.', 'Motivates separate supervision for cues absent from transcripts.', 'Clip-level reasoning is not our long multi-speaker preparation policy.'),
]

THEMES = [
    'Reasoning before the next input and interruptible asynchronous processing already have close precedents.',
    'Structured state, conversation memory and request reasoning solve different problems and need separate controls.',
    'An unfinished private reasoning trace is not automatically a grounded result or a resumable provider state.',
    'Existing speech corpora supply conversations and timing, but not the proposed scheduling, validity and sharing labels.',
    'Text-to-audio reasoning distillation has direct precedents; causal prefixes, partial-trace revision and group attribution remain the proposed extension.'
]
GAPS = [
    dict(id='g1', statement='Whether selected background analysis improves later group-context answers beyond memory maintenance at matched compute.', refs=['proactive','lts','groupmem','longmem'], evidence='These works cover anticipation, streaming state or memory individually; their inspected evaluations do not establish this combination.'),
    dict(id='g2', statement='How to preempt, revise and reuse background notes under new multi-speaker evidence without stale speech.', refs=['asyncio','duplex','multitalk'], evidence='Interruptible tools, S1/S2 handoff and group speech are established separately; the proposal needs a joint causal evaluation.'),
    dict(id='g3', statement='Which small, grounded updates should reach S1 before a request, and whether training enables useful silence and clarification.', refs=['talker','convfill','ask','speak','muppet'], evidence='State sharing, late-result uptake, clarification, participation and privacy provide ingredients, rather than a verified unified policy.')
]
