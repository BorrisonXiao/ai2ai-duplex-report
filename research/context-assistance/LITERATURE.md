# Literature Review — Context-aware assistance from multi-party speech

**Instruction**: Research models, papers, benchmarks and training data for a duplex assistant that uses overheard multi-party conversation to disambiguate a later user request; publish the findings as a literature-review sub-tab.

**Date**: 2026-10-04 · **Window**: 2023–2026, plus foundational meeting resources · **Depth**: standard

## Scope & sub-questions

Context-grounded assistance after listening to an authorized multi-party conversation; unsolicited intervention is a separate extension.

- Which systems already listen to and participate in multi-party speech?
- Which evaluations require speaker-specific context to interpret a later request?
- Which resources teach or test clarification rather than guessing?
- What code, checkpoints, audio, transcripts and supervision are actually released?
- What changes are needed for causal, synchronized duplex evaluation and appropriate disclosure?

## Landscape summary

The primary example is proactive listening plus context-grounded assistance when asked. Unsolicited intervention is a separate decision problem.

MSI-Bench and GroupMemBench already formulate speaker-scoped use of conversation history; broad claims that this task is new would be unsound.

MultiTalk supplies a close duplex backbone and synthetic group-speech recipe; MISeD supplies meeting-grounded assistant responses; ASK-QA supplies clarification behavior.

Correct answers, speaker attribution, appropriate silence and disclosure are separate outcomes. A good answer score does not establish an appropriate participation policy.

Offline transcript, participant-replacement and continuous room-audio protocols answer different questions. A public dataset card is not proof of a runnable model release.

## Paper table

| Paper / authors / date | Venue | Method | Reported result | Relevance / limitation | Status |
| --- | --- | --- | --- | --- | --- |
| [MSI-Bench: Evaluating Multi-Speaker Voice Interaction for Collaborative AI Agents](https://arxiv.org/abs/2609.24812) · Chenxu Xiong, Dongming Shen, Yuzhi Tang, Wentao Ma, Mu Li, Alex Smola · 2026-09-21 | arXiv preprint | Short multi-person audio scenes end in an assistant-directed request; atomic rubrics and tool-call checks score the response. | 1,152 cases, split evenly between English and Mandarin. English all-pass rate: Gemini 3.1 Pro 66.8%; Qwen3-Omni-30B 34.0% (Table 1). | Closest benchmark to overhearing a group and acting on a later handoff. Scripted TTS, mostly turn-based evaluation; separate restraint probes are not a continuous meeting simulation. | verified |
| [GroupMemBench: Benchmarking LLM Agent Memory in Multi-Party Conversations](https://arxiv.org/abs/2605.14498) · Jingbo Yang, Kwei-Herng Lai, Xiaowen Wang, Shiyu Chang, Yaar Harari, Evgeniy Gabrilovich · 2026-05-14 | arXiv preprint | Graph-generated enterprise conversations; queries include asker identity and six memory categories, including term ambiguity and abstention. | Hindsight: 46.01% overall / 37.74% term ambiguity; BM25: 43.22% / 14.15% (Table 2). | Closest formulation of speaker-conditioned disambiguation; useful text-only control. Synthetic text; no speech timing or interactive clarification. Queries are adversarially filtered against a retrieval solver. Paper and data card differ on corpus counts. | verified |
| [MultiTalk: Scaling Full-Duplex Speech Models to Long, Multi-Party, Bilingual Conversation](https://arxiv.org/abs/2609.36903) · Ke Wang, Houxing Ren, Zimu Lu, Yunqiao Yang, Zhuofan Zong, Mingjie Zhan, Hongsheng Li · 2026-09-29 | arXiv preprint; author comment: NeurIPS 2026, acceptance not established | Moshi-derived Moshi-MTB trained in two phases: bilingual dyadic pretraining, then multi-party fine-tuning; parallel audio and word-aligned text. | MultiTalkBench final score: Moshi-MTB 13.15, MiniCPM-o-4.5 11.05, human reference 68.74 (Table 2). | Most directly relevant trained full-duplex model and released multi-party speech training data. Benchmark replaces a human participant, rather than exclusively testing a later assistant request. Persona prompts are constructed offline from transcript excerpts; audit future-context leakage. | verified |
| [Data-Centric Improvements for Enhancing Multi-Modal Understanding in Spoken Conversation Modeling](https://aclanthology.org/2025.findings-acl.71/) · Maximillian Chen, Ruoxi Sun, Sercan Ö. Arık · 2025-07 | Findings of ACL 2025 | DAMSEL audio-model customization and ASK-QA: TTS-rendered Abg-CoQA with narrated knowledge, dialogue history and simulated clarification exchanges. | ASK-QA reports 221.8 speech hours; 5,985 / 500 / 1,345 train / validation / test conversations (§3.1). | Direct source for the answer-versus-clarify behavior missing from many turn-taking tests. Narrator/user/assistant voices are not a natural multi-party meeting. Dedicated ASK-QA audio, code and trained weights were not located. | verified |
| [Efficient Data Generation for Source-grounded Information-seeking Dialogs: A Use Case for Meeting Transcripts](https://aclanthology.org/2024.findings-emnlp.106/) · Lotem Golany, Filippo Galgani, Maya Mamo, Nimrod Parasol, Omer Vandsburger, Nadav Bar, Ido Dagan · 2024-11 | Findings of EMNLP 2024 | LLM-generated information-seeking dialogues over QMSum meetings, with human validation, correction and attribution spans. | 432 retained dialogues over 225 meetings; 4,161 validated QA pairs, split 2,922 / 611 / 628 (Tables 2, 14). | Closest reusable meeting-grounded assistant dialogue supervision, including follow-up questions. Text-only access to a completed meeting; no assistant-addressing or real-time clarification policy. | verified |
| [MP-Bench: Evaluating Voice Agents as a Multiparty Conversation Participant](https://arxiv.org/abs/2609.13076) · Yi-Jen Shih, Shih-Yun Shan Kuan, Guan-Ting Lin, Kai-Wei Chang, Siddhant Arora, Shu-wen Yang, Abdelrahman Mohamed, Shinji Watanabe, Hung-yi Lee, David Harwath · 2026-09-11 | arXiv preprint; authors report acceptance to Findings of EMNLP 2026 | Three simulated humans plus an agent in discussion and turn-based games; behavioral and comprehension tasks. | Twelve evaluated agents; turn-taking, response appropriateness and complementary multi-party comprehension are evaluated. | Useful speaker-attribution and reference-resolution diagnostic, distinct from Duplex-MPE. Clean synthetic speech without overlap; short scenarios. Repository URL returned 404. PDF abstract says 33% where landing-page abstract says 22%; neither is plotted. | verified |
| [Duplex-MPE: Benchmarking Multi-Party Interaction in Full-Duplex Dialogue](https://arxiv.org/abs/2609.31948) · Chengqian Ma, Wenhao Feng, Weixuan Jin, Gaole Dai, Tianyu Xie, Yuexiao Ma, Zhaolu Kang, Xiangyu Zhao, Xiawu Zheng, Fei Chao · 2026-09-25 | arXiv preprint | Continuous synthetic multi-person streams; paired explicit and implicit invitation cases test onset, silence and floor release. | 2,000 paired scenarios / 4,000 streams; already included in the broader duplex review. | Essential addressing and conversational-restraint guardrail for ambient listening. Does not by itself establish long-history intent disambiguation; dedicated evaluation audio/code release was not located. | verified |
| [Speak or Stay Silent: Context-Aware Turn-Taking in Multi-Party Dialogue](https://arxiv.org/abs/2603.11409) · Kratika Bhagtani, Mrinal Anand, Yu Chen Xu, Amit Kumar Singh Yadav · 2026-03-12 | arXiv preprint | Text LLM plus LoRA / reasoning-trace SFT predicts SPEAK or SILENT for a target participant at utterance boundaries. | More than 120K labeled decisions from AMI, Friends and SPGISpeech; authors report up to 23 percentage-point balanced-accuracy improvement. | Released training recipe for contextual participation, separate from answer generation. Human next-speaker behavior supplies labels, not optimal assistant usefulness. Labels must not be exposed as input; split by meeting to avoid shared-history leakage. | verified |
| [ELITR-Bench: A Meeting Assistant Benchmark for Long-Context Language Models](https://aclanthology.org/2025.coling-main.28/) · Thibaut Thonet, Laurent Besacier, Jos Rozen · 2025-01 | COLING 2025 | Manually authored meeting questions; standalone QA and follow-up conversation settings, with simulated ASR-noise variants. | 271 manually crafted QA pairs; evaluates long-context LLMs and examines agreement between model and human judges. | Useful meeting QA and noisy-transcript baseline; conversation version tests follow-up references. Transcript-only completed meetings; not a streaming speaker-addressing test. | verified |
| [Does Your Voice Assistant Remember? Analyzing Conversational Context Recall and Utilization in Voice Interaction Models](https://aclanthology.org/2025.findings-acl.470/) · Heeseung Kim, Che Hyun Lee, Sangkwon Park, Jiheum Yeom, Nohil Park, Sangwon Yu, Sungroh Yoon · 2025-07 | Findings of ACL 2025 | MultiDialog human dialogue histories with generated, speaker-adaptive TTS recall questions and supporting utterances; native recall and RAG analyses. | 2,612 QA pairs over 653 retained two-speaker dialogues (Table 1). | Isolates spoken-context retention before adding group-level ambiguity. Dyadic, test-only recall data; full histories require the underlying MultiDialog corpus. | verified |
| [QMSum: A New Benchmark for Query-based Multi-domain Meeting Summarization](https://aclanthology.org/2021.naacl-main.472/) · Ming Zhong, Da Yin, Tao Yu, Ahmad Zaidi, Mutethia Mutuma, Rahul Jha, Ahmed Hassan Awadallah, Asli Celikyilmaz, Yang Liu, Xipeng Qiu, Dragomir Radev · 2021-06 | NAACL 2021 | Query-based summaries with manually selected relevant transcript spans across product, academic and committee meetings. | 1,808 query-summary pairs from 232 meetings (Table 1). | Evidence-localization supervision and meeting-grounded pretraining; also the source of MISeD. Summaries are not clarification labels; transcripts may contain future evidence relative to a live request. Audio must be obtained from source corpora. | verified |
| [MuPPET: A Benchmark for Contextual Privacy of LLM Assistants in Multi-Party Conversations](https://arxiv.org/abs/2606.23217) · Elena Sofia Ruzzetti, Cornelius Emde, Sangdoo Yun, Seong Joon Oh, Martin Gubri · 2026-06-22 | arXiv preprint | Workplace group chats, target-user memories and final assistant requests; score sensitive-information leakage alongside useful content. | 562 synthetic multi-party workplace conversations; released seeds, memories, conversations and evaluation scripts. | Privacy control for deciding what overheard context can be disclosed, not merely retrieved. Text-only synthetic interactions, not consent-aware ambient speech capture. | verified |
| [SocialMind: LLM-based Proactive AR Social Assistive System with Human-like Perception for In-situ Live Interactions](https://arxiv.org/abs/2412.04036) · Bufang Yang, Yunqi Guo, Lilin Xu, Zhenyu Yan, Hongkai Chen, Guoliang Xing, Xiaofan Jiang · 2024-12-05 | arXiv preprint | Multimodal sensing of speech and social cues, persona-aware LLM suggestions and proactive visual updates on AR glasses. | Evaluation on three public datasets and a 20-participant user study. | Existing ambient, proactive social-assistance system: broad proactive-help claims are not new. Visual coaching, not native speech-to-speech duplex or later-request disambiguation. Dedicated system release was not located. | verified |
| [ProMediate: A Simulation Testbed for Evaluating Proactive Mediation in Multi-Party Negotiation](https://aclanthology.org/2026.findings-acl.1479/) · Ziyi Liu, Bahareh Sarrafzadeh, Pei Zhou, Longqi Yang, Jieyu Zhao, Ashish Sharma · 2026-07 | Findings of ACL 2026 | Simulated multi-party negotiation with plug-in mediators; consensus and socio-cognitive intervention evaluation. | Social mediator improves consensus change over a generic mediator in the authors’ hard setting. | Useful only if scope expands to unsolicited assistance or meeting facilitation. LLM simulation and text interventions; not evidence of live speech synchronization. | verified |
| [Proactive Hearing Assistants that Isolate Egocentric Conversations](https://aclanthology.org/2025.emnlp-main.1289/) · Guilin Hu, Malek Itani, Tuochao Chen, Shyamnath Gollakota · 2025-11 | EMNLP 2025 | Self-speech beamforming anchors a slow conversation-embedding model and a fast streaming source-extraction model. | Real-world binaural test recordings: 11 participants, 6.8 hours (§4). | Front-end resource for distinguishing a user’s conversation from an unrelated bystander group. Acoustic conversation isolation, not language-level instruction interpretation or assistant answer generation. | verified |

## Training resources

| Resource | Scale | Supervision | Access | Use / limitation |
| --- | --- | --- | --- | --- |
| MultiTalkFT | 3.2k h reported multi-party fine-tuning speech. | Synthetic English/Chinese parallel streams; speaker-channel map, word timestamps, persona and voice prompts. | Public data / manifests; CC BY-NC 4.0. | Most directly relevant duplex training source; not curated ambiguity/clarification supervision. [Source](https://huggingface.co/datasets/MultiTalk/MultiTalkFT) |
| MultiTalkPT | 54.4k h reported bilingual dyadic pretraining speech. | Word-aligned synthetic speech; explicit paired streams. | Public manifests and audio files; CC BY-NC 4.0. HF preview is only 100 rows, not the full corpus. | Speech-backbone adaptation; do not call all 57.6k combined hours multi-party. [Source](https://huggingface.co/datasets/MultiTalk/MultiTalkPT) |
| MISeD | 4,161 validated QA turns: 2,922 train / 611 validation / 628 test. | Meeting transcript + assistant history + question + response + human attribution spans. | Public text dataset; explicit dataset reuse licence not verified in repository. | Meeting-grounded answers and follow-ups; align to original speech and enforce prefix-only context. [Source](https://github.com/google-research-datasets/MISeD) |
| AMI + ICSI meeting corpora | AMI: about 100 h; ICSI: 75 natural meetings. | Real multi-microphone speech, participant-linked transcripts and timing; AMI has scenario roles and selected dialogue/addressee annotations. | Official media/annotation downloads, CC BY 4.0. Annotation coverage differs by recording. | Natural meeting input and oracle speaker controls; needs new assistant requests, intended referents and clarification labels. [Source](https://groups.inf.ed.ac.uk/ami/) |
| QMSum | 1,808 query-summary pairs / 232 meetings. | Speaker-tagged transcripts, query-focused summaries and relevant text spans. | Public text annotations; MIT repository licence; respect original corpus terms. | Grounded evidence selection; related to MISeD, so split by underlying meeting across both. [Source](https://github.com/Yale-LILY/QMSum) |
| Context-aware turn-taking data | >120K labeled decisions before source-specific processing/subsampling. | AMI / Friends / SPGI transcript prefixes, target speaker, speak/silent labels and optional teacher reasoning. | Public train/validation/test files; dataset card Apache-2.0. Original recording/transcript rights still require source-specific checks. | Participation supervision only; remove future-label fields from input and use meeting-disjoint splits. [Source](https://huggingface.co/datasets/ishiki-labs/multi-party-dialogue) |
| Abg-CoQA → ASK-QA recipe | Public text ambiguity/clarification source; ASK-QA speech hours are paper-reported. | Ambiguous questions, answers and clarifying exchanges; ASK-QA adds TTS and narrated knowledge. | Abg-CoQA MIT repository; dedicated ASK-QA audio / customization weights not located. | Start with text clarification supervision; do not describe paper-reported ASK-QA as a downloadable training corpus. [Source](https://github.com/MeiqiGuo/AKBC2021-Abg-CoQA) |
| GroupMemBench generation recipe | Four synthetic enterprise domains; use the actual manifests to count. | Asker roles, threaded messages, decision updates and speaker-dependent terminology. | Conversation data public; explicit code/data licence not verified. | Regenerate disjoint training scenarios, rather than train on the released benchmark questions. [Source](https://github.com/UCSB-NLP-Chang/GroupMemBench) |

## Reported results

### MSI-Bench · English

All-pass rate (%) ↑; Table 1, PDF page 6; [Primary paper](https://arxiv.org/abs/2609.24812).

| Model / pipeline | All-pass rate (%) ↑ |
| --- | --- |
| Gemini 3.1 Pro (thinking) | 66.8 |
| GPT Realtime 2.1 (xhigh) | 58.3 |
| Qwen3-Omni-30B | 34.0 |
| Gemma 4-12B (no thinking) | 22.6 |

576 English cases; all rubrics must pass. These are different model configurations under one benchmark, not a continuous duplex success rate. Values are rounded as in the paper; its 95% Wilson intervals are omitted here.

### GroupMemBench · term ambiguity

Accuracy (%) ↑; Table 2, PDF page 7; [Primary paper](https://arxiv.org/abs/2605.14498).

| Model / pipeline | Accuracy (%) ↑ |
| --- | --- |
| Hindsight | 37.74 |
| HippoRAG | 30.19 |
| A-Mem | 26.42 |
| BM25 | 14.15 |

Text-only memory pipelines, not speech models. Same question interpretation depends on speaker-specific terminology. Backend and retrieval budgets follow the paper; these are not new experiments.

### MultiTalkBench · overall

Final score (0–100) ↑; Table 2, PDF page 8; [Primary paper](https://arxiv.org/abs/2609.36903).

| Model / pipeline | Final score (0–100) ↑ |
| --- | --- |
| Human reference | 68.74 |
| Moshi-MTB | 13.15 |
| MiniCPM-o-4.5 | 11.05 |
| Qwen3-Omni-30B | 4.94 |
| Moshiko-7B | 4.66 |
| PersonaPlex-7B | 2.52 |

Composite judge/participation score, not percent correct. Human reference uses original recordings. No closed-system result is reported in this comparison. Never compare its scale with MSI-Bench accuracy.

## Themes & consensus

- The primary example is proactive listening plus context-grounded assistance when asked. Unsolicited intervention is a separate decision problem.
- MSI-Bench and GroupMemBench already formulate speaker-scoped use of conversation history; broad claims that this task is new would be unsound.
- MultiTalk supplies a close duplex backbone and synthetic group-speech recipe; MISeD supplies meeting-grounded assistant responses; ASK-QA supplies clarification behavior.
- Correct answers, speaker attribution, appropriate silence and disclosure are separate outcomes. A good answer score does not establish an appropriate participation policy.
- Offline transcript, participant-replacement and continuous room-audio protocols answer different questions. A public dataset card is not proof of a runnable model release.

## Open gaps & opportunities

### Causal context-dependent requests with interactive clarification

MSI-Bench tests a later handoff; GroupMemBench tests speaker-conditioned ambiguity; ASK-QA tests clarification. The reviewed artifacts do not establish a shared, natural-meeting, prefix-only duplex protocol combining all three. [msi](https://arxiv.org/abs/2609.24812), [groupmem](https://arxiv.org/abs/2605.14498), [ask](https://aclanthology.org/2025.findings-acl.71/), [mised](https://aclanthology.org/2024.findings-emnlp.106/).

### Synchronize memory updates, clarification and spoken commitments

MultiTalk and Duplex-MPE address group participation and timing, but their reported scores do not isolate whether a late correction updates the intended referent before a spoken commitment. [multitalk](https://arxiv.org/abs/2609.36903), [mpe](https://arxiv.org/abs/2609.31948), [speak](https://arxiv.org/abs/2603.11409).

### Separate perception errors from interpretation errors

MSI-Bench explicitly compares speech and clean-transcript behavior; ContextDialog isolates speech-memory recall. Speaker-labeled transcript and oracle-diarization controls would distinguish front-end loss from reasoning failures. [msi](https://arxiv.org/abs/2609.24812), [contextdialog](https://aclanthology.org/2025.findings-acl.470/), [hearing](https://aclanthology.org/2025.emnlp-main.1289/).

### Retain useful context without revealing it to the wrong audience

MuPPET provides a group-disclosure test; MSI-Bench includes selective disclosure. The reviewed work does not by itself establish consent-aware ambient capture or speaker-specific retention controls. [muppet](https://arxiv.org/abs/2606.23217), [msi](https://arxiv.org/abs/2609.24812).

These are synthesis-based candidate gaps, not exhaustive novelty claims. No experiments or new annotations were created.

## References

- Chenxu Xiong, Dongming Shen, Yuzhi Tang, Wentao Ma, Mu Li, Alex Smola. MSI-Bench: Evaluating Multi-Speaker Voice Interaction for Collaborative AI Agents. arXiv preprint; 2609.24812v1. [Primary source](https://arxiv.org/abs/2609.24812).
- Jingbo Yang, Kwei-Herng Lai, Xiaowen Wang, Shiyu Chang, Yaar Harari, Evgeniy Gabrilovich. GroupMemBench: Benchmarking LLM Agent Memory in Multi-Party Conversations. arXiv preprint; 2605.14498v2. [Primary source](https://arxiv.org/abs/2605.14498).
- Ke Wang, Houxing Ren, Zimu Lu, Yunqiao Yang, Zhuofan Zong, Mingjie Zhan, Hongsheng Li. MultiTalk: Scaling Full-Duplex Speech Models to Long, Multi-Party, Bilingual Conversation. arXiv preprint; author comment: NeurIPS 2026, acceptance not established; 2609.36903v1. [Primary source](https://arxiv.org/abs/2609.36903).
- Maximillian Chen, Ruoxi Sun, Sercan Ö. Arık. Data-Centric Improvements for Enhancing Multi-Modal Understanding in Spoken Conversation Modeling. Findings of ACL 2025; 2025.findings-acl.71. [Primary source](https://aclanthology.org/2025.findings-acl.71/).
- Lotem Golany, Filippo Galgani, Maya Mamo, Nimrod Parasol, Omer Vandsburger, Nadav Bar, Ido Dagan. Efficient Data Generation for Source-grounded Information-seeking Dialogs: A Use Case for Meeting Transcripts. Findings of EMNLP 2024; 2024.findings-emnlp.106. [Primary source](https://aclanthology.org/2024.findings-emnlp.106/).
- Yi-Jen Shih, Shih-Yun Shan Kuan, Guan-Ting Lin, Kai-Wei Chang, Siddhant Arora, Shu-wen Yang, Abdelrahman Mohamed, Shinji Watanabe, Hung-yi Lee, David Harwath. MP-Bench: Evaluating Voice Agents as a Multiparty Conversation Participant. arXiv preprint; authors report acceptance to Findings of EMNLP 2026; 2609.13076v1. [Primary source](https://arxiv.org/abs/2609.13076).
- Chengqian Ma, Wenhao Feng, Weixuan Jin, Gaole Dai, Tianyu Xie, Yuexiao Ma, Zhaolu Kang, Xiangyu Zhao, Xiawu Zheng, Fei Chao. Duplex-MPE: Benchmarking Multi-Party Interaction in Full-Duplex Dialogue. arXiv preprint; 2609.31948v1. [Primary source](https://arxiv.org/abs/2609.31948).
- Kratika Bhagtani, Mrinal Anand, Yu Chen Xu, Amit Kumar Singh Yadav. Speak or Stay Silent: Context-Aware Turn-Taking in Multi-Party Dialogue. arXiv preprint; 2603.11409v1. [Primary source](https://arxiv.org/abs/2603.11409).
- Thibaut Thonet, Laurent Besacier, Jos Rozen. ELITR-Bench: A Meeting Assistant Benchmark for Long-Context Language Models. COLING 2025; 2025.coling-main.28. [Primary source](https://aclanthology.org/2025.coling-main.28/).
- Heeseung Kim, Che Hyun Lee, Sangkwon Park, Jiheum Yeom, Nohil Park, Sangwon Yu, Sungroh Yoon. Does Your Voice Assistant Remember? Analyzing Conversational Context Recall and Utilization in Voice Interaction Models. Findings of ACL 2025; 2025.findings-acl.470. [Primary source](https://aclanthology.org/2025.findings-acl.470/).
- Ming Zhong, Da Yin, Tao Yu, Ahmad Zaidi, Mutethia Mutuma, Rahul Jha, Ahmed Hassan Awadallah, Asli Celikyilmaz, Yang Liu, Xipeng Qiu, Dragomir Radev. QMSum: A New Benchmark for Query-based Multi-domain Meeting Summarization. NAACL 2021; 2021.naacl-main.472. [Primary source](https://aclanthology.org/2021.naacl-main.472/).
- Elena Sofia Ruzzetti, Cornelius Emde, Sangdoo Yun, Seong Joon Oh, Martin Gubri. MuPPET: A Benchmark for Contextual Privacy of LLM Assistants in Multi-Party Conversations. arXiv preprint; 2606.23217v1. [Primary source](https://arxiv.org/abs/2606.23217).
- Bufang Yang, Yunqi Guo, Lilin Xu, Zhenyu Yan, Hongkai Chen, Guoliang Xing, Xiaofan Jiang. SocialMind: LLM-based Proactive AR Social Assistive System with Human-like Perception for In-situ Live Interactions. arXiv preprint; 2412.04036v1. [Primary source](https://arxiv.org/abs/2412.04036).
- Ziyi Liu, Bahareh Sarrafzadeh, Pei Zhou, Longqi Yang, Jieyu Zhao, Ashish Sharma. ProMediate: A Simulation Testbed for Evaluating Proactive Mediation in Multi-Party Negotiation. Findings of ACL 2026; 2026.findings-acl.1479. [Primary source](https://aclanthology.org/2026.findings-acl.1479/).
- Guilin Hu, Malek Itani, Tuochao Chen, Shyamnath Gollakota. Proactive Hearing Assistants that Isolate Egocentric Conversations. EMNLP 2025; 2025.emnlp-main.1289. [Primary source](https://aclanthology.org/2025.emnlp-main.1289/).

## Evidence caveats

MP-Bench: PDF and landing-page abstracts disagree (33% vs. 22%); excluded from plots. GroupMemBench: paper and card corpus counts differ. MultiTalk: public data does not verify its claimed engine/scorer/checkpoint release. Dataset reuse licences are separated from code licences. Full primary manuscripts were read; all bibliography entries have independently checked metadata.
