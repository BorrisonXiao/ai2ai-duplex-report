# Focused duplex literature review

Review cutoff: 2026-09-30. Four categories, five resources each; rows are not ranked.

## Reasoning and system designs

Five anchors span explicit reasoning while listening, latent listening-time cognition, a released text-LLM duplex backbone, concurrent formulation/articulation, and a released asynchronous frontend/backend. Moshi is compared separately in the synchronization shortlist.

| System / paper | Reasoning, backbone and speech path | Code / weights | Training release |
| --- | --- | --- | --- |
| [Think while listening](https://arxiv.org/abs/2510.07497) | Moshi/Helium 7B temporal + depth transformers; parallel user/agent audio and text. Silent text reasoning is interleaved with ASR and answer text; completeness and preference supervision. | Study-specific code/weights not located; released Moshi is a different checkpoint. | Recipe only; full 1.8M-example spoken-CoT collection not located. |
| [FLAIR](https://arxiv.org/abs/2603.17837) | Qwen2.5-7B + streaming Parakeet encoder + autoregressive speech decoder. Listening steps feed a soft vocabulary-weighted latent embedding; full-context teacher trains a causal inference model. | Dedicated implementation/checkpoint not located. | ELBO/SFT recipe; full mixture not located. |
| [MiniCPM-o 4.5](https://arxiv.org/abs/2604.27393) | Qwen3-8B (~9B system). Omni-Flow serializes timed windows. Main LLM predicts text/listen decisions; a small Llama/S3 speech-token decoder and streaming flow decoder synthesize audio. | Inference + realtime demo and weights; Apache-2.0. | General fine-tuning tools; complete duplex recipe and mixture not established. |
| [StepAudio 3 Realtime](https://arxiv.org/abs/2609.14005) | Step 3.7 Flash MoE (196B total/11B active) + AuT speech encoder. Two concurrent audio-LLM processes share parameters: private formulation and articulation, with playback-aware pacing and async tools. | Report/project demos; Realtime code/weights not located. Earlier Step releases are not this model. | Recipe; full training code/mixture not located. |
| [Realtime-Venus](https://arxiv.org/abs/2609.13814) | MiniCPM-o 4.5-derived 9B Audio/Omni frontend; causal 1 s chunks, persistent context, and an asynchronous backend. A harness returns backend text to the speaking frontend. | Inference/harness + Audio/Omni weights; Apache-2.0. Demo integration is Omni-based. | Methods; complete training package/mixture not located. |

## Synchronization and temporal interfaces

Five directly relevant works cover clock-aligned serialization, codec-rate multi-stream generation, speech/listening/action alignment, adaptive scheduling, and representation-level speaker/listener coupling. The last is an analysis, not another model architecture.

| Paper | Temporal mechanism | What it establishes | Access / remaining issue |
| --- | --- | --- | --- |
| [SyncLLM](https://arxiv.org/abs/2409.15594) | Llama 3-8B with deduplicated HuBERT units (25 Hz before deduplication); periodic speaker/chunk tokens align the sequence to a real-world clock. Speculative user chunks are replaced by observed input. | Synchronous full-duplex scheduling despite variable token counts; evaluates processing/network delay. | Official paper/demos; model code/weights not located. Clock alignment alone does not establish revision correctness. |
| [Moshi](https://arxiv.org/abs/2410.00037) | Mimi 12.5 Hz (80 ms) frames; temporal transformer plus depth transformer model parallel audio streams and aligned inner-monologue text. | A concrete shared acoustic grid, streaming speech generation, and low-latency duplex interaction. | Inference and fine-tuning code + weights. MIT/Apache code; model CC BY 4.0. A frame clock is not a semantic commitment policy. |
| [DuplexSLA](https://arxiv.org/abs/2605.20755) | Step-Audio 2 mini-derived ~7B model. A 160 ms clock joins two 80 ms listening features, one text/four audio tokens, and up to ten action tokens; queued action spillover and dual-side ASR. | Native concurrent speaking/listening plus timestamp-aligned planning, control and tool events. | Official repository says inference, weights and benchmark are forthcoming. Not a released checkpoint as of cutoff. |
| [AdaptDuplex](https://arxiv.org/abs/2609.29217) | Qwen3-Omni Thinker/Talker; 0.48/0.64/0.96 s windows, bounded text lead, and up to four indexed backend jobs. Cancelled/stale results are suppressed before injection. | Adaptive granularity and explicit backend-result admission already exist; not a new idea to simply cancel a stale job. | Paper verified; dedicated code/checkpoint not located. Joint speaker-owned state and actual playback still need controlled tests. |
| [Synchronization and Turn-Taking](https://arxiv.org/abs/2605.20356) | Moshi--Moshi appointment dialogues: lagged CKA compares speaker/listener hidden states; causal probes classify end-of-interpausal-unit hold/non-hold events. | Representational coupling and predictive timing signals vary with noise and speech activity bias. | Preprint; study artifacts not located. Restricted task; CKA/probe success is not causal reasoning consistency. |

## Benchmarks for the proposal

Five complementary tests cover streaming reasoning onset, grounded task completion, natural disfluency/tool use, post-interruption state revision, and speaker/addressee control. Their scores should not be merged into a leaderboard.

| Benchmark | Coverage / provenance | Useful measurements | Availability / blind spot |
| --- | --- | --- | --- |
| [SRQA](https://arxiv.org/abs/2510.07497) | TTS/LLM-rewritten ARC-E/C, SIQA, PIQA, GSM8K; mostly single-turn synthetic spoken questions. | Reasoning accuracy and post-question chain-of-thought delay; prefix sufficiency controls. | Construction in ICLR paper; released audio/eval package not located. CoT onset is not first useful audible answer. |
| [tau-Voice](https://arxiv.org/abs/2603.13686) | 278 airline/retail/telecom tasks; clean/realistic speech; full-duplex simulated user. ICML 2026 (PMLR 306). | Grounded pass@1, interruption behavior and voice interaction quality; tool/task consequences. | Code/tasks/simulator; provider APIs needed. Virtual time decouples simulation from wall-clock runtime; pin original revision (repo now tau3-bench). |
| [Full-Duplex-Bench v3](https://arxiv.org/abs/2604.04847) | Human recordings, five disfluency types, chained tools across four task domains. | Tool-selection F1, argument accuracy, pass@1; first response, tool and completion latencies. | Scoring/inference code + recording download. Tool F1 is not task success; exact and judge-assisted argument scores differ. |
| [EchoChain](https://arxiv.org/abs/2604.16456) | 200 controlled interrupted conversations; synthesized user/barge-in audio; four closed realtime models; paired half-duplex control. | Conversation/criterion pass rates and failures: contextual inertia, interruption amnesia, objective displacement. | Paper, prompts and examples verified; standalone code/audio release not located. Does not cover backchannels, side speech or detailed acoustic timing. |
| [Duplex-MPE](https://arxiv.org/abs/2609.31948) | 2,000 matched pairs / 4,000 synthetic streams; 3--4 human roles plus assistant; explicit/implicit address. | Response initiation, answer accuracy, silence preservation, floor release; speaker-owned update controls. | Paper verified; standalone code/audio release not located. Floor release is conditional on the assistant already speaking. |

## Training data and supervision sources

Five natural conversational resources are chosen for channel separation, temporal/speaker annotations, or task events. These are resources to construct supervision, not five existing reasoning-training mixtures.

| Resource | Scale / channels | What is annotated | Access / project use |
| --- | --- | --- | --- |
| [SmoothConv](https://huggingface.co/datasets/qualialabsAI/SmoothConv) | 100.53 h; Chinese; natural multi-party, multi-channel audio. | Expert transcripts, speaker IDs, turn state, timing and paralinguistic labels. | HF release; CC BY-NC 4.0. Control/speaker supervision; shares source conversations with DuplexConv. |
| [DuplexConv](https://huggingface.co/datasets/OpenT2S/DuplexConv) | 2,000.21 h; Chinese; natural multi-party, multi-channel audio. | LLM-assisted transcripts, per-track VAD, speaker/turn segments, acoustic and scene labels. | HF release; CC BY-NC 4.0. Larger timing pretraining; audit labels and split by underlying source session. |
| [otoSpeech Task](https://huggingface.co/datasets/otoearth/otoSpeech-full-duplex-task-oriented-20h) | 20.006 h; 58 English sessions; two-speaker 48 kHz channels; seven task types. | Synchronized events, stimuli, participant artifacts and task-related metadata. | Gated HF files/contact acceptance; CC BY 4.0. Task-evidence alignment; verify outcomes before treating as reasoning labels. |
| [otoSpeech conversational](https://huggingface.co/datasets/otoearth/otoSpeech-full-duplex-processed-141h) | 280 h raw / 141 h curated; English; separate speaker channels; curated 44.1 kHz. | Session/speaker metadata, redactions, surveys; natural overlap and timing. | Gated HF files/contact acceptance; CC BY 4.0. Listening robustness; curated hours are a subset, not extra data. |
| [Open Yap 1K](https://github.com/The-Agentic-Data-Co/open-yap-1k) | 1,000 h; 1,602 English conversations; 239 speakers; separate 48 kHz channels. | Word-level transcripts, speaker/device metadata, overlap and turn-gap statistics. | Public sample; full corpus by request/Data Use Agreement. Natural conversation, not an ungated full release. |

## Synthesis and open gaps

G1: Jointly measure evidence age, correct useful audible response time, and unsafe commitment under late corrections.
G2: Maintain speaker-owned hypothesis versions across concurrent capture, reasoning, synthesis and playback.
G3: Establish causal end-to-end consistency across corrected frontend state, pending tools and output queues, beyond cancellation alone.
G4: Validate adaptive temporal interfaces against real wall-clock deadlines and compute contention, not only virtual-clock task scores.
G5: Construct auditable prefix-sufficiency, revision and addressee labels without future-evidence leakage or cross-corpus session contamination.

## Five major research questions

### RQ1: Think while listening

When is partial speech sufficient to begin useful reasoning, and when should an emerging hypothesis remain provisional?

Hypothesis: A trigger conditioned on available evidence and correction risk improves the correct-answer/latency frontier over end-of-turn and fixed-prefix triggers.

Small experiment: 200 matched late-constraint questions with two suffixes sharing an identical prefix; compare end-of-turn, fixed-prefix and calibrated triggers under the same evidence and decode budgets.

Prior-work distinction: Early or latent reasoning while listening already exists; the candidate contribution is risk-calibrated revision under delayed/jittered evidence, not the concurrency claim itself.

### RQ2: Think while speaking

How far can reasoning and synthesis run ahead of playback without committing to an answer that new evidence will invalidate?

Hypothesis: Evidence-tagged output queues and a bounded playback lead reduce stale audible claims at matched response-quality and compute budgets.

Small experiment: Deliver a correction before generation, during synthesis, while queued, or after playback; compare unrestricted lead, fixed-duration lead and evidence-aware admission.

Prior-work distinction: Dual-process reasoning and bounded lead already exist. Test an explicit causal playback commitment boundary, rather than merely producing a faster first sound.

### RQ3: Listen while speaking

Can new input update the right speaker/task hypothesis while the system speaks, without mistaking backchannels or side conversations for corrections?

Hypothesis: Per-speaker evidence watermarks and selective state invalidation improve correction accuracy without increasing needless interruption or side-speech responses.

Small experiment: Use matched corrections, backchannels and other-directed utterances with oracle versus predicted speaker/addressee labels; compare global versus speaker-owned state under matched load.

Prior-work distinction: Turn-taking and addressee tests are not new. The candidate is their coupling to causal reasoning-state ownership; attribution noise must be separated from reasoning failure.

### RQ4: Synchronize listening, reasoning and speaking

Which temporal interface remains reliable when speaking rate, inference speed, network delay and backend latency vary independently?

Hypothesis: A scheduler observing evidence age and audio-buffer duration has fewer missed deadlines and stale claims than fixed-window scheduling at matched task accuracy.

Small experiment: Replay identical dialogues across speech-rate, jitter and compute-contention conditions; compare fixed 80 ms/1 s interfaces where implementable with a two- or three-level adaptive controller.

Prior-work distinction: Fixed clocks, adaptive windows and action alignment already exist. The target is a causal consistency/robustness claim under heterogeneous clocks; virtual-time results alone are insufficient.

### RQ5: Revise while delegating

What should be canceled, reused or withheld when a speaker correction arrives between backend launch, result return and audible delivery?

Hypothesis: Speaker/task-versioned dependency checks at both result admission and playback reduce stale-answer failures beyond an existing cancellation-only baseline.

Small experiment: Inject corrections into a simulated 0.5/2/5 s backend at launch, inflight, return and pre-playback stages; compare blind injection, explicit cancel/stale suppression, and joint result/output validation.

Prior-work distinction: AdaptDuplex already cancels jobs and suppresses stale results. Candidate novelty requires speaker-specific dependency plus audible-commitment consistency, not renaming that mechanism.

## References

- [Can Speech LLMs Think while Listening?](https://arxiv.org/abs/2510.07497). Shih, Yi-Jen, Raj, Desh, Wu, Chunyang, Zhou, Wei, Bong, SK, Gaur, Yashesh, Mahadeokar, Jay, Kalinli, Ozlem, Seltzer, Mike. ICLR 2026; 2025-10-08.
- [The Silent Thought: Modeling Internal Cognition in Full-Duplex Spoken Dialogue Models via Latent Reasoning](https://arxiv.org/abs/2603.17837). Wu, Donghang, Zhang, Tianyu, Li, Yuxin, Liu, Hexin, Chen, Chen, Chng, Eng Siong, Bengio, Yoshua. Preprint / technical report; 2026-03-18.
- [MiniCPM-o 4.5: Towards Real-Time Full-Duplex Omni-Modal Interaction](https://arxiv.org/abs/2604.27393). Cui, Junbo, Xu, Bokai, Wang, Chongyi, Yu, Tianyu, Sun, Weiyue, Xu, Yingjing, Wang, Tianran, He, Zhihui, Ma, Wenshuo, Cai, Tianchi, Gui, Jiancheng, Zhang, Luoyuan, Sun, Xian, Huang, Fuwei, Chen, Moye, Lin, Zhuo, Liu, Hanyu, Gui, Qingxin, Han, Qingzhe, Wen, Yuyang, Liu, Huiping, Wang, Rongkang, Zhang, Yaqi, Wei, Hongliang, Chen, Chi, Li, You, Fang, Kechen, Zhou, Jie, Li, Yuxuan, Zeng, Guoyang, Xiao, Chaojun, Lin, Yankai, Han, Xu, Sun, Maosong, Liu, Zhiyuan, Yao, Yuan. Preprint / technical report; 2026-04-30.
- [StepAudio 3 Realtime Technical Report](https://arxiv.org/abs/2609.14005). Lin, Bin, Zhao, Bo, Zhang, Boyang, Wu, Boyong, Yan, Chao, Geng, Chen, Wu, Chen, Yi, Cheng, Feng, Chengli, Zhu, Chenglin, Feng, Chengting, Yao, Chengyuan, Liu, Daijiao, Wan, DanNi, Jiang, Daxin, Li, Dongjian, Pang, Dongqing, Tian, Fei, Tian, Feng, Li, Future, Yu, Gang, Yang, Guanglong, Zhang, Haoyang, Wang, Hongyuan, Peng, Jia, Song, Jiahao, Xue, Jialong, Fan, Jiamin, Zhen, Jiangjie, Gao, Jianzheng, Wen, Jincheng, Liang, Jinghua, Gong, Jinglan, Chen, Jun, Xie, Li, Zhao, Liang, Zhang, Lifang, Ji, Lingli, Cai, Lun, Xu, Min, Li, Peilin, Yang, Peng, Tan, Pengfei, Lin, Qingjian, Du, Qinxin, Xiong, Ruijie, Li, Runze, Hu, Shenghua, Qin, Shengqian, Qiu, Shi, Tu, Siqi, Zhou, Siyi, Deng, Tianjiao, Lu, Wanying, Niu, Weiming, Sun, Wen, Qu, WenWen, Zhang, Xiangyu, Zhang, Xianwei, Su, Xiaosu, Chen, Xing, Liu, Xinyu, Yang, Xuerui, Wu, Yan, Li, Yang, Yang, Yang, Huang, Yechang, Zhu, Yibo, Zhang, Yifan, Yan, Yinuo, Chen, Youjun, Fu, Yu, Luo, Yu, Zhou, Yu, Chen, Yujie, Wang, Yumang, Ju, Yunzhou, Yang, Yuxiang, Li, Yuxin, Zhang, Yuxin, Liu, Zekai, Yao, Zengwei, Yuan, Zhaoxin, Mou, Zhenwei, Zhang, Zhiquan, Wu, Zhiyue, Li, Zichao, Zhou, Zichao, Ren, Ziqi, Wang, Zixuan. Preprint / technical report; 2026-09-12.
- [Realtime-Venus: A full-duplex interaction system with asynchronous delegation](https://arxiv.org/abs/2609.13814). Ant Group. Preprint / technical report; 2026-09-12.
- [Beyond Turn-Based Interfaces: Synchronous LLMs as Full-Duplex Dialogue Agents](https://arxiv.org/abs/2409.15594). Veluri, Bandhav, Peloquin, Benjamin N, Yu, Bokai, Gong, Hongyu, Gollakota, Shyamnath. EMNLP 2024; 2024-09-23.
- [Moshi: a speech-text foundation model for real-time dialogue](https://arxiv.org/abs/2410.00037). Défossez, Alexandre, Mazaré, Laurent, Orsini, Manu, Royer, Amélie, Pérez, Patrick, Jégou, Hervé, Grave, Edouard, Zeghidour, Neil. Preprint / technical report; 2024-09-17.
- [DuplexSLA: A Full-Duplex Spoken Language Model with Synchronized Speech, Language, and Action](https://arxiv.org/abs/2605.20755). Zhang, Haoyang, Chen, Jun, Wu, Donghang, Li, Yuxin, Zhang, Yuxin, Zhang, Xiangyu Tony, Liu, Che, Lin, Qingjian, Peng, Yizhou, Liu, Hexin, Chng, Eng Siong, Yan, Chao, Wu, Boyong, Huang, Yechang, Yang, Xuerui, Tian, Fei. Preprint / technical report; 2026-05-20.
- [AdaptDuplex: from static to adaptive full-duplex spoken dialogue](https://arxiv.org/abs/2609.29217). Zhou, Zhiyang, Shang, Yingxin, Wang, Zhou, Cai, Hongwei, Wang, Weixu, Zhou, Shuran, Zhao, Shuofeng, Fan, Wenke, Guo, Qingxiang, Yang, Dawei, Yang, Lin, Song, Yang. Preprint / technical report; 2026-09-24.
- [Synchronization and Turn-Taking in Full-Duplex Speech Dialogue Models](https://arxiv.org/abs/2605.20356). Riera, Pablo, Brusco, Pablo, Kuo, Cristina, Sancinetti, Marcelo, Branavan, S. R. K.. Preprint / technical report; 2026-05-19.
- [τ-Voice: Benchmarking Full-Duplex Voice Agents on Real-World Domains](https://arxiv.org/abs/2603.13686). Ray, Soham, Dhandhania, Keshav, Barres, Victor, Narasimhan, Karthik. ICML 2026; 2026-03-14.
- [Full-Duplex-Bench-v3: Benchmarking Tool Use for Full-Duplex Voice Agents Under Real-World Disfluency](https://arxiv.org/abs/2604.04847). Lin, Guan-Ting, Chen, Chen, Chen, Zhehuai, Lee, Hung-yi. Preprint / technical report; 2026-04-06.
- [EchoChain: A Full-Duplex Benchmark for State-Update Reasoning Under Interruptions](https://arxiv.org/abs/2604.16456). Modi, Smit Nautambhai, Mahajan, Gandharv, Wetter, Marc, Welles, Randall. Preprint / technical report; 2026-04-08.
- [Duplex-MPE: Benchmarking Multi-Party Interaction in Full-Duplex Dialogue](https://arxiv.org/abs/2609.31948). Ma, Chengqian, Feng, Wenhao, Jin, Weixuan, Dai, Gaole, Xie, Tianyu, Ma, Yuexiao, Kang, Zhaolu, Zhao, Xiangyu, Zheng, Xiawu, Chao, Fei. Preprint / technical report; 2026-09-25.
- [Mind-Paced Speaking: A Dual-Brain Approach to Real-Time Reasoning in Spoken Language Models](https://arxiv.org/abs/2510.09592). Wu, Donghang, Zhang, Haoyang, Chen, Jun, Xiangyu, Zhang, Liu, Hexin, Chng, Eng Siong, Tian, Fei, Yang, Xuerui, Zhang, Xiangyu, Jiang, Daxin, Yu, Gang. Preprint / technical report; 2025-10-10.
- [Context Spanning: A Communication Framework for Full-Duplex Speech Models and External LLM Backends](https://arxiv.org/abs/2609.33443). Go, Seonghyeon, Kim, Yongwoo, Cha, Hyeonjin, Shin, Jaeho. Preprint / technical report; 2026-09-27.

## Per-paper notes

### Can Speech LLMs Think while Listening?

Problem: Direct prior work for both semantic sufficiency and revision-aware reasoning in the original proposal.

Method: Moshi / Helium 7B + Mimi Text monologue interleaves streaming ASR, silent text CoT and answer text alongside audio. Moshi temporal + depth transformers; reasoning tokens have no corresponding spoken output. Question-completeness supervision starts CoT early; correctness and length DPO improve adaptation.

Results: Authors report 2.4× mean reasoning accuracy over Moshi and about 70% lower reasoning latency without accuracy loss.

Relevance: Direct prior work for both semantic sufficiency and revision-aware reasoning in the original proposal.

Limitations: Single-turn spoken reasoning suite; 480 ms ASR look-ahead; benchmark/model release not located. Reasoning latency is not first useful spoken answer latency.

### The Silent Thought: Modeling Internal Cognition in Full-Duplex Spoken Dialogue Models via Latent Reasoning

Problem: Listening-time silence/padding does not exploit ongoing latent reasoning.

Method: Soft vocabulary-weighted latent embeddings; ELBO/SFT from a full-context expert into a causal inference model.

Results: Authors evaluate reasoning and interaction improvements over their pretraining-only baseline; no independent reproduction or unified leaderboard in this review.

Relevance: Direct alternative to explicit prefix chain-of-thought and a close prior to think-while-listening claims.

Limitations: Complete mixture and dedicated artifacts not located; teacher access to future context is training supervision, not permitted evaluation evidence.

### MiniCPM-o 4.5: Towards Real-Time Full-Duplex Omni-Modal Interaction

Problem: Concrete open alternative to Moshi for a streaming encoder + text reasoning backbone.

Method: Qwen3-8B; about 9B total Omni-Flow serializes time windows of audio, video and assistant output; [listen] when silent. Small Llama speech-token decoder + S3 tokens + streaming flow-matching waveform decoder. Explicit listen/speak decision; main LLM generates text, separate decoder generates speech.

Results: In the paper’s ablation, 1.0 s windows outperform 0.1 / 0.2 s on the tested language tasks.

Relevance: Concrete open alternative to Moshi for a streaming encoder + text reasoning backbone.

Limitations: Shorter windows trade response opportunity against language competence. A full duplex-training mixture is not released.

### StepAudio 3 Realtime Technical Report

Problem: Strong reference for coordinating speech, private reasoning and tool execution.

Method: Step 3.7 Flash MoE: 196B total / 11B active AuT encoder + adapter; user and model audio feed shared conversational context. Streaming speech generator; detailed generator internals are less specified than the LLM. Listen / speak / start / end states; private think-while-speaking; asynchronous tools.

Results: Authors report 98.9 Overall on Artificial Analysis Full-Duplex Bench and 56.0% macro task success on τ-Voice.

Relevance: Strong reference for coordinating speech, private reasoning and tool execution.

Limitations: Reported benchmark scores use their own protocol. No StepAudio 3 Realtime checkpoint or training release was located; earlier Step-Audio releases are separate models.

### Realtime-Venus: A full-duplex interaction system with asynchronous delegation

Problem: Released architecture and harness for testing revisions while a backend task is pending.

Method: MiniCPM-o 4.5-derived Audio and Omni frontends; 9B family One-second causal chunks; retained frontend state; separate background task loop. Frontend text and speech generation; text results admitted back into the stream. Explicit foreground / delegation outputs; harness executes background jobs asynchronously.

Results: Audio variant reports continuation of 97% / 88% / 86% for backchannel / other-directed / background speech in FDB v1.5.

Relevance: Released architecture and harness for testing revisions while a backend task is pending.

Limitations: Audio and Omni evaluations differ. Released harness/demo integration is Omni-based; do not assume every paper setting is reproduced.

### Beyond Turn-Based Interfaces: Synchronous LLMs as Full-Duplex Dialogue Agents

Problem: Variable text/unit sequence length must still track a real acoustic clock.

Method: Periodic speaker/chunk boundaries plus deduplicated semantic units and speculative user prediction/replacement.

Results: Authors demonstrate synchronous full-duplex generation and evaluate processing/network delay; no independent reproduction.

Relevance: Direct temporal-interface prior work, predating modern text-backbone duplex releases.

Limitations: Clock alignment does not itself establish correction-sensitive reasoning; dedicated released checkpoint not located.

### Moshi: a speech-text foundation model for real-time dialogue

Problem: Open foundation for the supplied paper; it already uses a pretrained LLM backbone.

Method: Helium 7B text LM + Mimi codec Synchronized user-audio, assistant-audio and assistant-text streams at 12.5 Hz. Temporal transformer models time; depth transformer predicts residual codec levels. Text inner monologue precedes acoustic generation; learned silence and overlap patterns.

Results: Paper reports 160 ms theoretical and approximately 200 ms practical latency under its setup.

Relevance: Open foundation for the supplied paper; it already uses a pretrained LLM backbone.

Limitations: Frame timing limits text bandwidth; basic inner monologue is not a private reasoning implementation.

### DuplexSLA: A Full-Duplex Spoken Language Model with Synchronized Speech, Language, and Action

Problem: Speaking, listening and structured actions need a shared temporal protocol.

Method: 160 ms shared clock; two listening features, one text/four audio outputs, bounded action tokens and queued action spillover.

Results: Authors evaluate integrated duplex/tool behavior on a reported 2,100-case benchmark; no independent reproduction.

Relevance: Very close prior work for explicit action/speech/listening synchronization.

Limitations: Official repository marks inference, checkpoints and benchmark as forthcoming at cutoff.

### AdaptDuplex: from static to adaptive full-duplex spoken dialogue

Problem: Very recent alternative for controlling the timing/capacity trade-off.

Method: Adaptive windows and bounded text lead; indexed backend launch/cancel; cancelled/stale results suppressed before injection.

Results: Reports 72.9 Final score on HumDial-FDBench; interruption and rejection have separate trade-offs.

Relevance: Cancellation alone is already implemented; joint speaker-owned result/output commitment must be differentiated.

Limitations: Paper verified; trained checkpoint and training package not located at the review cutoff.

### Synchronization and Turn-Taking in Full-Duplex Speech Dialogue Models

Problem: Determine whether speaker/listener hidden states synchronize and encode turn-taking signals.

Method: Moshi--Moshi appointment conversations; lagged CKA and causal end-of-interpausal-unit probes under noise/activity-bias variation.

Results: Authors report near-zero-lag coupling that degrades with noise and useful timing probes; no causal correctness guarantee.

Relevance: Representation-level synchronization evidence complementary to runtime clocks.

Limitations: Restricted conversational task; artifact package not located; probe quality is not revision correctness.

### τ-Voice: Benchmarking Full-Duplex Voice Agents on Real-World Domains

Problem: 278 airline / retail / telecom tasks; clean and realistic accents/noise; simulated full-duplex user.

Method: 278 airline / retail / telecom tasks; clean and realistic accents/noise; simulated full-duplex user. Metrics: Grounded pass@1; latency, interruptions and voice interaction quality.

Results: Original study reports voice-task success below its text baseline under both audio conditions.

Relevance: End-to-end task completion and correction consequences.

Limitations: Pin the task revision and simulator/provider configuration. Paper-clean, realistic and macro-domain scores are different conditions.

### Full-Duplex-Bench-v3: Benchmarking Tool Use for Full-Duplex Voice Agents Under Real-World Disfluency

Problem: Real human audio; five disfluency types; chained tool calls in four task domains.

Method: Real human audio; five disfluency types; chained tool calls in four task domains. Metrics: Tool selection F1, argument accuracy, pass@1, first response / tool / completion latency.

Results: Authors identify self-correction and hard multi-step reasoning as recurring failures.

Relevance: Self-corrections, hesitation and multi-step tool reasoning.

Limitations: Tool-selection F1 is not task completion. Judge-assisted and exact argument matching differ.

### EchoChain: A Full-Duplex Benchmark for State-Update Reasoning Under Interruptions

Problem: A model can acknowledge an interruption while its subsequent task-state reasoning remains wrong.

Method: Speech-onset-relative controlled interruptions, paired half-duplex control, and conversation-specific human-audited rubrics.

Results: Authors report no evaluated model above 50% conversation pass rate across 200 interrupted conversations; result not reproduced here.

Relevance: Direct benchmark predecessor for correction-sensitive ongoing reasoning.

Limitations: Four closed models; no backchannel/side-speech coverage or detailed acoustic timing; separate runnable release not located.

### Duplex-MPE: Benchmarking Multi-Party Interaction in Full-Duplex Dialogue

Problem: 2,000 matched scenario pairs / 4,000 streams; 3–4 human roles plus an assistant; explicit versus implicit address.

Method: 2,000 matched scenario pairs / 4,000 streams; 3–4 human roles plus an assistant; explicit versus implicit address. Metrics: Fresh response initiation, answer accuracy, silence preservation and floor release.

Results: Shows that frequent speech can coexist with wrong answers and failures to remain silent.

Relevance: Closest recent benchmark for the proposal’s multi-party speaker/stream-aware goal.

Limitations: Scenario roles do not imply natural human recordings. Floor release depends on whether the model was speaking.

### Mind-Paced Speaking: A Dual-Brain Approach to Real-Time Reasoning in Spoken Language Models

Problem: Full pre-response reasoning delays speech; interleaving may disrupt reasoning continuity.

Method: Concurrent formulation/articulation with shared Step-Audio 2 parameters; incremental thought segments and think-incomplete SFT.

Results: Authors report improved latency/quality trade-offs; their near-zero-latency configuration still depends on synthesis buffering.

Relevance: Established think-while-speaking predecessor, underlying Step-Audio R1.1 and referenced by StepAudio 3.

Limitations: Concurrent formulation does not establish correction-safe audible commitment; performance depends on the tested backbone/tasks.

### Context Spanning: A Communication Framework for Full-Duplex Speech Models and External LLM Backends

Problem: Fresh alternative to compressed backend conditioning; useful for evidence provenance.

Method: Moshi frontend + external text backend Backend text injected into duplex token frames through chunked causal prefill. Frontend independently produces speech after receiving raw reference text. Context injection must fit prefill + one decode step in an 80 ms frame budget.

Results: Reports QA and full-duplex evaluations with direct information injection.

Relevance: Fresh alternative to compressed backend conditioning; useful for evidence provenance.

Limitations: Very recent preprint. Some experiments use precomputed backend answers with fixed delay; that differs from live tool execution.
