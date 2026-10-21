"""Offline behavioral checks. All observations here are synthetic, never client data."""
import argparse
import copy
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "skills/seo-geo/scripts"
sys.path.insert(0, str(SCRIPTS))
import geo
import page_audit


class MeasurementTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="seo-geo-test-")
        self.path = Path(self.tmp.name)
        geo.initialize(argparse.Namespace(out=self.path / "client", domain="acme.example", brand="Acme", category="Terminsoftware"))
        self.cfgpath = self.path / "client/project.json"
        c = geo.read_json(self.cfgpath)
        c["brands"]["Other"] = {"aliases": ["Other"], "domains": ["other.example"]}
        c["repeats"] = 1
        c["prompts"] = [c["prompts"][0]]
        self.cfgpath.write_text(json.dumps(c), encoding="utf-8")
        self.c = geo.config(self.cfgpath)

    def tearDown(self):
        self.tmp.cleanup()

    def row(self, **kw):
        raw = {"id": "one", "prompt_id": "core-1", "repeat": 1, "surface": "chatgpt-search", "method": "consumer_ui",
            "model": "observed-model", "country": "DE", "language": "de", "context": "fresh synthetic fixture",
            "search_mode": "auto", "captured_at": "2026-10-12T09:00:00Z", "status": "ok",
            "answer": "Acme and Other are options. Acme may be unsuitable.", "citations": ["https://docs.acme.example/a"],
            "retrieved_sources": None, "search_triggered": True, "artifact": "capture.txt", "recommendation": None}
        raw.update(kw)
        return geo.normalize(raw, self.c)

    def test_host_boundaries_aliases_and_no_recommendation_inference(self):
        row = self.row(citations=["https://acme.example.evil.test/", "https://other.example/acme.example"])
        self.assertFalse(row["brand_citations"]["Acme"])
        self.assertIsNone(row["recommendation"])
        self.assertTrue(geo.owned("https://docs.acme.example:443/p?ref=x", ["acme.example"]))
        self.assertFalse(geo.mentioned("ACMECorp", ["Acme"]))
        self.assertTrue(geo.mentioned("ACME, günstig", ["Acme"]))

    def test_errors_and_unknown_citations_are_not_negative_visibility(self):
        self.c["repeats"] = 3
        rows = [self.row(id="one", repeat=1), self.row(id="two", repeat=2, citations=None, answer="Other only"),
            self.row(id="three", repeat=3, status="error", error="capture timed out", answer="", citations=None)]
        g = geo.summarize_rows(rows, self.c)["groups"][0]
        self.assertEqual(g["brands"]["Acme"]["mention"]["n"], 2)
        self.assertEqual(g["brands"]["Acme"]["citation"]["n"], 1)
        self.assertEqual(g["brands"]["Acme"]["citation"]["rate"], 1)
        self.assertIsNone(g["brands"]["Acme"]["retrieved"]["rate"])
        self.assertEqual(g["errors"], 1)
        self.assertFalse(g["balanced_complete"])
        self.assertAlmostEqual(g["brands"]["Acme"]["mention_sov"], 1 / 3)

    def test_ui_api_and_controls_are_separate_groups(self):
        self.c["prompts"].append({"id": "control", "text": "Was ist Acme?", "cohort": "control"})
        rows = [self.row(), self.row(id="two", surface="openai-api", method="api_proxy"), self.row(id="control", prompt_id="control")]
        self.assertEqual(len(geo.summarize_rows(rows, self.c)["groups"]), 3)
        with self.assertRaisesRegex(ValueError, "Duplicate"):
            geo.summarize_rows([rows[0], rows[0]], self.c)

    def test_no_feature_denominator_and_failed_empty_answer(self):
        a = self.row(id="a", surface="google-aio", method="serp_capture", status="no_feature", answer="", citations=[], search_triggered=False)
        b = self.row(id="b", repeat=2, surface="google-aio", method="serp_capture")
        self.c["repeats"] = 2
        g = geo.summarize_rows([a, b], self.c)["groups"][0]
        self.assertEqual(g["brands"]["Acme"]["citation"]["rate"], 0.5)
        self.assertEqual(g["citation_when_search_triggered"]["rate"], 1)
        with self.assertRaisesRegex(ValueError, "answer"):
            self.row(answer="")

    def test_unresolved_grounding_urls_are_unknown(self):
        row = self.row(citations=["https://vertexaisearch.cloud.google.com/grounding-api-redirect/token"],
                       retrieved_sources=["https://vertexaisearch.cloud.google.com/grounding-api-redirect/token"])
        self.assertIsNone(row["brand_citations"]["Acme"])
        self.assertIsNone(row["brand_retrieved"]["Acme"])
        self.assertEqual(len(row["unresolved_citations"]), 1)

    def test_openai_sources_differ_from_visible_citations(self):
        parsed = geo.parse_response("openai", {"status": "completed", "output": [
            {"type": "web_search_call", "status": "completed", "action": {"sources": [{"url": "https://acme.example/"}]}},
            {"type": "message", "content": [{"type": "output_text", "text": "Other is an option", "annotations": [{"type": "url_citation", "url": "https://other.example/"}]}]}]})
        self.assertEqual(parsed["citations"], ["https://other.example/"])
        self.assertEqual(parsed["retrieved_sources"], ["https://acme.example/"])
        with self.assertRaises(ValueError):
            geo.parse_response("openai", {"status": "incomplete", "output": []})

    def test_perplexity_search_list_is_not_a_citation(self):
        p = geo.parse_response("perplexity", {"output": [
            {"type": "search_results", "results": [{"url": "https://acme.example/"}]},
            {"type": "message", "content": [{"type": "output_text", "text": "Acme [1]", "annotations": []}]}]})
        self.assertIsNone(p["citations"])
        self.assertEqual(p["retrieved_sources"], ["https://acme.example/"])

    def test_gemini_only_supported_chunks_are_citations(self):
        p = geo.parse_response("gemini", {"candidates": [{"finishReason": "STOP", "content": {"parts": [{"text": "Acme"}]},
            "groundingMetadata": {"webSearchQueries": ["software"], "groundingChunks": [
                {"web": {"uri": "https://acme.example/"}}, {"web": {"uri": "https://other.example/"}}],
                "groundingSupports": [{"groundingChunkIndices": [1]}]}}]})
        self.assertEqual(p["citations"], ["https://other.example/"])
        self.assertEqual(len(p["retrieved_sources"]), 2)

    def test_no_network_without_live_and_cap_before_calls(self):
        with patch.object(geo, "call", side_effect=AssertionError("Network must not run")):
            geo.collect(argparse.Namespace(config=self.cfgpath, out=self.path / "plan", live=False))
            self.assertEqual(geo.read_json(self.path / "plan/plan.json")["requests"], 0)
            c = geo.read_json(self.cfgpath)
            c["providers"]["openai"] = {"enabled": True, "model": "test-model", "search_mode": "auto"}
            c["max_requests"] = 0
            self.cfgpath.write_text(json.dumps(c), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "cap"):
                geo.collect(argparse.Namespace(config=self.cfgpath, out=self.path / "over-cap", live=True))

    def test_provider_failure_stops_without_retries(self):
        c = geo.read_json(self.cfgpath)
        c["repeats"] = 3
        c["providers"]["openai"] = {"enabled": True, "model": "test-model", "search_mode": "auto"}
        self.cfgpath.write_text(json.dumps(c), encoding="utf-8")
        with patch.dict(os.environ, {"OPENAI_API_KEY": "synthetic-test-key"}), patch.object(geo, "call", side_effect=ValueError("synthetic failure")) as call:
            geo.collect(argparse.Namespace(config=self.cfgpath, out=self.path / "failed-run", live=True))
            self.assertEqual(call.call_count, 1)
        rows = geo.jsonl(self.path / "failed-run/observations.jsonl")
        self.assertEqual(rows[0]["status"], "error")
        self.assertNotIn("synthetic-test-key", (self.path / "failed-run/plan.json").read_text())

    def test_end_to_end_import_summary_report_and_portfolio_change(self):
        (self.path / "capture.txt").write_text("SYNTHETIC RAW CAPTURE: Acme and Other", encoding="utf-8")
        source = self.path / "captures.jsonl"
        source.write_text(json.dumps(self.row()) + "\n", encoding="utf-8")
        geo.import_captures(argparse.Namespace(config=self.cfgpath, input=source, out=self.path / "run"))
        inp = self.path / "run/observations.jsonl"
        geo.summarize(argparse.Namespace(config=self.cfgpath, input=inp, out=self.path / "summary.json", period_start="2026-10-12", period_end="2026-10-18", complete=True))
        geo.report(argparse.Namespace(current=self.path / "summary.json", previous=None, metrics=None, previous_metrics=None, out=self.path / "report.md"))
        report = (self.path / "report.md").read_text()
        self.assertIn("100.0% (1/1)", report)
        self.assertIn("Baseline", report)
        self.assertIn("Entwurf", report)
        c = geo.read_json(self.cfgpath)
        c["prompts"][0]["text"] = "Changed query"
        self.cfgpath.write_text(json.dumps(c), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "Portfolio changed"):
            geo.summarize(argparse.Namespace(config=self.cfgpath, input=inp, out=self.path / "wrong.json"))

    def test_comparable_periods_require_adjacent_complete_windows(self):
        a = {"start": "2026-10-12", "end": "2026-10-18", "complete": True, "timezone": "Europe/Berlin"}
        b = {**a, "start": "2026-10-05", "end": "2026-10-11"}
        self.assertTrue(geo.periods_comparable(a, b))
        self.assertFalse(geo.periods_comparable(a, {**b, "complete": False}))
        self.assertFalse(geo.periods_comparable(a, {**b, "end": "2026-10-10"}))
        self.assertFalse(geo.periods_comparable(a, None))

    def test_metric_zero_base_and_missing_provenance(self):
        a = {"id": "clicks", "value": 10, "unit": "clicks", "source": "GSC", "artifact": "export.csv", "start": "2026-10-12", "end": "2026-10-18", "timezone": "America/Los_Angeles", "complete": True, "dimensions": "DE", "definition_version": "1"}
        b = {**a, "value": 0, "start": "2026-10-05", "end": "2026-10-11"}
        output = "\n".join(geo.metrics_table([a], [b]))
        self.assertIn("Basis 0", output)
        self.assertNotIn("inf", output)
        with self.assertRaisesRegex(ValueError, "artifact"):
            geo.metrics_table([{k: v for k, v in a.items() if k != "artifact"}], [])

    def test_report_deltas_need_periods_and_full_metric_coverage(self):
        self.c["repeats"] = 2
        old = geo.summarize_rows([self.row(id="a", repeat=1), self.row(id="b", repeat=2, citations=None)], self.c)
        cur = geo.summarize_rows([self.row(id="c", repeat=1, answer="Other", citations=[]), self.row(id="d", repeat=2, answer="Other", citations=None)], self.c)
        old["reporting_period"] = {"start": "2026-10-05", "end": "2026-10-11", "timezone": "Europe/Berlin", "complete": True}
        cur["reporting_period"] = {"start": "2026-10-12", "end": "2026-10-18", "timezone": "Europe/Berlin", "complete": True}
        geo.write_json(self.path / "old.json", old)
        geo.write_json(self.path / "cur.json", cur)
        geo.report(argparse.Namespace(current=self.path / "cur.json", previous=self.path / "old.json", metrics=None, previous_metrics=None, out=self.path / "delta.md"))
        lines = (self.path / "delta.md").read_text().splitlines()
        self.assertIn("-100.0 pp", next(l for l in lines if l.startswith("| Brand-Mention")))
        self.assertNotIn("pp", next(l for l in lines if l.startswith("| Domain-Zitation")))

    def test_returned_model_is_preserved_for_grouping(self):
        c = geo.read_json(self.cfgpath)
        c["providers"]["openai"] = {"enabled": True, "model": "alias", "search_mode": "auto"}
        self.cfgpath.write_text(json.dumps(c), encoding="utf-8")
        response = {"model": "actual-version", "status": "completed", "output": [
            {"type": "message", "content": [{"type": "output_text", "text": "Acme", "annotations": []}]}]}
        with patch.dict(os.environ, {"OPENAI_API_KEY": "synthetic-test-key"}), patch.object(geo, "call", return_value=response):
            geo.collect(argparse.Namespace(config=self.cfgpath, out=self.path / "model-run", live=True))
        row = geo.jsonl(self.path / "model-run/observations.jsonl")[0]
        self.assertEqual(row["model"], "actual-version")
        self.assertEqual(row["requested_model"], "alias")
        self.assertTrue((self.path / "model-run/project_snapshot.json").is_file())

    def test_total_missing_surface_is_reported_instead_of_disappearing(self):
        old = geo.summarize_rows([self.row(), self.row(id="api", surface="openai-api", method="api_proxy")], self.c)
        cur = geo.summarize_rows([self.row(id="api", surface="openai-api", method="api_proxy")], self.c)
        geo.write_json(self.path / "old.json", old)
        geo.write_json(self.path / "cur.json", cur)
        geo.report(argparse.Namespace(current=self.path / "cur.json", previous=self.path / "old.json", metrics=None, previous_metrics=None, out=self.path / "missing.md"))
        report = (self.path / "missing.md").read_text()
        self.assertIn("chatgpt-search / consumer_ui", report)
        self.assertIn("aktuell keine Beobachtung", report)
        self.assertIn("kein gemessener Sichtbarkeitsverlust", report)


class AuditTests(unittest.TestCase):
    def test_multiple_jsonld_scripts_graph_and_rendering_scope(self):
        html = '''<html><head><title>A &amp; B</title><link rel="canonical" href="/shop">
        <meta name="robots" content="noindex"><script type="application/ld+json">{"@graph":[{"@type":"Organization"},{"@type":"Product","offers":{"@type":"Offer"}}]}</script>
        <script type="application/ld+json">[{"@type":"BreadcrumbList"}]</script>
        <script type="application/ld+json">{broken}</script></head>
        <body><h1>Real <span>product</span></h1><div itemscope itemtype="https://schema.org/Product"></div></body></html>'''
        result = page_audit.parse_html(html, "https://example.com/")
        self.assertEqual(result["title"], "A & B")
        self.assertEqual(result["canonicals"], ["https://example.com/shop"])
        self.assertEqual(result["headings"][0]["text"], "Real product")
        self.assertEqual(set(result["json_ld_types"]), {"Organization", "Product", "Offer", "BreadcrumbList"})
        self.assertEqual(len(result["json_ld_parse_errors"]), 1)
        self.assertTrue(result["other_schema_markup_detected"]["microdata"])


if __name__ == "__main__":
    unittest.main()
