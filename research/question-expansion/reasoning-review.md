# Research review: questions that need connected evidence

Date: 2026-10-26. Eight primary papers. Research and report analysis only; no new questions or inference.

## Assessment

All 15 retained information needs can be answered from one local passage or short exchange. Several transcript chunks or a long time gap do not make them multi-hop.

The target is a short, believable spoken request whose answer combines separate evidence. Referring to someone by a task or earlier action can introduce an identity step, but only when that step actually matters. The video paper matching the user’s description has not been established; LongVideoBench is a close documented example.

## Papers

### Compositional Questions Do Not Necessitate Multi-hop Reasoning

Sewon Min, Eric Wallace, Sameer Singh, Matt Gardner, Hannaneh Hajishirzi, Luke Zettlemoyer (2019), ACL. [Primary source](https://aclanthology.org/P19-1416/). Verified against the downloaded paper.

Problem: A question can appear compositional while one paragraph already supplies its answer.

Method: Tests HotpotQA using a model that reads one paragraph and a human study with supporting paragraphs withheld.

Reported result: Single-paragraph BERT reaches 67 F1; humans answer over 80% in the reported incomplete-evidence setting.

Application: Test whether each proposed evidence step is necessary, rather than counting citations or descriptive phrases.

Limit: A QA diagnostic rather than a question generator; its numeric results do not predict performance on meeting audio.

### Reinforced Multi-task Approach for Multi-hop Question Generation

Deepak Gupta, Hardik Chauhan, Ravi Tej Akella, Asif Ekbal, Pushpak Bhattacharyya (2020), COLING. [Primary source](https://aclanthology.org/2020.coling-main.249/). Verified against the downloaded paper.

Problem: Question generators can ignore some of the facts supplied to them.

Method: Jointly predicts supporting facts and generates the question, with a reward for using the supporting information.

Reported result: Reports improvements in automatic scores and human judgments of question quality and coverage.

Application: Select and check the required facts before polishing a question’s spoken wording.

Limit: Using more facts is not sufficient if one fact or another passage still gives away the answer.

### Multi-hop Question Generation with Graph Convolutional Network

Dan Su, Yan Xu, Wenliang Dai, Ziwei Ji, Tiezheng Yu, Pascale Fung (2020), Findings of EMNLP. [Primary source](https://aclanthology.org/2020.findings-emnlp.416/). Verified against the downloaded paper.

Problem: Relevant evidence is scattered across paragraphs.

Method: MulQG uses an entity graph and repeated encoding to connect evidence before question generation.

Reported result: Reports better HotpotQA generation metrics and a human evaluation of completeness and multi-hop content.

Application: Represent a connection such as task → person → earlier commitment explicitly before writing the question.

Limit: Its learned graph architecture does not need to be reproduced for a small prompt-based pilot; graph edges also need source verification.

### CQG: A Simple and Effective Controlled Generation Framework for Multi-hop Question Generation

Zichu Fei, Qi Zhang, Tao Gui, Di Liang, Sirui Wang, Wei Wu, Xuanjing Huang (2022), ACL. [Primary source](https://aclanthology.org/2022.acl-long.475/). Verified against the downloaded paper.

Problem: A generator can receive several documents but still produce a shallow question.

Method: Extracts important entities along a reasoning chain and controls generation so relevant entities appear in the question.

Reported result: Reports a five-BLEU-point improvement on HotpotQA over its stated comparison.

Application: Plan a connected evidence chain and check that the final question still needs that connection.

Limit: We should not force every entity name into speech: that can sound unnatural or reveal the intermediate answer. This is our adaptation concern, not a reported failure of CQG.

### MuSiQue: Multihop Questions via Single-hop Question Composition

Harsh Trivedi, Niranjan Balasubramanian, Tushar Khot, Ashish Sabharwal (2022), TACL. [Primary source](https://aclanthology.org/2022.tacl-1.31/). Verified against the downloaded paper.

Problem: Existing multi-hop questions often allow an answer without connecting the intended steps.

Method: Composes simple questions only when a later step depends on the answer to an earlier one; filters shortcuts and adds unanswerable variants.

Reported result: Creates about 25,000 questions requiring two to four steps, with tests for disconnected reasoning.

Application: The strongest construction principle for this project: each link must be necessary, including identity resolution.

Limit: The source is Wikipedia QA. Meeting timing, speaker motivation and ordinary spoken wording require additional review.

### Explainable Multi-hop Question Generation: An End-to-End Approach without Intermediate Question Labeling

Seonjeong Hwang, Yunsu Kim, Gary Geunbae Lee (2024), LREC-COLING. [Primary source](https://aclanthology.org/2024.lrec-main.599/). Verified against the downloaded paper.

Problem: Complex generated questions are hard to explain, and intermediate rewriting labels are costly.

Method: E2EQR successively rewrites a question using additional documents, transferring decoder state between steps and training without intermediate question labels.

Reported result: Evaluates three- and four-step generation and the usefulness of generated questions for QA training.

Application: Start from a useful short reminder, then add one necessary dependency while retaining a natural sentence.

Limit: A rewrite can add words without adding a necessary reasoning step. Every source document in our adaptation must already be available at the question time.

### LongVideoBench: A Benchmark for Long-context Interleaved Video-Language Understanding

Haoning Wu, Dongxu Li, Bei Chen, Junnan Li (2024), NeurIPS Datasets and Benchmarks. [Primary source](https://proceedings.neurips.cc/paper_files/paper/2024/hash/329ad516cf7a6ac306f29882e9c77558-Abstract-Datasets_and_Benchmarks_Track.html). Verified against the downloaded paper.

Problem: Video questions can be answered from one frame instead of understanding a longer context.

Method: Human annotators write questions that first refer to a person, event, scene or subtitle, then ask about the referred content.

Reported result: 6,678 human-annotated multiple-choice questions over 3,763 videos. Its annotation guide includes clothing-based descriptions and earlier/later appearances.

Application: A close match to the user’s remembered style. For audio, an earlier task or proposal can identify the speaker before retrieving what that person said.

Limit: The remembered paper is not identified conclusively. LongVideoBench includes perception tasks as well as relations; indirect descriptions alone do not guarantee multiple necessary evidence steps.

### Multi-Hop Question Generation via Dual-Perspective Keyword Guidance

Maodong Li, Longyin Zhang, Fang Kong (2025), Findings of ACL. [Primary source](https://aclanthology.org/2025.findings-acl.526/). Verified against the downloaded paper.

Problem: Keywords expressing the questioner’s intent play a different role from words locating evidence.

Method: Distinguishes question keywords from document keywords and uses both to guide generation.

Reported result: Reports improvements on HotpotQA generation experiments.

Application: Keep the participant’s immediate need separate from the evidence used to answer it.

Limit: Forced keywords should not replace a review of whether a real participant would ask the resulting question.

## Recommended direction for discussion

Find the person, then retrieve their commitment: An earlier task assignment identifies a participant; a separate turn supplies that participant’s commitment or requested detail. Use a task description only when it is a believable way for this requester to refer to that participant.

Apply a later change to an earlier plan: An earlier plan supplies one fact; a later constraint or correction changes what remains possible. Ask about the practical consequence that matters at the current point, rather than requesting a chronology for its own sake.

Resolve a reference in the call, then check a document: Earlier speech identifies the company metric or store group; an available document supplies the comparison or exact value. Use this as a later tool experiment, with a clear reason to open the document.

## Acceptance criteria

- The answer requires two connected facts in separate passages; supplying unrelated facts is not a chain.
- Every necessary fact is available before the proposed question time.
- Search the entire available transcript for a recap that already combines the facts. If one passage is sufficient, classify the item as recall.
- Withhold each necessary fact, accounting for repeated mentions. The remaining evidence should not justify the complete answer.
- Use a plausible alternative person, proposal or metric to check that the first step genuinely selects the second.
- Review wording, requester motivation, ambiguity and whether the question reveals an intermediate answer.
- Use source-based review and independent human checks; the same 30B model’s agreement cannot establish validity.

For a future pilot, cover early, middle and late points where real dependencies exist, and report elapsed time separately from evidence age. Do not create an early question before its needed evidence has arrived.

No generation, training, TTS or inference has been started for this proposal.
