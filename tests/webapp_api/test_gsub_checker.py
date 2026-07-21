# -*- coding: utf-8 -*-
"""GSUB rclt simulation: chaining semantics, ignore rules, readings."""

from __future__ import annotations

from webapp.backend.services import gsub_checker

# Synthetic table mirroring the generator's structure:
#   A after B  -> A.ss02 (context rule, rclt_0)
#   "AC"       -> A.ss03, except when preceded by B (ignore, rclt_2)
TABLE = {
    "lookupOrder": [
        "lookup_rclt_0",
        "lookup_sub2",
        "lookup_rclt_2",
        "lookup_sub3",
    ],
    "lookups": {
        "lookup_rclt_0": {
            "type": "gsub_chaining",
            "subtables": [
                {
                    "match": [["gB"], ["gA"]],
                    "apply": [{"at": 1, "lookup": "lookup_sub2"}],
                    "inputBegins": 1,
                    "inputEnds": 2,
                },
            ],
        },
        "lookup_rclt_2": {
            "type": "gsub_chaining",
            "subtables": [
                # ignore: B A' C -> no substitution
                {
                    "match": [["gB"], ["gA"], ["gC"]],
                    "apply": [],
                    "inputBegins": 1,
                    "inputEnds": 2,
                },
                {
                    "match": [["gA"], ["gC"]],
                    "apply": [{"at": 0, "lookup": "lookup_sub3"}],
                    "inputBegins": 0,
                    "inputEnds": 2,
                },
            ],
        },
        "lookup_sub2": {"type": "gsub_single", "subtables": [{"gA": "gA.ss02"}]},
        "lookup_sub3": {"type": "gsub_single", "subtables": [{"gA": "gA.ss03"}]},
    },
}

CHAR_TO_GLYPH = {"A": "gA", "B": "gB", "C": "gC"}
GLYPH_TO_CHAR = {v: k for k, v in CHAR_TO_GLYPH.items()}
READINGS = {"A": ["a0", "a1", "a2"], "B": ["b0"], "C": ["c0"]}


def _simulate(text: str):
    return gsub_checker.simulate(
        TABLE, text, CHAR_TO_GLYPH, GLYPH_TO_CHAR, lambda c: READINGS.get(c, [])
    )


class TestSimulate:
    def test_context_rule_substitutes(self):
        rows = _simulate("BA")
        assert rows[1]["final_glyph"] == "gA.ss02"
        # .ss02 -> readings[1]
        assert rows[1]["reading"] == "a1"

    def test_no_context_keeps_default(self):
        rows = _simulate("A")
        assert rows[0]["final_glyph"] == "gA"
        assert rows[0]["reading"] == "a0"
        assert rows[0]["applied"] == []

    def test_phrase_rule_fires(self):
        rows = _simulate("AC")
        assert rows[0]["final_glyph"] == "gA.ss03"
        assert rows[0]["reading"] == "a2"

    def test_ignore_rule_suppresses_substitution(self):
        # In "BAC": rclt_0 first substitutes A after B (gA.ss02), so the
        # rclt_2 rules no longer match — the exceptional sub must not fire.
        rows = _simulate("BAC")
        assert rows[1]["final_glyph"] == "gA.ss02"

    def test_ignore_wins_within_same_lookup(self):
        # Drop the rclt_0 rule so only rclt_2 sees "BAC": the ignore rule
        # (listed first) must consume A and suppress the "AC" substitution.
        table = {
            "lookupOrder": ["lookup_rclt_2", "lookup_sub3"],
            "lookups": {
                "lookup_rclt_2": TABLE["lookups"]["lookup_rclt_2"],
                "lookup_sub3": TABLE["lookups"]["lookup_sub3"],
            },
        }
        rows = gsub_checker.simulate(
            table, "BAC", CHAR_TO_GLYPH, GLYPH_TO_CHAR, lambda c: READINGS.get(c, [])
        )
        assert rows[1]["final_glyph"] == "gA"  # unchanged
        assert rows[1]["reading"] == "a0"
        assert any(a.get("ignored") for a in rows[1]["applied"])


class TestGlyphReading:
    def test_mapping_convention(self):
        readings = ["r0", "r1", "r2"]
        assert gsub_checker._glyph_reading("g", readings) == "r0"
        assert gsub_checker._glyph_reading("g.ss01", readings) == "r0"
        assert gsub_checker._glyph_reading("g.ss02", readings) == "r1"
        assert gsub_checker._glyph_reading("g.ss00", readings) is None
        assert gsub_checker._glyph_reading("g.ss09", readings) is None


class TestExpectedPhrases:
    def test_parses_all_sources(self):
        cases = gsub_checker.parse_expected_phrases()
        by_phrase = {c["phrase"]: c for c in cases}
        # The canonical exceptional-pattern pair
        assert by_phrase["着手"]["expected"] == ["zhuó", "shǒu"]
        assert by_phrase["背着手"]["expected"] == ["bèi", "zhe", "shǒu"]
        assert by_phrase["着手"]["source"] == "exceptional"
        # Pattern one is the bulk of the data
        assert sum(1 for c in cases if c["source"] == "pattern_one") > 1000


class TestVerifyClassification:
    def test_statuses(self):
        assert gsub_checker._classify("x", "x", "d") == "ok"
        assert gsub_checker._classify("x", "d", "d") == "fallback"
        assert gsub_checker._classify("x", "y", "d") == "wrong"

    def test_verify_phrases_counts(self):
        cases = [
            {"phrase": "BA", "expected": ["b0", "a1"], "source": "t"},  # ok
            {"phrase": "A", "expected": ["a9"], "source": "t"},  # fallback
        ]
        report = gsub_checker.verify_phrases(
            TABLE, cases, CHAR_TO_GLYPH, GLYPH_TO_CHAR, lambda c: READINGS.get(c, [])
        )
        assert report["counts"] == {"ok": 1, "fallback": 1, "wrong": 0}


class TestCharRuleGraph:
    def test_rules_for_target_char(self):
        graph = gsub_checker.char_rule_graph(
            TABLE, "A", CHAR_TO_GLYPH, GLYPH_TO_CHAR, READINGS["A"]
        )
        assert graph["glyph"] == "gA"
        lookups = {r["lookup"] for r in graph["rules"]}
        assert lookups == {"lookup_rclt_0", "lookup_rclt_2"}
        ignore_rules = [r for r in graph["rules"] if r["ignore"]]
        assert len(ignore_rules) == 1
        normal = [r for r in graph["rules"] if not r["ignore"]]
        assert {r["output_reading"] for r in normal} == {"a1", "a2"}
        # Context translated back to characters
        assert ignore_rules[0]["context"] == [["B"], ["A"], ["C"]]
