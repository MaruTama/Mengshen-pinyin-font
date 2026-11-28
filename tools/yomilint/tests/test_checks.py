"""Each check passes on the good font and notices the font broken its way."""

import pytest
from fontmaker import READINGS, FontPlan, corrupt_gsub


def test_the_good_font_has_no_findings(project):
    assert project().findings() == []


def test_the_good_font_has_no_findings_by_glyph_names(project):
    assert project(kind="names").findings() == []


def test_a_glyph_shared_with_a_character_outside_the_dictionary(project, ):
    # U+2F00 KANGXI RADICAL ONE sorts before 一 and is in no dictionary.
    plan = FontPlan(aliases={"\u2f00": "一"})
    assert project(plan=plan).findings() == []
    assert project(plan=plan, kind="names").findings() == []


def test_a_character_without_a_glyph(project):
    built = project(plan=FontPlan(unmapped=["一"]))
    assert "coverage/charset-has-glyph" in built.findings()


def test_a_default_glyph_without_annotation(project):
    # The dictionary knows a character the font draws bare.
    readings = dict(READINGS)
    plan = FontPlan(shown={("一", 1): ""})
    built = project(plan=plan, dictionary=readings)
    assert "coverage/charset-has-reading" in built.findings()


def test_a_default_reading_that_is_not_the_dictionarys(project):
    built = project(plan=FontPlan(shown={("着", 1): "zhuó", ("着", 2): "zhe"}))
    assert "coverage/default-reading" in built.findings()


def test_a_reading_no_glyph_shows(project):
    readings = dict(READINGS, 着=["zhe", "zhuó", "zháo"])
    built = project(dictionary=readings)
    assert "coverage/all-readings-reachable" in built.findings()


def test_a_phrase_that_reads_wrong(project):
    built = project(plan=FontPlan(with_rclt=False))
    assert built.findings().count("context/phrase") == 1


def test_an_exception_that_reads_wrong(project):
    built = project(phrases=["着手: zhuó/shǒu, 背着手: bèi/zhuó/shǒu"])
    assert built.findings() == ["context/phrase"]


def test_a_phrase_longer_than_its_readings(project):
    built = project(phrases=["着手: zhuó"])
    assert built.findings() == ["context/phrase"]


def test_a_selector_that_shows_another_reading(project):
    built = project(plan=FontPlan(shown={("着", 2): "zháo"}))
    findings = built.findings()
    assert "select/ivs-order" in findings


def test_a_missing_reading_selector(project):
    built = project(plan=FontPlan(missing_selectors=[("着", 2)]))
    assert built.findings() == ["select/ivs-order"]


def test_a_missing_bare_selector(project):
    built = project(plan=FontPlan(missing_selectors=[("一", 0)]))
    assert built.findings() == ["select/ivs-none"]


def test_no_alternates(project):
    built = project(plan=FontPlan(with_aalt=False))
    assert set(built.findings()) == {"select/aalt-covers-readings"}


def test_too_many_glyphs(project):
    # 26 glyphs and 65,500 of padding leave less than 500 to spare.
    built = project(plan=FontPlan(padding_glyphs=65_100), headroom=500)
    assert built.findings() == ["format/glyph-count"]


def test_names_that_disagree_with_the_parts(project):
    # `.ss02` of 着 is named as its second reading but draws the first.
    built = project(plan=FontPlan(shown={("着", 2): "zhe"}))
    assert "resolve/methods-agree" in built.findings()


# ---- context: a phrase inside a sentence ---------------------------------


def test_a_rule_that_fails_inside_a_sentence(project):
    # 一 is in no phrase, so it is what the check puts around each phrase;
    # after it the 着手 rule is switched off.
    built = project(plan=FontPlan(ignore_after=["一"]))
    assert built.findings() == ["context/phrase-in-sentence"]


# ---- geometry -------------------------------------------------------------


def test_an_annotation_above_the_line(project):
    # Letters are 150 units tall: at 900 they reach 1050, past winAscent 1000.
    built = project(plan=FontPlan(annotation_y=900))
    assert set(built.findings()) == {"geometry/no-clipping"}


def test_an_annotation_on_the_character(project):
    # The character is 700 tall and the annotation starts at 650.
    built = project(plan=FontPlan(annotation_y=650))
    assert set(built.findings()) == {"geometry/no-overlap"}


def test_an_annotation_too_close_to_the_character(project):
    # 60 units above the character, where the spec asks for 100.
    assert set(project(min_gap=100).findings()) == {"geometry/no-overlap"}
    assert project(min_gap=60).findings() == []


def test_a_reading_with_another_advance(project):
    built = project(plan=FontPlan(advances={"uni7740.ss02": 1200}))
    assert built.findings() == ["geometry/advance-matches-base"]


def test_an_annotation_wider_than_the_character(project):
    # Four letters 300 apart do not fit in 1000 units.
    built = project(plan=FontPlan(letter_advance=300))
    assert set(built.findings()) == {"geometry/annotation-within-advance"}


# ---- format ---------------------------------------------------------------


def test_components_that_refer_to_each_other(project):
    built = project(plan=FontPlan(circular=True))
    findings = built.findings()
    assert findings.count("format/no-circular-reference") == 1
    # The sanitizer, when it is installed, refuses the loop as well.
    assert set(findings) <= {"format/no-circular-reference", "format/ots"}


def test_a_broken_table_is_reported_and_stops_no_other_check(project):
    pytest.importorskip("ots")
    built = project()
    corrupt_gsub(built.font)
    findings = built.findings()
    assert "format/tables-parse" in findings
    assert "format/ots" in findings


def test_the_sanitizer_accepts_the_good_font(project):
    pytest.importorskip("ots")
    assert "format/ots" not in project().findings()
