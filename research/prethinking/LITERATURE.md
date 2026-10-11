# Literature Review — Pre-thinking for long multi-speaker duplex conversation
**Instruction**: Review a tentative dual-brain duplex system for long multi-speaker conversations: interaction-controlled <pre_think> before a request, transition to <think>, partial-result sharing, and causal training-data construction including MultiTalkFT. A powerful text-only teacher generates private CoT from causally aligned transcripts to supervise an audio-conditioned thinking student p(z | x, c), with teacher p(z | x_text, c). Discuss overlooked details, using readable explanations and mathematical probability notation, in an HTML report sub-tab.
**Date**: 2026-10-10 · **Window**: 2021–2026 · **Depth**: standard

## Scope and sub-questions
Background preparation before an assistant-directed request, followed by interruptible request reasoning in a continuous multi-speaker conversation.
- What can be prepared usefully before the actual request is known?
- When should the interaction layer start, update, stop or resume background work?
- What happens when a request or correction arrives during unfinished reasoning?
- Which information should be private to S2 and which should reach S1?
- How can existing dialogue data become causal scheduling and revision supervision?
- How can causal transcript-conditioned teacher reasoning supervise the audio-conditioned student without future or speaker-information leakage?
- How can evaluation separate background reasoning gains from memory, extra compute and easier input?

## Landscape summary
Reasoning before the next input and interruptible asynchronous processing already have close precedents.
Structured state, conversation memory and request reasoning solve different problems and need separate controls.
An unfinished private reasoning trace is not automatically a grounded result or a resumable provider state.
Existing speech corpora supply conversations and timing, but not the proposed scheduling, validity and sharing labels.
Text-to-audio reasoning distillation has direct precedents; causal prefixes, partial-trace revision and group attribution remain the proposed extension.

## Paper notes

### [2026] Don't Wait to Reply: Towards Responsive yet Thoughtful Dialogue through Proactive Thinking
Ante Wang, Jiaqi Fu, Xuanyi Chen, Ruotian Ma, Zhaopeng Tu, Weizhi Ma, Yang Liu · arXiv preprint · 2607.03093v1 · verified
- **Problem**: Reactive reasoning adds delay after each reply.
- **Method**: Precompute likely next-turn reasoning; interrupt on arrival, then reuse or extend suitable work.
- **Reported scope/result**: Training-free evaluation in three time-aware dialogue environments.
- **Relevance**: Closest precedent for the central idea.
- **Limitation**: Predicting a next reply differs from maintaining a long, changing group conversation.
- **Primary source**: https://arxiv.org/abs/2607.03093v1

### [2026] LTS-VoiceAgent: A Listen-Think-Speak Framework for Efficient Streaming Voice Interaction via Semantic Triggering and Incremental Reasoning
Wenhao Zou, Yuwei Miao, Zhanyu Ma, Jun Xu, Jiuchong Gao, Jinghua Hao, Renqing He, Jingwen Xu · arXiv preprint · 2601.19952v1 · verified
- **Problem**: Sequential voice processing delays reasoning.
- **Method**: Semantic prefix triggers, background state updates and concurrent response generation.
- **Reported scope/result**: Streaming QA and Pause-and-Repair evaluation.
- **Relevance**: Close precedent for trigger selection and structured notes.
- **Limitation**: Does not establish long multi-party preparation or speaker-scoped memory.
- **Primary source**: https://arxiv.org/abs/2601.19952v1

### [2026] Building Interactive Real-Time Agents with Asynchronous I/O and Speculative Tool Calling
Coleman Hooper, Minwoo Kang, Suhong Moon, Nicholas Lee, Eric Wen, John Wawrzynek, Michael W. Mahoney, Yakun Sophia Shao, Amir Gholami, Kurt Keutzer · arXiv preprint · 2605.13360v1 · verified
- **Problem**: New input can invalidate ongoing reasoning and tools.
- **Method**: Interruptible event input, editable tool calls and clock-based training.
- **Reported scope/result**: Reported speedups on asynchronous agent tasks.
- **Relevance**: Useful training and cancellation design.
- **Limitation**: Tool-centric evaluation is not continuous multi-speaker speech.
- **Primary source**: https://arxiv.org/abs/2605.13360v1

### [2026] DuplexOmni: Real-Time Listening, Seeing, Thinking, and Speaking for Full-Duplex Interaction
Muye Huang, Lingling Zhang, Xingyu Yu, Lei Shi, Zhanyu Ma, Jun Xu, Jiuchong Gao, Jinghua Hao, Renqing He, Jun Liu · arXiv preprint · 2606.09186v1 · verified
- **Problem**: Deep reasoning must coexist with immediate interaction.
- **Method**: Asynchronous interaction/thinking layers and Writer-Director data construction.
- **Reported scope/result**: Streaming results support real-time interaction in the reported system.
- **Relevance**: Our existing backbone and control-data recipe.
- **Limitation**: Its request-driven interface does not establish this preparation policy.
- **Primary source**: https://arxiv.org/abs/2606.09186v1

### [2024] Agents Thinking Fast and Slow: A Talker-Reasoner Architecture
Konstantina Christakopoulou, Shibl Mourad, Maja Matarić · arXiv preprint · 2410.08328v1 · verified
- **Problem**: Conversation and planning have different timing needs.
- **Method**: A fast Talker uses state updated by a slower Reasoner.
- **Reported scope/result**: Architecture discussion grounded in sleep coaching.
- **Relevance**: Precedent for sharing state rather than every reasoning token.
- **Limitation**: Not a long multi-speaker duplex evaluation.
- **Primary source**: https://arxiv.org/abs/2410.08328v1

### [2025] Thinking While Speaking: Inference-Time Knowledge Transfer for Responsive and Intelligent Conversational Voice Agents
Vidya Srinivas, Zachary Englhardt, Vikram Iyer, Shwetak Patel · arXiv preprint · 2511.07397v3 · verified
- **Problem**: Reasoner delay makes voice responses slow.
- **Method**: Train a small talker to incorporate streamed reasoner information.
- **Reported scope/result**: Released synthetic conversational-infill training recipe.
- **Relevance**: Supports explicit supervision for using late information.
- **Limitation**: Immediate speech and infill do not establish silent pre-request reasoning.
- **Primary source**: https://arxiv.org/abs/2511.07397v3

### [2026] MultiTalk: Scaling Full-Duplex Speech Models to Long, Multi-Party, Bilingual Conversation
Ke Wang, Houxing Ren, Zimu Lu, Yunqiao Yang, Zhuofan Zong, Mingjie Zhan, Hongsheng Li · arXiv preprint · 2609.36903v1 · verified
- **Problem**: Full-duplex models struggle with long group conversations.
- **Method**: Synthetic dialogue scripts, parallel speech and aligned text; staged Moshi-style training.
- **Reported scope/result**: 54.4k-hour MultiTalkPT and 3.2k-hour MultiTalkFT reported.
- **Relevance**: Closest speech-data ingredient for this proposal.
- **Limitation**: Does not supply our pre-thinking scheduling or reuse labels.
- **Primary source**: https://arxiv.org/abs/2609.36903v1

### [2026] GroupMemBench: Benchmarking LLM Agent Memory in Multi-Party Conversations
Jingbo Yang, Kwei-Herng Lai, Xiaowen Wang, Shiyu Chang, Yaar Harari, Evgeniy Gabrilovich · arXiv preprint · 2605.14498v2 · verified
- **Problem**: Question interpretation depends on the asker.
- **Method**: Speaker-conditioned queries over synthetic group history.
- **Reported scope/result**: Tests updates, ambiguity and abstention.
- **Relevance**: Motivates speaker-specific memory and controls.
- **Limitation**: Text-only benchmark; not an interactive speech training set.
- **Primary source**: https://arxiv.org/abs/2605.14498v2

### [2026] MSI-Bench: Evaluating Multi-Speaker Voice Interaction for Collaborative AI Agents
Chenxu Xiong, Dongming Shen, Yuzhi Tang, Wentao Ma, Mu Li, Alex Smola · arXiv preprint · 2609.24812v1 · verified
- **Problem**: Voice agents must attribute context and requests correctly.
- **Method**: Group audio followed by assistant-directed tasks.
- **Reported scope/result**: 1,152 bilingual evaluation cases.
- **Relevance**: Useful held-out speaker/context evaluation.
- **Limitation**: Mostly short scripted speech; does not test our live scheduling.
- **Primary source**: https://arxiv.org/abs/2609.24812v1

### [2025] Data-Centric Improvements for Enhancing Multi-Modal Understanding in Spoken Conversation Modeling
Maximillian Chen, Ruoxi Sun, Sercan O Arik · Findings of ACL 2025 · 2025.findings-acl.71 · verified
- **Problem**: A spoken question may have several meanings.
- **Method**: ASK-QA renders ambiguity/clarification dialogues from Abg-CoQA.
- **Reported scope/result**: Reported spoken clarification evaluation and model customization.
- **Relevance**: Ingredient for answer-versus-clarify supervision.
- **Limitation**: Dedicated ASK-QA release not verified; underlying text repository is reachable.
- **Primary source**: https://aclanthology.org/2025.findings-acl.71/

### [2024] Efficient Data Generation for Source-grounded Information-seeking Dialogs: A Use Case for Meeting Transcripts
Lotem Golany, Filippo Galgani, Maya Mamo, Nimrod Parasol, Omer Vandsburger, Nadav Bar, Ido Dagan · Findings of EMNLP 2024 · 2024.findings-emnlp.106 · verified
- **Problem**: Meeting-grounded answers need attributable evidence.
- **Method**: Generated dialogues with human verification and evidence spans.
- **Reported scope/result**: Released Meeting Information Seeking Dialogs (MISeD).
- **Relevance**: Meeting QA and grounded-note supervision.
- **Limitation**: Completed-meeting context needs causal prefix filtering.
- **Primary source**: https://aclanthology.org/2024.findings-emnlp.106/

### [2021] QMSum: A New Benchmark for Query-based Multi-domain Meeting Summarization
Ming Zhong, Da Yin, Tao Yu, Ahmad Zaidi, Mutethia Mutuma, Rahul Jha, Ahmed Hassan, Asli Celikyilmaz, Yang Liu, Xipeng Qiu (邱锡鹏), Dragomir Radev · NAACL 2021 · 2021.naacl-main.472 · verified
- **Problem**: Meeting queries need relevant evidence selected.
- **Method**: Query-focused summaries with relevant transcript spans.
- **Reported scope/result**: 1,808 query-summary pairs over 232 meetings.
- **Relevance**: Evidence selection and original meeting links.
- **Limitation**: Summary targets may require speech not yet heard.
- **Primary source**: https://aclanthology.org/2021.naacl-main.472/

### [2026] Speak or Stay Silent: Context-Aware Turn-Taking in Multi-Party Dialogue
Kratika Bhagtani, Mrinal Anand, Yu Chen Xu, Amit Kumar Singh Yadav · arXiv preprint · 2603.11409v1 · verified
- **Problem**: Participation depends on conversational context.
- **Method**: Context-based SPEAK/SILENT prediction with supervised adaptation.
- **Reported scope/result**: Released multi-party decision data and recipe.
- **Relevance**: Useful inspiration for separate addressing decisions.
- **Limitation**: The next human speaker is not an optimal assistant or pre-thinking label.
- **Primary source**: https://arxiv.org/abs/2603.11409v1

### [2026] MuPPET: A Benchmark for Contextual Privacy of LLM Assistants in Multi-Party Conversations
Elena Sofia Ruzzetti, Cornelius Emde, Sangdoo Yun, Seong Joon Oh, Martin Gubri · arXiv preprint · 2606.23217v1 · verified
- **Problem**: Useful group history may be inappropriate to disclose.
- **Method**: Evaluate assistance together with contextual privacy.
- **Reported scope/result**: 562 synthetic workplace conversations.
- **Relevance**: Audience-sensitive use of background notes.
- **Limitation**: Text-only; does not establish audio consent or live disclosure control.
- **Primary source**: https://arxiv.org/abs/2606.23217v1

### [2024] LongMemEval: Benchmarking Chat Assistants on Long-Term Interactive Memory
Di Wu, Hongwei Wang, Wenhao Yu, Yuwei Zhang, Kai-Wei Chang, Dong Yu · ICLR 2025 · 2410.10813 · verified
- **Problem**: Long histories require updates and selective recall.
- **Method**: Evaluate extraction, temporal reasoning, updates and abstention.
- **Reported scope/result**: 500 curated long-memory questions.
- **Relevance**: Memory-only baseline and knowledge-update tests.
- **Limitation**: Dyadic text histories; background reasoning remains a separate question.
- **Primary source**: https://arxiv.org/abs/2410.10813

### [2025] Teaching Audio Models to Reason: A Unified Framework for Source- and Layer-wise Distillation
Runyan Yang, Yuke Si, Yingying Gao, Junlan Feng, Chao Deng, Shilei Zhang · arXiv preprint · 2509.18579v1 · verified
- **Problem**: Audio models lag text models on reasoning.
- **Method**: Transfer from a text teacher with source- and layer-wise distillation.
- **Reported scope/result**: Audio reasoning framework and evaluation.
- **Relevance**: Direct precedent for text-to-audio reasoning transfer.
- **Limitation**: Does not establish causal group prefixes or request-time preemption.
- **Primary source**: https://arxiv.org/abs/2509.18579v1

### [2026] X³-OPD: Distilling Reasoning into Large Audio-Language Models via On-Policy Alignment
Dongjie Fu, Di Cao, Xize Cheng, Zihan Zhang, Wenxu Jia, Yifu Chen, Shengpeng Ji, Yu Zhang, Tao Jin · arXiv preprint · 2607.21550v1 · verified
- **Problem**: Teacher-written traces can diverge from student acoustic perception.
- **Method**: Audio-conditioned student rollouts receive matched-text teacher guidance.
- **Reported scope/result**: Reasoning benchmarks and preservation analyses.
- **Relevance**: Close precedent for the proposed conditional distributions and a later on-policy stage.
- **Limitation**: Uses matched text and verified answers; our pre-request teacher must not see the future request or answer.
- **Primary source**: https://arxiv.org/abs/2607.21550v1

### [2025] Step-Audio-R1 Technical Report
Fei Tian, Xiangyu Tony Zhang, Yuxin Zhang, Haoyang Zhang, Yuxin Li, Daijiao Liu, Yayue Deng, Donghang Wu, Jun Chen, Liang Zhao, Chengyuan Yao, Hexin Liu, Eng Siong Chng, Xuerui Yang, Xiangyu Zhang, Daxin Jiang, Gang Yu · arXiv preprint · 2511.15848v1 · verified
- **Problem**: Reasoning must remain grounded in acoustic evidence.
- **Method**: Modality-grounded reasoning distillation for audio tasks.
- **Reported scope/result**: Speech, sound and music reasoning evaluation.
- **Relevance**: Motivates separate supervision for cues absent from transcripts.
- **Limitation**: Clip-level reasoning is not our long multi-speaker preparation policy.
- **Primary source**: https://arxiv.org/abs/2511.15848v1

## Open gaps and opportunities
- Whether selected background analysis improves later group-context answers beyond memory maintenance at matched compute. These works cover anticipation, streaming state or memory individually; their inspected evaluations do not establish this combination.
- How to preempt, revise and reuse background notes under new multi-speaker evidence without stale speech. Interruptible tools, S1/S2 handoff and group speech are established separately; the proposal needs a joint causal evaluation.
- Which small, grounded updates should reach S1 before a request, and whether training enables useful silence and clarification. State sharing, late-result uptake, clarification, participation and privacy provide ingredients, rather than a verified unified policy.

## Proposal and resource boundary
The self-contained discussion is ../../prethinking.html. It models text teacher p_T(z | x_text, c) and audio student p_theta(z | x, c), with causal prefixes, private CoT supervision, request-time revision and a separate S1 scheduling policy. This work uses 0 GPUs and launches no inference/training. A possible controller-only pilot uses 2 H100 SXM 80 GB each: all S1 on GPU 0 and text S2 on GPU 1; maximum 2, sequential, no automatic fallback. It cannot validate the proposed audio student. Audio-student training resources remain unestimated until model selection and profiling.
