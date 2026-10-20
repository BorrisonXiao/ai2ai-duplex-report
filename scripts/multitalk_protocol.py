"""Render the evaluation protocol and prompts from pinned public source."""
from __future__ import annotations

import ast
import hashlib
from html import escape as e
import importlib.util
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
RESEARCH = ROOT / "research/multitalk-bench"
SOURCE = RESEARCH / "protocol-source"
COMMIT = "3979639b5a2b89fe2a85c323e286928cbfea5acb"
UPSTREAM = f"https://github.com/multitalk-ai/MultiTalk/blob/{COMMIT}/MultiTalkBench/"

TRANSCRIPT = """A: First, let's agree on the budget. B, what is the limit?
B: We can spend 500 dollars.
C: We also need to reserve 100 dollars for testing.
A: That leaves 400 dollars for the design. Let's move to materials. C, what do you recommend?
C: Recycled plastic fits that budget.
B: I agree, provided we test durability.
A: Both of you support recycled plastic with a durability check. Let's move to testing. B, can you own that?
B: Yes, I can finish the test on Friday.
A: Then let's confirm the decision: recycled plastic, a 400-dollar design budget, and B tests durability by Friday. C, any concern before we close?
C: No, that covers my concern.
A: Agreed. We have the decision and an owner. That closes the meeting."""


def load_module():
    manifest = json.loads((RESEARCH / "protocol-sources.json").read_text())
    assert manifest["upstream_commit"] == COMMIT
    for item in manifest["files"]:
        assert hashlib.sha256((SOURCE / item["path"]).read_bytes()).hexdigest() == item["sha256"]
    path = SOURCE / "MultiTalkBench/prompt_builder.py"
    spec = importlib.util.spec_from_file_location("multitalk_pinned_prompts", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def benchmark_function(name):
    """Load only the two reviewed pure prompt functions, without model imports."""
    text = (SOURCE / "MultiTalkBench/benchmark.py").read_text()
    tree = ast.parse(text)
    node = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == name)
    return ast.get_source_segment(text, node)


def link(file, label, line=None):
    return f'<a href="{UPSTREAM}{file}{"#L" + str(line) if line else ""}">{e(label)}</a>'


def equation(tex):
    return '<div class="equation">\\[' + e(tex) + '\\]</div>'


def render_protocol():
    module = load_module()
    # These functions only format prompts; no client, model or judge is loaded.
    namespace = {"PromptPair": module.PromptPair, "Language": module.Language,
                 "Sequence": list}
    exec(compile("from __future__ import annotations\n" + benchmark_function("add_target_alias_focus")
                 + "\n" + benchmark_function("compact_score_prompt"), "pinned-prompt-functions", "exec"), namespace)
    inp = module.PipelineInput(transcript=TRANSCRIPT, target_speaker="A", all_speakers=["A", "B", "C"],
                               language=module.Language.EN)
    builder = module.PromptBuilder()
    prompts = []
    for call in ["call1", "call2a", "call2b", "call2c", "call3a"]:
        pair = getattr(builder, "build_" + call)(inp)
        pair = namespace["add_target_alias_focus"](pair, language=inp.language, target_alias="A")
        prompts.append((call, pair.description, pair))
    for role in ["Facilitator", "Driver", "Collaborator", "Evaluator"]:
        inp.primary_role = role
        pair = namespace["add_target_alias_focus"](builder.build_call3b(inp), language=inp.language, target_alias="A")
        prompts.append(("call3b-" + role.lower(), pair.description, pair))
    retry = namespace["compact_score_prompt"](prompts[1][2], ["M1", "M2"])
    prompts.append(("retry-call2a", "Compact retry for M1/M2 after a failed first attempt", retry))
    prompt_records = []
    panels = []
    prompt_dir = RESEARCH / "prompts"
    prompt_dir.mkdir(exist_ok=True)
    for key, description, pair in prompts:
        messages = pair.to_openai_messages()
        relative = f"research/multitalk-bench/prompts/{key}.json"
        (ROOT / relative).write_text(json.dumps(messages, indent=2, ensure_ascii=False) + "\n")
        prompt_records.append(dict(id=key, description=description, messages=messages))
        panels.append(f'<details class="mtb-prompt" id="prompt-{key}"><summary>{e(key)} · {e(description)}</summary>'
                      f'<p><a href="{relative}">Download these exact system/user messages (JSON)</a></p>'
                      f'<h4>System message</h4><pre><code>{e(pair.system)}</code></pre>'
                      f'<h4>User message</h4><pre><code>{e(pair.user)}</code></pre></details>')
    (RESEARCH / "prompt-examples.json").write_text(json.dumps(dict(
        upstream_commit=COMMIT, kind="illustrative_prompt_rendering_not_model_evaluation",
        transcript=TRANSCRIPT, role_branch_note="All four Call 3b roles are shown as alternatives; no role was inferred by a judge.",
        prompts=prompt_records), indent=2, ensure_ascii=False) + "\n")

    coefficient_equation = equation(r'c=\max\!\left(0,\,1-\left|r_{\mathrm{model}}-r_{\mathrm{human}}\right|\right)')
    score_equation = equation(r'\text{Sample score}=\frac{G+M+R}{3}\,c')
    return f"""
<section class="section" id="evaluation-protocol"><h2>How a sample is evaluated</h2>
<p class="section-intro">The model takes one participant’s place in a recorded conversation. Its contributions are judged as part of a reconstructed group transcript by <code>google/gemma-4-31B-it</code>. A separate mechanical measure compares the span of its participation with the original human participant’s span.</p>
<p>The other participants follow their original recordings; they do not adapt to the model’s new statements. The detailed persona prompt or alternative minimal prompt conditions model inference. Those persona files are distinct from the judge prompts below: the judge receives the speaker list, target alias and reconstructed transcript. The released adapters save timestamped text in an <code>alignments</code> array for evaluation. {link('README.md', 'Adapter and judge setup')} · {link('benchmark.py', 'Transcript construction', 239)}</p>
<ol class="mtb-workflow"><li><strong>Run the target participant.</strong> Replay the peer audio through the model adapter and save the model’s timestamped output text.</li><li><strong>Build the judging transcript.</strong> Remove padding tokens, join model tokens into utterances, and split when the gap exceeds 1.2 seconds. Interleave these with the peers’ reference sentence alignments in start-time order.</li><li><strong>Assign aliases.</strong> The target becomes <code>A:</code>; peers become <code>B:</code>, <code>C:</code>, and so on. Every judge call includes a reminder to cite only the target’s lines.</li><li><strong>Judge six modules.</strong> Identify the target’s observed dominant role, then obtain general, multi-party and role-specific ratings. This role comes from the reconstructed transcript, rather than a fixed gold role label.</li><li><strong>Aggregate ratings.</strong> Normalize the ratings, average within three groups, and apply the released code’s participation multiplier.</li></ol>
<div class="callout"><h3>What the judge can see</h3><p>The judge reads text with speaker aliases. Although timestamps determine utterance order and the participation metric, they are omitted from the judging transcript itself. The judge does not hear waveform quality, pauses or overlap. Its assessments of conversational rhythm and competing inputs are therefore based on the text sequence. {link('benchmark.py', 'Exact transcript formatting', 338)}</p></div>
<div class="table-wrap"><table id="mtb-judge-calls"><caption>Table 3. The six intended judge calls for each sample.</caption><thead><tr><th scope="col">Call</th><th scope="col">Tests</th><th scope="col">Output / example evidence sought</th></tr></thead><tbody>
<tr><th scope="row"><a href="#prompt-call1">1 · Role identification</a></th><td>Facilitator, Driver, Collaborator or Evaluator</td><td>Primary/secondary role, confidence, turn count, evidence and reasoning. For example, does the target allocate turns and close decisions?</td></tr>
<tr><th scope="row"><a href="#prompt-call2a">2a · M1–M2</a></th><td>Speaker tracking; differentiated responses</td><td>Does it attribute an earlier statement correctly and respond to different people’s distinct concerns?</td></tr>
<tr><th scope="row"><a href="#prompt-call2b">2b · M3–M4</a></th><td>Cross-speaker information integration; disagreement handling</td><td>Does it combine facts from several speakers and address three-way conflicting positions?</td></tr>
<tr><th scope="row"><a href="#prompt-call2c">2c · M5–M6</a></th><td>Group awareness; input prioritization</td><td>Does it consider everyone present and explain how it resolves contradictory inputs?</td></tr>
<tr><th scope="row"><a href="#prompt-call3a">3a · G1–G4</a></th><td>Clarity/actionability; response relevance; agenda fit; progress</td><td>Does it provide concrete, responsive contributions that help the meeting advance?</td></tr>
<tr><th scope="row"><a href="#prompt-call3b-facilitator">3b · Assigned role</a></th><td>Four or five dimensions for the role identified by Call 1</td><td>For a facilitator: agenda momentum, activating participation, converging on decisions, closure and fairness.</td></tr>
</tbody></table></div>
<p>Table 3 describes rubric judgments, including speaker tracking and addressee-sensitive behavior; these are not separate exact-match addressee labels or timed turn-boundary accuracy tests. A sample receives 14 ratings, or 15 for a facilitator. Across all four role branches there are 27 judged dimensions, plus mechanical P1. The paper describes independent calls after role identification; the pinned <code>benchmark.py</code> executes its call list sequentially. {link('prompt_builder.py', 'Complete definitions and English templates', 625)} · {link('benchmark.py', 'Execution loop', 656)}</p>
</section>
<section class="section" id="judge-prompts"><h2>Actual prompts, with an illustrative meeting</h2>
<p class="section-intro">Expand a module below to read its complete system and user messages. They are rendered from the unchanged public prompt builder at commit <code>{COMMIT[:12]}</code>, with the same target-only reminder used by the benchmark. The short meeting below is authored for explanation; it is not a benchmark sample, a model output, or a scored result.</p>
<p>In this example, B supplies the 500-dollar limit and C reserves 100 dollars for testing; A combines those inputs into a 400-dollar design budget. This gives the integration module something concrete to assess. A also asks both peers for input and records an owner and deadline, which the facilitator module can examine. There is no three-way conflict, so the example does not demonstrate disagreement-handling ability. No judge has rated this example.</p>
<details id="illustrative-transcript"><summary>Read the authored transcript used in every prompt example</summary><pre><code>{e(TRANSCRIPT)}</code></pre></details>
<p>Each scoring system message supplies the shared 1–5 rubric and dimension-specific questions. Its required JSON includes <code>score</code>, <code>positive_evidence</code>, <code>negative_evidence</code> and <code>reasoning</code> for each dimension. English evidence snippets are limited to 12 words and one item per evidence array; reasoning is limited to 40 words. The Chinese templates use 20-character evidence and 40-character reasoning limits. The general and role prompts instruct the judge to assess meeting behavior, rather than domain knowledge correctness. {link('prompt_builder.py', 'Output schema and shared rubric', 180)}</p>
<div class="table-wrap"><table id="mtb-rating-rubric"><caption>Table 4. Shared ordinal rubric; labels are summarized from the source.</caption><thead><tr><th scope="col">Rating</th><th scope="col">Interpretation</th><th scope="col">Normalized value</th></tr></thead><tbody>
<tr><th scope="row">5</th><td>Outstanding; clear positive evidence and no notable flaws</td><td>100</td></tr><tr><th scope="row">4</th><td>Good; minor imperfections</td><td>75</td></tr><tr><th scope="row">3</th><td>Adequate; baseline behavior</td><td>50</td></tr><tr><th scope="row">2</th><td>Noticeable problems affecting meeting outcomes</td><td>25</td></tr><tr><th scope="row">1</th><td>Little evidence or clear negative behavior</td><td>0</td></tr><tr><th scope="row">N/A</th><td>Fewer than five valid speaking turns; insufficient material to judge</td><td>0; included at the minimum, not dropped</td></tr>
</tbody></table></div>
<p>The four Call 3b examples show alternative branches. In a real evaluation, only the branch selected by Call 1 is used. We set the role explicitly here to expose each template; this is not a judge’s inferred role. {link('prompt_builder.py', 'Role-specific definitions', 917)}</p>
{''.join(panels[:9])}
<details id="judge-retries"><summary>Judge defaults and the retry prompt</summary><p>The client defaults to temperature 1.0, top-p 0.95 and top-k 64. Each module’s output cap is 8,192 tokens in the pinned benchmark. These are judge settings, not settings for the speech model under test. Six logical calls can involve additional requests: the default permits two retries per call. {link('judge/gemma4.py', 'Request settings', 80)} · {link('benchmark.py', 'Per-call caps', 33)}</p><p><strong>Retry caveat:</strong> after a failed scoring attempt, the code replaces the normal transcript/rubric messages with a compact JSON request that contains neither the transcript nor the dimension definitions. It explicitly instructs the judge not to inspect or quote the transcript, and suggests score 1 when uncertain. This is not equivalent to repeating the original evidence-based judgment; inspect each result’s <code>attempts</code> and <code>retry_mode</code> before trusting a score. Role-identification retries retain their original prompt. The exact M1/M2 retry messages are shown below. {link('benchmark.py', 'Retry construction and selection', 480)}</p>{panels[9]}</details>
<p><a href="research/multitalk-bench/prompt-examples.json">Download all ten examples and their provenance</a>. English messages are displayed here; both language templates remain available in the <a href="research/multitalk-bench/protocol-source/MultiTalkBench/prompt_builder.py">unchanged source snapshot</a>.</p>
</section>
<section class="section" id="scoring"><h2>How the released code computes scores</h2>
<p>Each judged rating is mapped to 0–100 as shown in Table 4. General score G averages four dimensions; multi-party score M averages six; role score R averages the four or five dimensions of the selected role. The three groups receive equal weight, so the larger multi-party group does not automatically dominate. {link('prompt_builder.py', 'ScoreCalculator', 1185)}</p>
<p>Participation is computed separately. For either the model or the human reference, r is the time between that target’s first utterance start and last utterance end, divided by the corresponding meeting span. A target with no utterances receives zero. This measures the span of presence, rather than total voiced duration or the fraction of turns spoken. The coefficient c compares model and human spans:</p>
{coefficient_equation}
<p>The released implementation multiplies the group average by c. The dataset score averages these per-sample final scores; it does not multiply a dataset-wide mean participation coefficient by independently averaged groups.</p>
{score_equation}
<p><strong>Worked arithmetic example, not a measured result:</strong> suppose normalized G, M and R are 75, 50 and 25. Their mean is 50. If the model’s participation span ratio is 0.8 and the human’s is 0.9, c is 0.9, so the sample score is 45. P1 is reported separately on a 0–100 scale as 100 times c; the raw result stores it on the 1–5 scale as 1 plus 4 times c. {link('benchmark.py', 'Participation and stored P1', 684)}</p>
<div class="callout amber" id="paper-code-discrepancy"><h3>Paper/code discrepancy</h3><p>Appendix E.5 displays the final score as the equally weighted average of the three judge groups, without a participation multiplier. The pinned released code applies c to every group and to the final score. We document the implementation above; this source review does not establish which exact revision produced the paper’s result table. <a href="https://arxiv.org/html/2609.36903#A5.SS5">Paper Appendix E.5</a> · {link('prompt_builder.py', 'Executed scoring expression', 1314)}</p></div>
<div class="callout"><h3>Limits of the participation metric</h3><p>Two brief utterances near the beginning and end can produce a span ratio close to one, just as continuous talking can. The metric therefore does not establish an appropriate speech rate, balanced airtime, correct entry points or interruption recovery. Those behaviors would need separate measurements.</p></div>
</section>
<section class="section" id="evaluation-limits"><h2>What an evaluation result would establish</h2>
<p>The scores describe transcript-level meeting behavior under replay of fixed human peers. Those peers cannot respond to a model’s novel proposal, so our interpretation is that this protocol cannot alone establish success in a fully reactive group conversation. The paper explicitly excludes direct latency and interruption-timing measurement. It also provides no dedicated tool-execution, backchannel-timing or acoustic-quality score. <a href="https://arxiv.org/html/2609.36903#S2.SS2">Paper §2.2</a></p>
<p>Long-range tracking and addressee-sensitive behavior are assessed through the rubric questions, not through an additional question set with exact-match gold answers in this scorer. English and Chinese have corresponding templates; bilingual coverage does not by itself establish code-switching ability. The source recordings and aligned utterances below illustrate the data, not evaluated model behavior.</p>
<details id="protocol-provenance"><summary>Source pin, attribution and reproducibility</summary><p>This review pins public upstream commit <code>{COMMIT}</code>. Six unchanged files, including the Apache-2.0 license, are archived under <code>research/multitalk-bench/protocol-source/</code>; the <a href="research/multitalk-bench/protocol-sources.json">source manifest</a> records URLs, byte counts and SHA-256 values. The code/templates retain their <a href="research/multitalk-bench/protocol-source/LICENSE">Apache-2.0 license</a>; the audio remains separately attributed under CC BY-SA 4.0.</p><p>Rebuild the page and prompt examples with <code>python scripts/build_multitalk_bench.py</code> from the site checkout. Prompt rendering is offline and uses 0 GPUs. No speech inference or Gemma judge requests were run for this documentation update. The short transcript and worked score are authored illustrations; no local benchmark score is claimed.</p></details>
</section>
"""
