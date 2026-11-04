# Literature review: compact notes that track meeting changes

- Replace repeated snapshots with one current state or small source-supported edits.
- Preserve old and new states when owners, quantities, deadlines or decisions change.
- Test accuracy and request-time thinking alongside the entire earlier token cost.

Date: 2026-11-04; focused review of nine verified papers.

## What the sources support

Memory update operations, compact fact representations and explicit links between evolving events recur across the literature. These are design motivations. Most cited systems use retrieval or trained memory policies, while this study retains the full transcript and tests prompts with the existing readers. Reported gains do not transfer automatically.

## Paper table

| Paper | Publication | Method | Reported result | Use in this design | Status |
|---|---|---|---|---|---|
| [Mem0: Building Production-Ready AI Agents with Scalable Long-Term Memory](https://arxiv.org/abs/2504.19413) | arXiv preprint | Separate fact extraction from ADD/UPDATE/DELETE/NOOP memory operations using related existing memories. | Authors report better LoCoMo accuracy and substantially lower token/latency costs than their full-context comparison. | Use edits and explicit no-change output; preserve old versions instead of deleting revision evidence. | Verified primary source |
| [A-MEM: Agentic Memory for LLM Agents](https://arxiv.org/abs/2502.12110) | NeurIPS 2025 | Create atomic structured notes and link related memories; new evidence can update older note context. | Evaluations over six foundation models report gains from memory linking and evolution. | Use stable event IDs and explicit relationships; avoid copying keywords/tags that add cost without a tested benefit. | Verified primary source |
| [LongMemEval: Benchmarking Chat Assistants on Long-Term Interactive Memory](https://arxiv.org/abs/2410.10813) | ICLR 2025 | Evaluate extraction, cross-session reasoning, time, knowledge updates and unanswered questions; separate indexing, retrieval and reading. | The 500-question benchmark exposes long-history forgetting; decomposition and time-aware retrieval improve recall. | Score updates, ownership and uncertainty separately; a correct current state must not erase a relevant old state. | Verified primary source |
| [Recursively Summarizing Enables Long-Term Dialogue Memory in Large Language Models](https://arxiv.org/abs/2308.15022) | Neurocomputing (acceptance stated on arXiv; bibliographic publication year not inferred) | Generate a new compact memory from the previous memory and new dialogue, then use the latest memory. | Reported dialogue consistency gains with open and closed models; this does not guarantee lossless fact retention. | A latest-state replacement is an important simple control against accumulated snapshots. | Verified primary source |
| [MEM1: Learning to Synergize Memory and Reasoning for Efficient Long-Horizon Agents](https://arxiv.org/abs/2506.15841) | ICLR 2026 (author repository confirms acceptance) | Train a recurrent compact memory state with reinforcement learning rather than retaining the entire interaction. | Reports improved long-horizon task performance and smaller memory; requires training rather than prompting alone. | Motivates bounded current memory; the present pilot tests prompts without claiming to reproduce trained MEM1. | Verified primary source |
| [SimpleMem: Efficient Lifelong Memory for LLM Agents](https://arxiv.org/abs/2601.02553) | ICML 2026 | Filter low-information turns, extract self-contained facts, consolidate related content and retrieve according to the question. | Authors report improved LoCoMo F1 and lower inference tokens; exact gains depend on their retrieval-based setup. | Filter fillers and redundant confirmations, but keep short rejections that change decisions; preserve relative times when AMI has no calendar date. | Verified primary source |
| [AriadneMem: Threading the Maze of Lifelong Memory for LLM Agents](https://arxiv.org/abs/2603.03290) | arXiv preprint | Use information filtering and conflict-aware consolidation, preserving state transitions as temporal links. | Abstract reports stronger multi-hop F1 and lower runtime on LoCoMo; full experimental reproduction is outside this review. | Keep a compact change log alongside current facts; similarity alone must not merge different event states. | Verified primary source |
| [MemSIF: From Structured Interactions to Dual-Track Fact Memory for LLM Agents](https://arxiv.org/abs/2608.01742) | arXiv preprint; submitted to AAAI 2027 | Group coherent topical segments and link nonadjacent segments belonging to an evolving event; distinguish stable facts from facts formed on demand. | Reports gains on LoCoMo and LongMemEval-S across five LLMs; no direct AMI/streaming evidence. | Use an event/topic ID for updates across separated chunks; question-blind salience is uncertain, so retain the original full transcript at answer time. | Verified primary source |
| [LeanMem: Simple and Efficient Long-Term Memory for LLM Agents](https://arxiv.org/abs/2608.03463) | arXiv preprint | Treat stable profiles, changing events and source-grounded records differently; selectively update dynamic event memories. | Reports accuracy and construction-cost gains on LoCoMo/LongMemEval-S; independent meeting results remain untested. | Update only affected notes, keep source IDs for exact quantities and decisions, and measure construction cost separately from request cost. | Verified primary source |

## Design choices to test

1. Isolate duplication with a latest-old-snapshot reader control.
2. Replace the entire state using only the new chunk, recent reference speech and one earlier state.
3. Emit only edits, and preserve genuine revisions in a program-maintained change log.
4. Retain all available transcript history at answer time, under the same response prompt and token caps.
5. Freeze prompts on the six development questions before the additional-meeting comparison.

## Open questions
- Most reported token savings compare retrieved memory with full-history inputs; they do not directly establish lower native request thinking when the full transcript is retained.
- Stable speaker ownership, disfluent speech and unresolved AMI discussion require source checks beyond schema validity.
- A prompt-only incremental edit system may reduce copying but still merge distinct events or mistake intent for completion.
