#!/usr/bin/env python3
"""Regression checks for mixed-unit scores, missing cells and imported references."""
import json
from pathlib import Path
import unittest

from build_performance import all_groups, exact_table, plot_profile, scores
from performance_profiles import PROFILES

ROOT = Path(__file__).resolve().parents[1]


class PerformanceTests(unittest.TestCase):
    def setUp(self):
        self.data = json.loads((ROOT / "research/reported-performance.json").read_text())
        self.groups = {group["id"]: group for group in all_groups(self.data)}

    def test_wer_conversion_and_missing_cells(self):
        group = self.groups["duplexomni"]
        original = json.dumps(group)
        self.assertEqual(scores(group, group["rows"][0]), [72.6, 77.2, 53.8, 11.92, 0.506])
        self.assertIsNone(scores(group, group["rows"][1])[3])
        self.assertEqual(json.dumps(group), original)
        table = exact_table(self.data, group)
        self.assertIn("11.92", table)
        self.assertIn("thinking only", table)
        self.assertIn("NR", table)

    def test_nr_is_not_a_zero_length_bar(self):
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        group = self.groups["duplexomni"]
        spec = next(profile for profile in PROFILES if profile["id"] == "duplexomni")
        figure = plot_profile(self.data, group, spec, plt)
        self.assertEqual(len(figure.axes[0].patches), 6)
        self.assertEqual(len(figure.axes[3].patches), 4)
        self.assertEqual(sum(text.get_text() == "NR" for text in figure.axes[3].texts), 2)
        plt.close(figure)

    def test_comparator_sources_stay_distinct(self):
        group = self.groups["voicechat_fdb3"]
        by_model = {row["model"]: row["source"] for row in group["rows"]}
        self.assertEqual(by_model["NemotronLabs VoiceChat"], "voicechat")
        self.assertEqual(by_model["Gemini Live 3.1"], "voicechat")
        self.assertEqual(by_model["GPT-Realtime"], "fdb_original")
        self.assertEqual(by_model["Realtime-Venus-Omni"], "fdb_venus")
        self.assertEqual(len(self.groups), len(PROFILES))

    def test_thinkaloud_latency_endpoints_and_missing_values(self):
        group = self.groups["thinkaloud_timing"]
        self.assertEqual(scores(group, group["rows"][0]), [91.6, 83.6, 0.36, 4.34])
        self.assertEqual(group["metric_specs"][2]["unit"], "s")
        self.assertFalse(group["metric_specs"][3]["higher"])
        self.assertIsNone(group["rows"][-2]["source_values"][3])
        self.assertEqual(group["rows"][-1]["source_values"][2:], [None, None])
        self.assertIn("cumulative", group["notes"])
        self.assertIn("not time to first audio", group["notes"])

    def test_thinkaloud_qa_is_s2s_not_s2t_or_a_radar(self):
        group = self.groups["thinkaloud_qa"]
        spec = next(profile for profile in PROFILES if profile["group"] == group["id"])
        self.assertEqual(spec["kind"], "facets")
        self.assertEqual(group["rows"][0]["source_values"], [40.3, 38.7])
        closed = [row for row in group["rows"] if row["role"] == "closed_voice"]
        self.assertEqual([row["model"] for row in closed], ["GPT-4o-Realtime"])
        self.assertEqual(closed[0]["source_values"], [51.6, 69.7])
        self.assertIn("S2S block", group["protocol"])


if __name__ == "__main__":
    unittest.main()
