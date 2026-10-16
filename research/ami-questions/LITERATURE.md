# Literature review: timed, speaker-aware meeting questions

Date: 2026-10-16. Depth: focused quick review, twelve papers plus one source-inspected tool. Window: recent work plus foundational references.

## Scope
Research scripted pipelines for synthesizing natural, role-based, history-dependent questions and reference answers from speaker-diarized, time-aligned AMI transcripts, then compare local text LLMs with assistant-authored questions.

## Landscape
Meeting-specific precedents provide either annotated questions from real participants or queries over an already recorded meeting. They are useful sources of natural phrasing and evidence conventions. For an injected request, the available prefix must be fixed before generating the question and proposed answer; full-meeting summaries or metadata that resolve later decisions must not leak into that input. This is our design inference, not a claim that scripted question generation is new.

PREME is the closest inspected meeting-question pipeline: segment the transcript, sample multiple questions, organize them by topic and evaluate answerability/coverage. Roundtrip consistency adds a separate answer-recovery step. Meta’s toolkit supplies a practical batch-generation/curation pattern. We implement a small local version with explicit source times rather than importing a large framework.

Memory benchmarks motivate temporal revisions, speaker ownership and missing-information controls. Fluent questions with old citations can still be answerable from the last turn. The pilot therefore compares full-prefix reading with recent-only, question-only and evidence-removal conditions and reviews actual answers.

## Verified papers
### p1: QMSum: A New Benchmark for Query-based Multi-domain Meeting Summarization
Ming Zhong et al. (2021); NAACL. [Primary source](https://aclanthology.org/2021.naacl-main.472/). Verification: verified — ACL Anthology primary abstract and metadata.

Problem: One meeting summary cannot address all user information needs. Method: Human query-summary annotation with relevant transcript spans; locate evidence and then summarize. Result/resource: 1,808 query-summary pairs over 232 meetings. Relevance and limits: Use explicit evidence spans and focused answers; full-meeting queries cannot automatically become causal in-meeting requests.

### p2: MeetingQA: Extractive Question-Answering on Meeting Transcripts
Archiki Prasad et al. (2023); ACL. [Primary source](https://aclanthology.org/2023.acl-long.837/). Verification: verified — ACL Anthology primary abstract and paper.

Problem: Meeting questions and their responses are understudied relative to summarization. Method: Annotate naturally occurring participant questions and corresponding extractive answers. Result/resource: Introduces an extractive meeting QA resource; no numerical baseline reused here. Relevance and limits: Useful examples of actual spoken wording; answers that occur after the original question cannot be treated as already available to an injected assistant.

### p3: MeeQA: Natural Questions in Meeting Transcripts
Reut Apel et al. (2023); venue not specified here. [Primary source](https://arxiv.org/abs/2305.08502). Verification: verified — Primary arXiv abstract; venue left unspecified.

Problem: Real meeting questions can be unclear, context-dependent or unanswered. Method: Extract participant QA and explicitly model questions with no transcript answer using a flat hierarchical loss. Result/resource: 48K QA pairs extracted from 422 meeting transcripts, according to the abstract. Relevance and limits: Include abstention and ambiguity controls; do not assume every plausible question has a uniquely determined answer.

### p4: PREME: Preference-based Meeting Exploration through an Interactive Questionnaire
Negar Arabzadeh et al. (2023); Findings of EACL. [Primary source](https://aclanthology.org/2023.findings-eacl.25/). Verification: verified — Primary ACL paper sections 3.1–3.3 and official repository.

Problem: A user unfamiliar with a meeting may not know which useful questions to ask. Method: Segment meeting topics, generate GPT-3 questions across temperatures and repeated trials, extract subjects/aspects and normalize the questionnaire; evaluate answerability and coverage. Result/resource: Releases 1,000 questions annotated with subjects and aspects. Generation uses temperature 0–1 in .05 steps and ten trials per temperature. Relevance and limits: Direct precedent for a scriptable meeting-question pipeline. Our prefix cutoff and current requester task are additional constraints; PREME explores recorded meetings.

### p5: Synthetic QA Corpora Generation with Roundtrip Consistency
Chris Alberti, Daniel Andor, Emily Pitler, Jacob Devlin, Michael Collins (2019); ACL. [Primary source](https://aclanthology.org/P19-1620/). Verification: verified — Primary arXiv abstract and ACL record.

Problem: Synthetic questions and proposed answers can disagree. Method: Generate questions and independently extract answers; retain consistent pairs. Result/resource: The paper reports downstream SQuAD2/NQ gains; we reuse the validation idea, not its training results. Relevance and limits: Hide the proposed answer from the reader and compare the recovered facts. A model declaring its own answerable flag is insufficient validation.

### p6: Evaluating Very Long-Term Conversational Memory of LLM Agents
Adyasha Maharana et al. (2024); venue not specified here. [Primary source](https://arxiv.org/abs/2402.17753). Verification: verified — Primary arXiv abstract; venue not inferred.

Problem: Short dialogue evaluation misses long-range temporal and causal memory failures. Method: Generate persona/event-grounded conversations, then have human annotators verify and edit long-range consistency; evaluate QA, event summaries and multimodal generation. Result/resource: LoCoMo conversations average 300 turns and 9K tokens, over up to 35 sessions. Relevance and limits: Balance temporal revision, attribution and multi-evidence questions and review grounding. This pilot uses real conversation rather than generated conversation.

### p7: LongMemEval: Benchmarking Chat Assistants on Long-Term Interactive Memory
Di Wu et al. (2025); ICLR. [Primary source](https://arxiv.org/abs/2410.10813). Verification: verified — Primary revised arXiv abstract explicitly identifies ICLR 2025.

Problem: Memory must track time, updates and missing information across sustained interactions. Method: Curate questions covering extraction, multi-session reasoning, temporal reasoning, knowledge updates and abstention within scalable chat histories. Result/resource: 500 curated questions; abstract reports substantial memory degradation in long histories. Relevance and limits: Use a question taxonomy and explicit stale-answer/abstention controls, rather than counting fluent answers as correct.

### p8: Self-Instruct: Aligning Language Models with Self-Generated Instructions
Yizhong Wang et al. (2023); ACL. [Primary source](https://aclanthology.org/2023.acl-long.754/). Verification: verified — Primary ACL Anthology record and arXiv abstract.

Problem: Instruction datasets can be limited and repetitive. Method: Generate instructions and input/output instances, then filter invalid and overly similar examples. Result/resource: Demonstrates instruction-tuning improvements; not evidence that generated meeting questions are valid. Relevance and limits: Separate generation from filtering and preserve rejected examples. Do not scale a seed set before checking diversity and factual support.

### p9: Grounding Spoken LLMs in Multi-Speaker Audio via Diarization Conditioning
Alexander Polok et al. (2026); Interspeech (as cited by the authors' dataset card). [Primary source](https://arxiv.org/abs/2606.18134). Verification: verified — Primary arXiv record and dataset-author card; generation details attributed specifically to the card.

Problem: Spoken LLMs need target-speaker grounding in multiparty audio. Method: Condition the acoustic encoder on diarization masks. The associated NSF-QA card describes Gemini-generated QA from speaker-conditioned ground-truth transcripts. Result/resource: The dataset card warns that its automatically generated references are not guaranteed correct; no performance values reused here. Relevance and limits: Close precedent for layering synthetic speaker-aware QA over real meeting data, but not proof of causal, timed, participant-motivated questions. We do not reuse its generated labels.

## Inspected tooling
[Meta Synthetic Data Kit](https://github.com/meta-llama/synthetic-data-kit): Chunk documents, generate QA in batches, then rate and filter candidates. Our adaptation: Reuse the staged pattern in a small local script. Do not feed a future-informed full-meeting summary into a prefix-conditioned generator. [Inspected implementation](https://raw.githubusercontent.com/meta-llama/synthetic-data-kit/main/synthetic_data_kit/generators/qa_generator.py).

## Themes and limits
- Meeting QA provides realistic wording and evidence conventions, but usually assumes access to a recorded meeting.
- Generation followed by answering/filtering is a well-established pattern; it does not by itself establish temporal causality or necessity of old history.
- Temporal updates, speaker attribution and abstention should be evaluated separately.

## Open design questions
- A synthetic request asked during a real meeting needs an explicit prefix cutoff, requester and injection policy. p1/p4 target recorded-meeting exploration; p2/p3 use original participant QA. This is our task-design inference, not a novelty claim.
- An old citation is not proof that earlier history is necessary. p5 motivates answer reconstruction; p7 motivates knowledge-update controls. Add recent-only and question-only readers plus semantic review.
- Text references and spoken evaluation artifacts need separate provenance. p9 illustrates speaker-grounded synthetic QA; planned audio must preserve roles, source times and explicit synthetic status.

## Additional close precedents verified during the pilot

### p10: Efficient Data Generation for Source-grounded Information-seeking Dialogs: A Use Case for Meeting Transcripts
Lotem Golany et al. (2024); Findings of EMNLP. [Primary source](https://aclanthology.org/2024.findings-emnlp.106/). Verification: verified.

Problem: Generating grounded dialogue and reliable attribution over long noisy meeting transcripts is difficult. Method: Generate queries and responses with LLMs, then ask humans to verify them and identify source attribution spans. Resource: Introduces MISeD; the author repository describes 432 dialogues over QMSum transcripts. Relevance and limits: Closest precedent for supervised generation over existing meeting transcripts. Our assistant-only review does not replace its human attribution validation, and our queries must obey an in-meeting cutoff.

### p11: GroupMemBench: Benchmarking LLM Agent Memory in Multi-Party Conversations
Jingbo Yang et al. (2026); arXiv preprint. [Primary source](https://arxiv.org/abs/2605.14498). Verification: verified.

Problem: Group memory needs requester identity, speaker-grounded beliefs and audience-dependent language. Method: Graph-grounded conversation synthesis and adversarial query generation bind questions to an asking user across six memory categories. Resource: Repository questions explicitly pair question/answer with asking_user_id; source messages include role, timestamp and reply structure. Relevance and limits: Direct precedent for role-aware questions and temporal updates. It generates enterprise text chats rather than injecting requests into real AMI speech. Do not claim role-conditioned memory QA is new.

### p12: Data-Centric Improvements for Enhancing Multi-Modal Understanding in Spoken Conversation Modeling
Maximillian Chen, Ruoxi Sun, Sercan Ö. Arık (2025); Findings of ACL. [Primary source](https://aclanthology.org/2025.findings-acl.71/). Verification: verified.

Problem: Spoken conversation QA must handle ambiguous requests and speech-specific variability. Method: DAMSEL auxiliary tasks and ASK-QA; turn text conversations into speech with separate narrator, user and assistant voices. Resource: ASK-QA includes ambiguous multi-turn spoken QA and dynamic inputs; no performance value reused here. Relevance and limits: Useful precedent for text-first data construction and separate voice assignments. Narrated knowledge plus synthetic user/assistant speech is not natural multi-party streaming.

