#!/usr/bin/env python3
"""Offline generation of literature tables, verified BibTeX and reusable digests."""
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "research"))
import focused_review as data

def tex(value):
    special = {"\\": r"\textbackslash{}", "&": r"\&", "%": r"\%", "$": r"\$", "#": r"\#", "_": r"\_", "{": r"\{", "}": r"\}", "~": r"\textasciitilde{}", "^": r"\textasciicircum{}", "τ": r"$\tau$", "×": r"$\times$"}
    return "".join(special.get(char, char) for char in str(value))

def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value.rstrip() + "\n", encoding="utf-8")

def bibliography(audit):
    indexed = {source["url"].rsplit("/", 1)[-1]: source["metadata"] for source in audit["sources"] if "metadata" in source and source["status"] == "reachable"}
    entries, papers = [], []
    broad = {p["id"]: p for p in json.loads((ROOT.parent / "research" / "literature.json").read_text())["papers"]}
    additions = {
        "syncllm": {"problem": "Variable text/unit sequence length must still track a real acoustic clock.", "method": "Periodic speaker/chunk boundaries plus deduplicated semantic units and speculative user prediction/replacement.", "results": "Authors demonstrate synchronous full-duplex generation and evaluate processing/network delay; no independent reproduction.", "relevance": "Direct temporal-interface prior work, predating modern text-backbone duplex releases.", "limitations": "Clock alignment does not itself establish correction-sensitive reasoning; dedicated released checkpoint not located."},
        "flair": {"problem": "Listening-time silence/padding does not exploit ongoing latent reasoning.", "method": "Soft vocabulary-weighted latent embeddings; ELBO/SFT from a full-context expert into a causal inference model.", "results": "Authors evaluate reasoning and interaction improvements over their pretraining-only baseline; no independent reproduction or unified leaderboard in this review.", "relevance": "Direct alternative to explicit prefix chain-of-thought and a close prior to think-while-listening claims.", "limitations": "Complete mixture and dedicated artifacts not located; teacher access to future context is training supervision, not permitted evaluation evidence."},
        "duplexsla": {"problem": "Speaking, listening and structured actions need a shared temporal protocol.", "method": "160 ms shared clock; two listening features, one text/four audio outputs, bounded action tokens and queued action spillover.", "results": "Authors evaluate integrated duplex/tool behavior on a reported 2,100-case benchmark; no independent reproduction.", "relevance": "Very close prior work for explicit action/speech/listening synchronization.", "limitations": "Official repository marks inference, checkpoints and benchmark as forthcoming at cutoff."},
        "synchrony": {"problem": "Determine whether speaker/listener hidden states synchronize and encode turn-taking signals.", "method": "Moshi--Moshi appointment conversations; lagged CKA and causal end-of-interpausal-unit probes under noise/activity-bias variation.", "results": "Authors report near-zero-lag coupling that degrades with noise and useful timing probes; no causal correctness guarantee.", "relevance": "Representation-level synchronization evidence complementary to runtime clocks.", "limitations": "Restricted conversational task; artifact package not located; probe quality is not revision correctness."},
        "echochain": {"problem": "A model can acknowledge an interruption while its subsequent task-state reasoning remains wrong.", "method": "Speech-onset-relative controlled interruptions, paired half-duplex control, and conversation-specific human-audited rubrics.", "results": "Authors report no evaluated model above 50% conversation pass rate across 200 interrupted conversations; result not reproduced here.", "relevance": "Direct benchmark predecessor for correction-sensitive ongoing reasoning.", "limitations": "Four closed models; no backchannel/side-speech coverage or detailed acoustic timing; separate runnable release not located."},
        "mindpaced": {"problem": "Full pre-response reasoning delays speech; interleaving may disrupt reasoning continuity.", "method": "Concurrent formulation/articulation with shared Step-Audio 2 parameters; incremental thought segments and think-incomplete SFT.", "results": "Authors report improved latency/quality trade-offs; their near-zero-latency configuration still depends on synthesis buffering.", "relevance": "Established think-while-speaking predecessor, underlying Step-Audio R1.1 and referenced by StepAudio 3.", "limitations": "Concurrent formulation does not establish correction-safe audible commitment; performance depends on the tested backbone/tasks."},
    }
    for key, aid in data.PAPERS.items():
        meta = indexed[aid]
        authors = meta["citation_author"]
        displayed = authors if len(authors) <= 3 else authors[:3] + ["others"]
        title = meta["citation_title"][0].replace(r"$\tau$", "τ")
        date = meta["citation_date"][0]
        year = date[:4]
        url = "https://arxiv.org/abs/" + aid
        venue = data.VENUES.get(key)
        kind = "inproceedings" if venue else "article"
        author_text = "{" + tex(displayed[0]) + "}" if key == "venus" else " and ".join(tex(author) for author in displayed)
        fields = {"title": "{" + tex(title) + "}", "author": author_text, "year": venue[1] if venue else year, "url": venue[2] if venue else url}
        if venue:
            fields["booktitle"] = venue[0]
        else:
            fields["journal"] = "arXiv preprint arXiv:" + aid
        entries.append("@" + kind + "{" + key + ",\n" + ",\n".join("  " + field + " = {" + value + "}" for field, value in fields.items()) + "\n}")
        analysis = additions.get(key, {field: broad.get(aid, {}).get(field) for field in ("problem", "method", "results", "relevance", "limitations")})
        rows = [row for category in data.CATEGORIES for row in category["rows"] if row["cite"] == key]
        analysis["focused_notes"] = [{"resource": row["name"], "comparison": row["cells"], "artifacts": row["links"]} for row in rows]
        if key == "adapt":
            analysis["method"] = "Adaptive windows and bounded text lead; indexed backend launch/cancel; cancelled/stale results suppressed before injection."
            analysis["relevance"] = "Cancellation alone is already implemented; joint speaker-owned result/output commitment must be differentiated."
        papers.append({"key": key, "id": aid, "title": title, "authors": authors, "date": date.replace("/", "-"), "venue": venue[0] + " " + venue[1] if venue else "Preprint / technical report", "status": "verified", "source": url, "publisher_source": venue[2] if venue else None, **analysis})
    for row in data.CATEGORIES[-1]["rows"]:
        fields = {"title": "{" + tex(row["name"]) + ": dataset documentation}", "author": "{" + tex(data.DATA_AUTHORS[row["cite"]]) + "}", "year": "n.d.", "howpublished": "Official dataset/release documentation", "url": row["links"][0][1], "note": "Accessed 30 September 2026; corpus sizes and access terms are card-reported"}
        entries.append("@misc{" + row["cite"] + ",\n" + ",\n".join("  " + field + " = {" + value + "}" for field, value in fields.items()) + "\n}")
    write(ROOT / "references.bib", "\n\n".join(entries))
    return papers

def tables():
    for category in data.CATEGORIES:
        assert len(category["rows"]) == 5, category["id"]
        # Widths sum to \linewidth after accounting for six intercolumn gaps.
        total = sum(category["widths"])
        assert abs(total - 1) < 1e-8
        columns = "".join(f">{{\\raggedright\\arraybackslash}}p{{{width:.2f}\\tablewidth}}" for width in category["widths"])
        lines = ["% Generated by scripts/generate.py; edit research/focused_review.py.", r"\begin{table}[H]", r"\centering", r"\small", r"\setlength{\tabcolsep}{4pt}", r"\setlength{\tablewidth}{\dimexpr\linewidth-6\tabcolsep\relax}", r"\renewcommand{\arraystretch}{1.12}", r"\caption{" + tex(category["title"]) + ". Five selected resources, unranked; availability checked 30 September 2026.}", r"\label{" + category["label"] + "}", r"\begin{tabular}{@{}" + columns + "@{}}", r"\toprule", " & ".join(r"\textbf{" + tex(head) + "}" for head in category["headers"]) + r" \\", r"\midrule"]
        for index, row in enumerate(category["rows"]):
            name = r"\textbf{" + (r"$\tau$-Voice" if row["name"] == "tau-Voice" else tex(row["name"])) + r"}\par\citep{" + row["cite"] + "}"
            cells = [tex(cell) for cell in row["cells"]]
            if row["links"]:
                link_column = 1 if category["id"] == "systems" else -1
                cells[link_column] += r"\par " + "; ".join(r"\href{" + url + "}{" + tex(label) + "}" for label, url in row["links"]) + "."
            lines.append(" & ".join([name] + cells) + r" \\")
            if index < 4:
                lines.append(r"\addlinespace[4pt]")
        lines += [r"\bottomrule", r"\end{tabular}", r"\end{table}"]
        write(ROOT / "tables" / (category["id"] + ".tex"), "\n".join(lines))

def ideas(papers):
    questions = {q["id"]: q for q in data.RQ}
    by_key = {p["key"]: p for p in papers}
    specifics = {
        "I1": ("Causal correction-risk calibration improves accuracy/latency over fixed prefix length without learning only speech duration.", "Train a small calibration head on paired shared-prefix questions; hold out templates/speaking rates and compare with fixed/end-of-turn triggers.", "medium", "low"),
        "I2": ("Playback-stage dependency validation reduces stale audible claims beyond generation-stage validation alone.", "Inject corrections at generation, synthesis, queue and playback stages; compare the same model with and without playback revalidation.", "medium", "medium"),
        "I3": ("A duration- and correction-risk-aware cap offers a better stale-claim/fluency frontier than a fixed lead limit.", "Sweep fixed-duration queue caps against a risk-aware cap on matched interrupted dialogues; report stale seconds, underruns and repair quality.", "medium", "medium"),
        "I4": ("Reserving ingestion capacity reduces correction failures attributable to generation contention, but not intrinsic encoder lookahead.", "Under matched speaking load, compare FIFO and ingestion-priority scheduling with a fixed encoder; log capture/arrival/incorporation delays separately.", "low", "medium"),
        "I5": ("Speaker-owned dependency states reduce irrelevant invalidation and stale relevant answers relative to a global state.", "Cross relevant correction/backchannel/other-directed input with oracle and predicted speaker labels; measure attribution and reasoning errors separately.", "high", "high"),
        "I6": ("An evidence-age-aware controller has fewer deadline misses at matched accuracy than a fixed temporal quantum under jitter/load.", "Replay identical speech under controlled jitter/rates/contention using the same backbone and feature extractor; compare fixed and two/three-level scheduling.", "high", "high"),
        "I7": ("Joint backend and playback dependency validation improves corrected outcomes beyond existing indexed cancellation and stale-result suppression.", "Vary simulated backend delay and correction stage; compare blind admission, cancel/stale suppression, and joint speaker/task-output validation.", "medium", "medium"),
        "I8": ("Some virtual-time task-success advantages disappear or reverse when real inference/playback deadlines are enforced.", "Replay the same deterministic tasks and model traces with virtual advancement versus measured physical time; isolate runtime/provider confounds.", "low", "medium"),
    }
    result = []
    for iid, rqid, title, one_liner, ctype, gaps, compute, implementation, risk, outcome in data.IDEA_SPECS:
        q = questions[rqid]
        hypothesis, experiment, risk_level, complexity = specifics[iid]
        prior = [{"key": key, "title": by_key[key]["title"], "authors": by_key[key]["authors"], "year": data.VENUES[key][1] if key in data.VENUES else by_key[key]["date"][:4], "url": "https://arxiv.org/abs/" + data.PAPERS[key]} for key in q["prior_work"]]
        prior_text = "; ".join(p["authors"][0] + " et al., " + p["year"] + " — " + p["title"] + " (" + p["url"] + ")" for p in prior)
        result.append({"id": iid, "research_question": rqid, "title": title, "one_liner": one_liner, "hypothesis": hypothesis, "proposed_method": one_liner + " " + q["method"], "minimal_experiment": experiment, "contribution_type": "diagnostic" if ctype == "analysis" else "method", "novelty_rationale": q["distinction"], "closest_prior_work": prior_text, "closest_prior_work_records": prior, "feasibility": {"compute": "Pilot estimate, not measured: " + compute + "; one A100 80 GB for a released 7--9B inference baseline, subject to runtime profiling. Estimates are per candidate, not a sum or training commitment.", "data": "200--500 paired controlled short dialogues; use synthetic causal-prefix pilot first, then licensed/gated recordings only after access approval. Keep benchmark test sets held out.", "implementation": complexity}, "implementation_notes": implementation, "risk": risk_level, "risk_notes": risk, "expected_outcome": outcome, "based_on_gaps": gaps})
    removed = [{"title": "Standalone indexed backend cancellation and stale-result suppression", "reason": "Already explicitly implemented by AdaptDuplex (arXiv:2609.29217); no distinct research claim on its own."}, {"title": "Foundation-scale reproduction of FLAIR or StepAudio 3 Realtime", "reason": "Not a feasible small pilot: complete training mixture not located and documented foundation-scale compute exceeds the skill's one-week pilot bound."}]
    payload = {"instruction": "Now craft a latex document, using a proper template (e.g., ICLR or something), as also a report, but 1). be a bit more focused, for each category, list the top-5 most relevant systems/papers. 2). Based on the original proposal, also list the major research questions that we might be able to pursue. For instance, the think while listen or think while speaking, etc., are some good formulations. Also I think the key is synchronization, both speaking sync the listening sync, since LLM is not time-aware. Create also a preview for the drafted latex.", "date": data.DATE, "grounded_on": "literature.json", "grounding_status": "grounded", "status": "Unranked candidate ideas; hypotheses, not results or established novelty", "light_filter": "Eight retained; two obvious directions excluded for duplication or pilot infeasibility. No independent external judging was requested or performed.", "ideas": result, "removed": removed}
    write(ROOT / "research" / "ideas.json", json.dumps(payload, ensure_ascii=False, indent=2))
    lines = ["# Candidate research ideas", "", payload["status"] + ". Grouped under the five report questions; no winners selected."]
    for idea in result:
        lines += ["", "## " + idea["id"] + ": " + idea["title"], "", "Research question: " + idea["research_question"] + ".", ""]
        for field in ("one_liner", "hypothesis", "proposed_method", "minimal_experiment", "contribution_type", "novelty_rationale", "risk", "risk_notes", "expected_outcome"):
            lines += ["**" + field.replace("_", " ").capitalize() + ":** " + idea[field], ""]
        lines += ["**Closest prior work:** " + ", ".join("[" + p["title"] + "](" + p["url"] + ")" for p in idea["closest_prior_work_records"]), "", "**Feasibility:** " + " ".join(idea["feasibility"].values()) + " " + idea["implementation_notes"], "", "**Based on gaps:** " + ", ".join(idea["based_on_gaps"])]
    lines += ["", "## Removed (with reason)", "", "| Direction | Reason |", "| --- | --- |"]
    lines += ["| " + item["title"] + " | " + item["reason"] + " |" for item in removed]
    write(ROOT / "research" / "IDEAS.md", "\n".join(lines))

def main():
    audit = json.loads((ROOT / "research" / "source-audit.json").read_text())
    papers = bibliography(audit)
    tables()
    ideas(papers)
    payload = {"date": data.DATE, "scope": "Original streaming/revision/speaker-aware reasoning proposal; exactly five resources in each of four categories", "selection": "Purposive relevance selection, unranked; not an exhaustive or independently reproduced survey", "categories": data.CATEGORIES, "papers": papers, "themes": ["Acoustic frames, autoregressive tokens, physical elapsed time and audible commitments are distinct.", "Full-duplex interfaces already encode timing, but do not by themselves establish causal reasoning-state consistency.", "Model inference releases are more common than reproducible complete training mixtures."], "gaps": data.GAPS, "research_questions": data.RQ, "limitations": ["Availability snapshots can change; not located is not evidence of nonexistence.", "No benchmarks, model calls, training or GPU jobs were run.", "Novelty is a bounded inference from these sources, not an exhaustive guarantee.", "Dataset scales and licenses are reported by their documentation, not independently audited."]}
    write(ROOT / "research" / "literature.json", json.dumps(payload, indent=2, ensure_ascii=False))
    lines = ["# Focused duplex literature review", "", "Review cutoff: " + data.DATE + ". Four categories, five resources each; rows are not ranked."]
    for category in data.CATEGORIES:
        lines += ["", "## " + category["title"], "", category["selection"], "", "| " + " | ".join(category["headers"]) + " |", "| " + " | ".join(["---"] * 4) + " |"]
        for row in category["rows"]:
            link = "https://arxiv.org/abs/" + data.PAPERS[row["cite"]] if row["cite"] in data.PAPERS else row["links"][0][1]
            cells = ["[" + row["name"] + "](" + link + ")"] + row["cells"]
            lines.append("| " + " | ".join(cells) + " |")
    lines += ["", "## Synthesis and open gaps", ""]
    lines += [gap["id"] + ": " + gap["text"] for gap in data.GAPS]
    lines += ["", "## Five major research questions", ""]
    for q in data.RQ:
        lines += ["### " + q["id"] + ": " + q["title"], "", q["question"], "", "Hypothesis: " + q["hypothesis"], "", "Small experiment: " + q["experiment"], "", "Prior-work distinction: " + q["distinction"], ""]
    lines += ["## References", ""]
    for paper in papers:
        lines += ["- [" + paper["title"] + "](" + paper["source"] + "). " + ", ".join(paper["authors"]) + ". " + paper["venue"] + "; " + paper["date"] + "."]
    lines += ["", "## Per-paper notes", ""]
    for paper in papers:
        lines += ["### " + paper["title"], ""]
        for field in ("problem", "method", "results", "relevance", "limitations"):
            lines += [field.capitalize() + ": " + (paper[field] or "Not extracted in the focused digest."), ""]
    write(ROOT / "research" / "LITERATURE.md", "\n".join(lines))
    print("Generated four five-row TeX tables, 21 verified/documented references, a focused digest, and eight unranked candidate notes.")

if __name__ == "__main__":
    main()
