# Candidate research ideas

Unranked candidate ideas; hypotheses, not results or established novelty. Grouped under the five report questions; no winners selected.

## I1: Calibrated prefix sufficiency under late constraints

Research question: RQ1.

**One liner:** Trigger private reasoning from causal prefix sufficiency and correction risk.

**Hypothesis:** Causal correction-risk calibration improves accuracy/latency over fixed prefix length without learning only speech duration.

**Proposed method:** Trigger private reasoning from causal prefix sufficiency and correction risk. Predict prefix sufficiency from causal input and track hypothesis versions; allow private inference before authorizing a task-specific spoken claim.

**Minimal experiment:** Train a small calibration head on paired shared-prefix questions; hold out templates/speaking rates and compare with fixed/end-of-turn triggers.

**Contribution type:** method

**Novelty rationale:** Early or latent reasoning while listening already exists; the candidate contribution is risk-calibrated revision under delayed/jittered evidence, not the concurrency claim itself.

**Risk:** medium

**Risk notes:** A sufficiency estimator may merely learn question-length or TTS cues.

**Expected outcome:** Either a better latency/accuracy frontier or a measured limit on prefix-only calibration.

**Closest prior work:** [Can Speech LLMs Think while Listening?](https://arxiv.org/abs/2510.07497), [The Silent Thought: Modeling Internal Cognition in Full-Duplex Spoken Dialogue Models via Latent Reasoning](https://arxiv.org/abs/2603.17837)

**Feasibility:** Pilot estimate, not measured: 12--24 GPU-hours; one A100 80 GB for a released 7--9B inference baseline, subject to runtime profiling. Estimates are per candidate, not a sum or training commitment. 200--500 paired controlled short dialogues; use synthetic causal-prefix pilot first, then licensed/gated recordings only after access approval. Keep benchmark test sets held out. low Small calibration head / inference controller; no foundation pretraining.

**Based on gaps:** G1, G5

## I2: Evidence-aware playback commitment fence

Research question: RQ2.

**One liner:** Admit task-specific output only while its evidence dependencies remain valid.

**Hypothesis:** Playback-stage dependency validation reduces stale audible claims beyond generation-stage validation alone.

**Proposed method:** Admit task-specific output only while its evidence dependencies remain valid. Separate private formulation from articulation, annotate queued output with evidence/state dependencies, revalidate unplayed output and repair already audible claims.

**Minimal experiment:** Inject corrections at generation, synthesis, queue and playback stages; compare the same model with and without playback revalidation.

**Contribution type:** method

**Novelty rationale:** Dual-process reasoning and bounded lead already exist. Test an explicit causal playback commitment boundary, rather than merely producing a faster first sound.

**Risk:** medium

**Risk notes:** Word/audio boundaries and mutable decoder state may prevent selective cancellation.

**Expected outcome:** Quantify whether queue-level revalidation reduces stale audible claims.

**Closest prior work:** [Mind-Paced Speaking: A Dual-Brain Approach to Real-Time Reasoning in Spoken Language Models](https://arxiv.org/abs/2510.09592), [StepAudio 3 Realtime Technical Report](https://arxiv.org/abs/2609.14005), [AdaptDuplex: from static to adaptive full-duplex spoken dialogue](https://arxiv.org/abs/2609.29217), [EchoChain: A Full-Duplex Benchmark for State-Update Reasoning Under Interruptions](https://arxiv.org/abs/2604.16456)

**Feasibility:** Pilot estimate, not measured: 8--20 GPU-hours; one A100 80 GB for a released 7--9B inference baseline, subject to runtime profiling. Estimates are per candidate, not a sum or training commitment. 200--500 paired controlled short dialogues; use synthetic causal-prefix pilot first, then licensed/gated recordings only after access approval. Keep benchmark test sets held out. medium Instrument text, synthesis and playback queues and dependency tags.

**Based on gaps:** G1, G2

## I3: Correction-aware bounded articulation lead

Research question: RQ2.

**One liner:** Adapt unplayed speech duration to correction risk rather than a token-count limit.

**Hypothesis:** A duration- and correction-risk-aware cap offers a better stale-claim/fluency frontier than a fixed lead limit.

**Proposed method:** Adapt unplayed speech duration to correction risk rather than a token-count limit. Separate private formulation from articulation, annotate queued output with evidence/state dependencies, revalidate unplayed output and repair already audible claims.

**Minimal experiment:** Sweep fixed-duration queue caps against a risk-aware cap on matched interrupted dialogues; report stale seconds, underruns and repair quality.

**Contribution type:** method

**Novelty rationale:** Dual-process reasoning and bounded lead already exist. Test an explicit causal playback commitment boundary, rather than merely producing a faster first sound.

**Risk:** medium

**Risk notes:** Short buffers may trade false commitments for stutter/underruns.

**Expected outcome:** A commitment/latency/fluency Pareto curve, including negative results.

**Closest prior work:** [Mind-Paced Speaking: A Dual-Brain Approach to Real-Time Reasoning in Spoken Language Models](https://arxiv.org/abs/2510.09592), [StepAudio 3 Realtime Technical Report](https://arxiv.org/abs/2609.14005), [AdaptDuplex: from static to adaptive full-duplex spoken dialogue](https://arxiv.org/abs/2609.29217), [EchoChain: A Full-Duplex Benchmark for State-Update Reasoning Under Interruptions](https://arxiv.org/abs/2604.16456)

**Feasibility:** Pilot estimate, not measured: 8--20 GPU-hours; one A100 80 GB for a released 7--9B inference baseline, subject to runtime profiling. Estimates are per candidate, not a sum or training commitment. 200--500 paired controlled short dialogues; use synthetic causal-prefix pilot first, then licensed/gated recordings only after access approval. Keep benchmark test sets held out. medium Duration estimator plus two- or three-level queue cap.

**Based on gaps:** G1, G4

## I4: Listening freshness under speaking load

Research question: RQ3.

**One liner:** Reserve ingestion capacity to keep new evidence from becoming stale during generation.

**Hypothesis:** Reserving ingestion capacity reduces correction failures attributable to generation contention, but not intrinsic encoder lookahead.

**Proposed method:** Reserve ingestion capacity to keep new evidence from becoming stale during generation. Prioritize fresh input ingestion under generation load; associate updates with speaker, addressee, task and hypothesis versions before invalidating dependent output.

**Minimal experiment:** Under matched speaking load, compare FIFO and ingestion-priority scheduling with a fixed encoder; log capture/arrival/incorporation delays separately.

**Contribution type:** method

**Novelty rationale:** Turn-taking and addressee tests are not new. The candidate is their coupling to causal reasoning-state ownership; attribution noise must be separated from reasoning failure.

**Risk:** low

**Risk notes:** Freshness may be dominated by encoder lookahead rather than scheduler priority.

**Expected outcome:** Identify whether contention or intrinsic lookahead limits correction responsiveness.

**Closest prior work:** [Duplex-MPE: Benchmarking Multi-Party Interaction in Full-Duplex Dialogue](https://arxiv.org/abs/2609.31948), [Synchronization and Turn-Taking in Full-Duplex Speech Dialogue Models](https://arxiv.org/abs/2605.20356), [Realtime-Venus: A full-duplex interaction system with asynchronous delegation](https://arxiv.org/abs/2609.13814)

**Feasibility:** Pilot estimate, not measured: 6--16 GPU-hours; one A100 80 GB for a released 7--9B inference baseline, subject to runtime profiling. Estimates are per candidate, not a sum or training commitment. 200--500 paired controlled short dialogues; use synthetic causal-prefix pilot first, then licensed/gated recordings only after access approval. Keep benchmark test sets held out. medium Instrument ingested-input watermarks and scheduler priorities.

**Based on gaps:** G2, G4

## I5: Speaker-owned revision states

Research question: RQ3.

**One liner:** Invalidate only hypotheses and output that depend on the speaker's relevant correction.

**Hypothesis:** Speaker-owned dependency states reduce irrelevant invalidation and stale relevant answers relative to a global state.

**Proposed method:** Invalidate only hypotheses and output that depend on the speaker's relevant correction. Prioritize fresh input ingestion under generation load; associate updates with speaker, addressee, task and hypothesis versions before invalidating dependent output.

**Minimal experiment:** Cross relevant correction/backchannel/other-directed input with oracle and predicted speaker labels; measure attribution and reasoning errors separately.

**Contribution type:** method

**Novelty rationale:** Turn-taking and addressee tests are not new. The candidate is their coupling to causal reasoning-state ownership; attribution noise must be separated from reasoning failure.

**Risk:** high

**Risk notes:** Attribution mistakes may erase any gain from state separation.

**Expected outcome:** Decompose attribution errors versus stale shared-reasoning errors.

**Closest prior work:** [Duplex-MPE: Benchmarking Multi-Party Interaction in Full-Duplex Dialogue](https://arxiv.org/abs/2609.31948), [Synchronization and Turn-Taking in Full-Duplex Speech Dialogue Models](https://arxiv.org/abs/2605.20356), [Realtime-Venus: A full-duplex interaction system with asynchronous delegation](https://arxiv.org/abs/2609.13814)

**Feasibility:** Pilot estimate, not measured: 12--28 GPU-hours; one A100 80 GB for a released 7--9B inference baseline, subject to runtime profiling. Estimates are per candidate, not a sum or training commitment. 200--500 paired controlled short dialogues; use synthetic causal-prefix pilot first, then licensed/gated recordings only after access approval. Keep benchmark test sets held out. high First oracle identities, then predicted diarization/addressee labels.

**Based on gaps:** G2, G5

## I6: Evidence-age-aware adaptive temporal quantum

Research question: RQ4.

**One liner:** Adapt chunk duration using evidence age, playback budget and compute deadlines.

**Hypothesis:** An evidence-age-aware controller has fewer deadline misses at matched accuracy than a fixed temporal quantum under jitter/load.

**Proposed method:** Adapt chunk duration using evidence age, playback budget and compute deadlines. Expose input watermarks, deadlines and predicted audio lead to the controller; adapt ingestion/generation quantum without using future speech or privileging one arm's compute.

**Minimal experiment:** Replay identical speech under controlled jitter/rates/contention using the same backbone and feature extractor; compare fixed and two/three-level scheduling.

**Contribution type:** method

**Novelty rationale:** Fixed clocks, adaptive windows and action alignment already exist. The target is a causal consistency/robustness claim under heterogeneous clocks; virtual-time results alone are insufficient.

**Risk:** high

**Risk notes:** Changing quantum can mismatch the model's training protocol.

**Expected outcome:** Measure robustness boundaries rather than claiming universal adaptivity.

**Closest prior work:** [Beyond Turn-Based Interfaces: Synchronous LLMs as Full-Duplex Dialogue Agents](https://arxiv.org/abs/2409.15594), [Moshi: a speech-text foundation model for real-time dialogue](https://arxiv.org/abs/2410.00037), [MiniCPM-o 4.5: Towards Real-Time Full-Duplex Omni-Modal Interaction](https://arxiv.org/abs/2604.27393), [DuplexSLA: A Full-Duplex Spoken Language Model with Synchronized Speech, Language, and Action](https://arxiv.org/abs/2605.20755), [AdaptDuplex: from static to adaptive full-duplex spoken dialogue](https://arxiv.org/abs/2609.29217), [τ-Voice: Benchmarking Full-Duplex Voice Agents on Real-World Domains](https://arxiv.org/abs/2603.13686)

**Feasibility:** Pilot estimate, not measured: 8--24 GPU-hours; one A100 80 GB for a released 7--9B inference baseline, subject to runtime profiling. Estimates are per candidate, not a sum or training commitment. 200--500 paired controlled short dialogues; use synthetic causal-prefix pilot first, then licensed/gated recordings only after access approval. Keep benchmark test sets held out. high Controller around a released streaming runtime; fixed feature extractors.

**Based on gaps:** G4

## I7: Joint backend-result and output dependency validation

Research question: RQ5.

**One liner:** Check state dependencies both when a job returns and before its answer becomes audible.

**Hypothesis:** Joint backend and playback dependency validation improves corrected outcomes beyond existing indexed cancellation and stale-result suppression.

**Proposed method:** Check state dependencies both when a job returns and before its answer becomes audible. Tag jobs/results and output segments with dependencies, reject invalidated results, and recompute only affected work; use read-only or simulated tools in the pilot.

**Minimal experiment:** Vary simulated backend delay and correction stage; compare blind admission, cancel/stale suppression, and joint speaker/task-output validation.

**Contribution type:** method

**Novelty rationale:** AdaptDuplex already cancels jobs and suppresses stale results. Candidate novelty requires speaker-specific dependency plus audible-commitment consistency, not renaming that mechanism.

**Risk:** medium

**Risk notes:** This duplicates AdaptDuplex unless joint speaker/output dependencies add measurable value.

**Expected outcome:** Determine whether a second commitment-stage check improves corrected task success.

**Closest prior work:** [Realtime-Venus: A full-duplex interaction system with asynchronous delegation](https://arxiv.org/abs/2609.13814), [AdaptDuplex: from static to adaptive full-duplex spoken dialogue](https://arxiv.org/abs/2609.29217), [Context Spanning: A Communication Framework for Full-Duplex Speech Models and External LLM Backends](https://arxiv.org/abs/2609.33443), [Full-Duplex-Bench-v3: Benchmarking Tool Use for Full-Duplex Voice Agents Under Real-World Disfluency](https://arxiv.org/abs/2604.04847), [τ-Voice: Benchmarking Full-Duplex Voice Agents on Real-World Domains](https://arxiv.org/abs/2603.13686)

**Feasibility:** Pilot estimate, not measured: 8--20 GPU-hours; one A100 80 GB for a released 7--9B inference baseline, subject to runtime profiling. Estimates are per candidate, not a sum or training commitment. 200--500 paired controlled short dialogues; use synthetic causal-prefix pilot first, then licensed/gated recordings only after access approval. Keep benchmark test sets held out. medium Versioned read-only/simulated jobs; cancellation baseline explicitly included.

**Based on gaps:** G2, G3

## I8: Virtual-time versus wall-clock consistency audit

Research question: RQ4.

**One liner:** Compare identical task traces under virtual replay and physical inference/playback time.

**Hypothesis:** Some virtual-time task-success advantages disappear or reverse when real inference/playback deadlines are enforced.

**Proposed method:** Compare identical task traces under virtual replay and physical inference/playback time. Expose input watermarks, deadlines and predicted audio lead to the controller; adapt ingestion/generation quantum without using future speech or privileging one arm's compute.

**Minimal experiment:** Replay the same deterministic tasks and model traces with virtual advancement versus measured physical time; isolate runtime/provider confounds.

**Contribution type:** diagnostic

**Novelty rationale:** Fixed clocks, adaptive windows and action alignment already exist. The target is a causal consistency/robustness claim under heterogeneous clocks; virtual-time results alone are insufficient.

**Risk:** low

**Risk notes:** Provider/runtime differences may confound the timing comparison.

**Expected outcome:** Expose which conclusions survive real deadlines and which are simulator artifacts.

**Closest prior work:** [Beyond Turn-Based Interfaces: Synchronous LLMs as Full-Duplex Dialogue Agents](https://arxiv.org/abs/2409.15594), [Moshi: a speech-text foundation model for real-time dialogue](https://arxiv.org/abs/2410.00037), [MiniCPM-o 4.5: Towards Real-Time Full-Duplex Omni-Modal Interaction](https://arxiv.org/abs/2604.27393), [DuplexSLA: A Full-Duplex Spoken Language Model with Synchronized Speech, Language, and Action](https://arxiv.org/abs/2605.20755), [AdaptDuplex: from static to adaptive full-duplex spoken dialogue](https://arxiv.org/abs/2609.29217), [τ-Voice: Benchmarking Full-Duplex Voice Agents on Real-World Domains](https://arxiv.org/abs/2603.13686)

**Feasibility:** Pilot estimate, not measured: 4--12 GPU-hours; one A100 80 GB for a released 7--9B inference baseline, subject to runtime profiling. Estimates are per candidate, not a sum or training commitment. 200--500 paired controlled short dialogues; use synthetic causal-prefix pilot first, then licensed/gated recordings only after access approval. Keep benchmark test sets held out. medium Timestamped trace harness, controlled delay and queue instrumentation.

**Based on gaps:** G1, G4

## Removed (with reason)

| Direction | Reason |
| --- | --- |
| Standalone indexed backend cancellation and stale-result suppression | Already explicitly implemented by AdaptDuplex (arXiv:2609.29217); no distinct research claim on its own. |
| Foundation-scale reproduction of FLAIR or StepAudio 3 Realtime | Not a feasible small pilot: complete training mixture not located and documented foundation-scale compute exceeds the skill's one-week pilot bound. |
