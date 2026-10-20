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
    plain_names = {
        "call1": "What part did A play in the meeting?",
        "call2a": "Did A keep track of who said what?",
        "call2b": "Did A put different people’s ideas together?",
        "call2c": "Did A consider the whole group?",
        "call3a": "Were A’s contributions clear and useful?",
        "retry-call2a": "What the judge receives if the first scoring attempt fails",
    }
    prompt_dir = RESEARCH / "prompts"
    prompt_dir.mkdir(exist_ok=True)
    for key, description, pair in prompts:
        messages = pair.to_openai_messages()
        relative = f"research/multitalk-bench/prompts/{key}.json"
        (ROOT / relative).write_text(json.dumps(messages, indent=2, ensure_ascii=False) + "\n")
        prompt_records.append(dict(id=key, description=description, messages=messages))
        plain_name = plain_names.get(key, "Did A do the job of a " + key.removeprefix("call3b-") + " well?")
        panels.append(f'<details class="mtb-prompt" id="prompt-{key}"><summary>{e(plain_name)}</summary>'
                      f'<p class="meta">Source label: <code>{e(key)}</code> · {e(description)}</p>'
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
<section class="section" id="evaluation-protocol"><h2>What actually happens during evaluation?</h2>
<p class="section-intro">First, the speech model takes one person’s place in a recorded meeting. Afterwards, a separate AI called Gemma reads the written conversation and judges how well the model participated.</p>
<ol class="mtb-workflow"><li><strong>The speech model joins the recording.</strong> It hears the other people and produces its own replies. The other people’s speech comes from the original recording, so they keep following their original conversation.</li><li><strong>The evaluator writes out the conversation.</strong> It combines the model’s words with the other people’s words in time order. In this written version, <strong>A is the model</strong>, and B, C and so on are the recorded people.</li><li><strong>Gemma reads that written conversation six times.</strong> Each “call” is one request sent to Gemma, with a different set of questions. The first request asks what part A played in the meeting. The other five ask for ratings of different aspects of A’s behavior.</li></ol>
<p>All six calls read the same conversation and judge A. The first call identifies a meeting role; the sixth uses that role to choose its questions. The five scoring calls give ratings from 1 to 5 and short reasons for those ratings. These ratings are combined into the final score, with a separate adjustment for how far into the meeting A kept participating. <a href="#scoring">See how the score is calculated</a>.</p>
<div class="callout"><h3>The judge reads words</h3><p>Gemma is the judge model, <code>google/gemma-4-31B-it</code>. It receives written lines such as “A: We have 400 dollars left.” It is told to use A’s own lines as evidence for A’s performance. The judge does not receive audio or the times when people spoke, so these six calls cannot tell us whether the voice sounded good or whether the model stopped quickly when interrupted. {link('benchmark.py', 'How the written conversation is assembled', 338)}</p></div>
<div class="mtb-teaching-case" id="simple-meeting"><h3>A small meeting to keep in mind</h3><p>The group is choosing a product design. In the examples below, <strong>A is the model, B is Ben, and C is Chloe</strong>.</p><ul><li><strong>Ben:</strong> “We can spend 500 dollars.”</li><li><strong>Chloe:</strong> “We need to reserve 100 dollars for testing.”</li><li><strong>A:</strong> “That leaves 400 dollars for the design.”</li></ul><p>These are authored teaching examples. The stronger and weaker replies below illustrate what the judge is asked to look for; they are not measured model outputs or actual judge decisions. Some examples extend this little meeting to explain a particular question.</p></div>
<h3 id="six-calls-explained">The six calls, in everyday language</h3>
<div class="mtb-call-list">
<article class="mtb-call" id="explain-call1"><p class="meta">1 of 6 · Source name: Call 1</p><h4>What part did A play in the meeting?</h4><p>The judge first decides how A helped the group. Did A organize the discussion, put forward new ideas, build on other people’s ideas, or point out risks? The benchmark calls these roles <strong>Facilitator, Driver, Collaborator and Evaluator</strong>.</p><p><strong>Example:</strong> A says, “Ben, what is our budget? Chloe, what do we need to test? Then let’s agree on the next step.” That suggests a <strong>Facilitator</strong>: someone helping organize the meeting.</p><p>This call returns a role label and an explanation. It does not give the quality ratings used in the final score. A can act like a facilitator and still do that job poorly; the sixth call checks how well it did the job. <a href="#prompt-call1">Read the exact prompt</a>.</p></article>
<article class="mtb-call" id="explain-call2a"><p class="meta">2 of 6 · Source name: Call 2a · Questions M1 and M2</p><h4>Did A keep track of who said what?</h4><p>The judge checks whether A remembers each person’s statements and responds to their different concerns.</p><p><strong>Stronger reply:</strong> “Ben set a 500-dollar limit. Chloe needs 100 dollars for testing.” A keeps the two people’s information straight.</p><p><strong>Weaker reply:</strong> “Chloe set the 500-dollar limit.” A has mixed up who said it. Repeating “Good point” to everyone also gives little evidence that A understood their different needs. <a href="#prompt-call2a">Read the exact prompt</a>.</p></article>
<article class="mtb-call" id="explain-call2b"><p class="meta">3 of 6 · Source name: Call 2b · Questions M3 and M4</p><h4>Did A put different people’s ideas together?</h4><p>The judge checks whether A combines information from several people. It also checks whether A can work through disagreements involving three or more positions, when the meeting contains such a disagreement.</p><p><strong>Stronger reply:</strong> “With Ben’s 500-dollar limit and Chloe’s 100-dollar testing reserve, we have 400 dollars for the design.” This uses both people’s information.</p><p><strong>Weaker reply:</strong> “We can spend all 500 dollars on the design.” A has lost Chloe’s constraint. Our small budget example illustrates combining information; it contains no three-way disagreement to assess. <a href="#prompt-call2b">Read the exact prompt</a>.</p></article>
<article class="mtb-call" id="explain-call2c"><p class="meta">4 of 6 · Source name: Call 2c · Questions M5 and M6</p><h4>Did A consider the whole group?</h4><p>The judge checks whether A considers everyone’s needs and handles competing requests sensibly. A should explain conflicts instead of simply following whoever spoke last or pushed hardest.</p><p><strong>Example extension:</strong> Ben now asks to spend all 500 dollars on the design, while Chloe still needs testing money.</p><p><strong>Stronger reply:</strong> “Spending all 500 would remove Chloe’s testing budget. Can we keep 100 for testing and use 400 for the design?”</p><p><strong>Weaker reply:</strong> “Sure, Ben, spend all 500.” That ignores the unresolved conflict with Chloe’s request. <a href="#prompt-call2c">Read the exact prompt</a>.</p></article>
<article class="mtb-call" id="explain-call3a"><p class="meta">5 of 6 · Source name: Call 3a · Questions G1–G4</p><h4>Were A’s contributions clear and useful?</h4><p>The judge asks four broad questions: Could people understand A? Did A answer what was actually said? Did A stay with the current topic? Did A help the group reach a decision or next step?</p><p><strong>Stronger reply:</strong> “Let’s use a design costing at most 400 dollars and keep 100 for testing. Ben, can you finish the durability test by Friday?”</p><p><strong>Weaker reply:</strong> “Great ideas, everyone. We should think about this more.” It sounds agreeable but gives the group little to act on. <a href="#prompt-call3a">Read the exact prompt</a>.</p></article>
<article class="mtb-call" id="explain-call3b"><p class="meta">6 of 6 · Source name: Call 3b</p><h4>Did A do its particular meeting job well?</h4><p>This call uses the role chosen in the first call. If A acted as a facilitator, the judge asks whether it moved the agenda along, brought people into the discussion, helped reach decisions, summarized the outcome and treated people fairly.</p><p><strong>Stronger facilitator reply:</strong> “Ben, can you run the test by Friday? Chloe, does that cover your concern? Then our decision is a 400-dollar design plus 100 for testing.”</p><p><strong>Weaker facilitator behavior:</strong> A says “Let’s move on” without resolving the budget or asking Chloe about testing. It is organizing the discussion, but doing so poorly.</p><p>If the first call instead identified A as a Driver, this call would ask how well it proposed and supported new ideas. A Collaborator is checked on building on others’ ideas; an Evaluator on useful criticism and risks. <a href="#prompt-call3b-facilitator">Read the exact role prompts</a>.</p></article>
</div>
<p><strong>How the pieces fit:</strong> Call 1 chooses A’s role. Calls 2–4 grade its ability to work with several people. Call 5 grades basic usefulness. Call 6 grades how well it performed its role. The final score combines the multi-party, basic-usefulness and role scores equally, then applies the participation adjustment described below.</p>
<details id="call-label-reference"><summary>Match the plain-language questions to the source code</summary><p>The source labels <code>2a</code>, <code>2b</code> and <code>2c</code> name three requests about working with several people. <code>3a</code> asks about general usefulness; <code>3b</code> asks about the identified role. Table 3 maps those names to the explanations above.</p><div class="table-wrap"><table id="mtb-judge-calls"><caption>Table 3. Plain-language questions and the corresponding source labels.</caption><thead><tr><th scope="col">Request to Gemma</th><th scope="col">Source label</th><th scope="col">What it returns</th></tr></thead><tbody>
<tr><th scope="row">1. What part did A play?</th><td>Call 1</td><td>A role label, supporting evidence and explanation</td></tr><tr><th scope="row">2. Who said what?</th><td>Call 2a · M1–M2</td><td>Two ratings</td></tr><tr><th scope="row">3. Put people’s ideas together?</th><td>Call 2b · M3–M4</td><td>Two ratings</td></tr><tr><th scope="row">4. Consider the whole group?</th><td>Call 2c · M5–M6</td><td>Two ratings</td></tr><tr><th scope="row">5. Clear and useful?</th><td>Call 3a · G1–G4</td><td>Four ratings</td></tr><tr><th scope="row">6. Do its meeting job well?</th><td>Call 3b · chosen role</td><td>Four ratings; five for a facilitator</td></tr>
</tbody></table></div><p>Each scoring request asks several questions, so one meeting receives 14 individual ratings, or 15 when A is identified as a facilitator. There are 27 possible judged questions across all roles, plus the separate mechanical participation measure P1. These are judgments using written guidelines, rather than checks against a list of exact correct answers. {link('prompt_builder.py', 'Complete definitions', 625)}</p><p>The paper describes calls that could be independent after role identification. The pinned implementation sends the six requests in sequence. {link('benchmark.py', 'Execution loop', 656)}</p></details>
<details id="transcript-technical-details"><summary>Technical details: how the model’s output becomes judge input</summary><p>A detailed persona prompt or a minimal alternative tells the speech model how to participate. The judge receives the speaker list, target label A and the written conversation. The adapters save the model’s words with timestamps in an <code>alignments</code> array. The evaluator removes padding tokens, joins text into utterances, and starts a new utterance when a gap exceeds 1.2 seconds. It combines those utterances with the other people’s reference sentences and sorts everything by start time. The written lines sent to the judge omit the timestamps. {link('README.md', 'Adapter and judge setup')} · {link('benchmark.py', 'Transcript construction', 239)}</p></details>
</section>
<section class="section" id="judge-prompts"><h2>Read the full instructions sent to the judge</h2>
<p class="section-intro">The explanations above summarize the questions in everyday language. Below, each expandable panel shows the exact instructions used by the released evaluator, filled in with a short authored meeting. “System message” contains the grading instructions; “user message” contains the meeting and the person to judge.</p>
<p>The full examples extend the budget conversation above: B is Ben, C is Chloe, and A is the model. A combines the budget and testing information, asks the others for input, and records an owner and deadline. The meeting is authored for explanation; it is not a benchmark sample or a model result, and no judge has rated it. The source templates come from unchanged public commit <code>{COMMIT[:12]}</code>.</p>
<details id="illustrative-transcript"><summary>Read the authored transcript used in every prompt example</summary><pre><code>{e(TRANSCRIPT)}</code></pre></details>
<p>For each question, Gemma is asked to give a rating, a short reason, and short quotes that support its judgment. Table 4 explains the rating scale. A higher rating means better meeting behavior. The general and role prompts focus on how A participated, rather than checking expert knowledge of the topic.</p><details id="judge-output-format"><summary>Technical details: the required answer format</summary><p>The answer must be JSON with <code>score</code>, <code>positive_evidence</code>, <code>negative_evidence</code> and <code>reasoning</code> for each question. Each English evidence list allows one quote of at most 12 words; each reason allows 40 words. The Chinese limits are 20 characters per quote and 40 characters per reason. {link('prompt_builder.py', 'Output format and shared rating scale', 180)}</p></details>
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
