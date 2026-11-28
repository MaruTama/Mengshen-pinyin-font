"""Each check passes on the good font and notices the font broken its way."""

import pytest
from fontmaker import READINGS, FontPlan, corrupt_gsub


def test_the_good_font_has_no_findings(project):
    assert project().findings() == []


def test_the_good_font_has_no_findings_by_glyph_names(project):
    assert project(kind="names").findings() == []


def test_a_glyph_shared_with_a_character_outside_the_dictionary(
    project,
):
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


def test_an_annotation_off_the_center(project):
    # 着's second reading is 60 units (0.06 em) to the right of the middle
    # of the advance; the tolerance is 0.01 em.
    built = project(plan=FontPlan(annotation_dx={("着", 2): 60}))
    assert built.findings() == ["geometry/centered"]


def test_an_annotation_within_the_center_tolerance(project):
    plan = FontPlan(annotation_dx={("着", 2): 8})
    assert project(plan=plan).findings() == []
    # The spec may ask for more.
    built = project(plan=plan, geometry={"center_tolerance": 0.005})
    assert built.findings() == ["geometry/centered"]


def test_the_center_tolerance_is_a_part_of_the_em(project):
    # The same 15 units: 0.015 em in a 1000-unit em, 0.0075 em in 2000.
    shift = {("着", 2): 15}
    small = project(plan=FontPlan(annotation_dx=shift))
    assert small.findings() == ["geometry/centered"]
    large = project(plan=FontPlan(annotation_dx=shift, units_per_em=2000))
    assert large.findings() == []
    # And 30 units are 0.015 em in 2000: the same verdict as 15 in 1000.
    far = project(plan=FontPlan(annotation_dx={("着", 2): 30}, units_per_em=2000))
    assert far.findings() == ["geometry/centered"]


def test_an_annotation_on_another_baseline(project):
    # 着's second reading is raised 40 units; the others stand on 760.
    built = project(plan=FontPlan(baseline_shift={("着", 2): 40}))
    assert built.findings() == ["geometry/baseline-aligned"]


def test_a_baseline_within_the_tolerance(project):
    # One unit is 0.001 em, the default tolerance.
    plan = FontPlan(baseline_shift={("着", 2): 1})
    assert project(plan=plan).findings() == []
    built = project(plan=plan, geometry={"baseline_tolerance": 0})
    assert built.findings() == ["geometry/baseline-aligned"]


def test_the_baseline_tolerance_is_a_part_of_the_em(project):
    # The same 2 units: 0.002 em in a 1000-unit em, 0.001 em in 2000.
    shift = {("着", 2): 2}
    assert project(plan=FontPlan(baseline_shift=shift)).findings() == [
        "geometry/baseline-aligned"
    ]
    large = project(plan=FontPlan(baseline_shift=shift, units_per_em=2000))
    assert large.findings() == []


def test_good_fonts_with_letters_drawn_from_parts(project):
    # A letter that is a composite (a body and a mark) must read as one
    # letter: the mark's own origin is no baseline.
    plan = FontPlan(composite_letters=True)
    assert project(plan=plan).findings() == []
    assert project(plan=plan, kind="names").findings() == []


def test_a_raised_annotation_with_letters_drawn_from_parts(project):
    plan = FontPlan(composite_letters=True, baseline_shift={("着", 2): 40})
    assert project(plan=plan).findings() == ["geometry/baseline-aligned"]


def test_one_reading_drawn_larger_does_not_make_the_rest_too_small(project):
    # 着's second reading is 1.5 times the size of all the others: they are
    # not too small, it is large. Against the largest they would be 0.67.
    plan = FontPlan(shrink={("着", 2): 1.5})
    built = project(plan=plan, geometry={"min_scale": 0.7})
    assert built.findings() == []


def test_lines_so_close_that_a_descender_touches_the_annotation_below(project):
    # A letter g reaches 300 below the baseline: the annotation of the next
    # line, 910 above its own baseline, is 10 units into it.
    built = project(plan=FontPlan(latin_descent=300))
    assert built.findings() == ["geometry/line-gap"]


def test_a_long_reading_shrunk_too_far(project):
    # Letters at 0.4 of the size the other readings have; the lower bound
    # is 0.6.
    built = project(plan=FontPlan(shrink={("着", 2): 0.4}))
    assert built.findings() == ["geometry/min-scale"]


def test_a_long_reading_shrunk_within_the_bound(project):
    plan = FontPlan(shrink={("着", 2): 0.7})
    assert project(plan=plan).findings() == []
    built = project(plan=plan, geometry={"min_scale": 0.8})
    assert built.findings() == ["geometry/min-scale"]


def test_lines_so_close_that_annotations_touch_the_line_above(project):
    # Lines are 900 apart (700 + 200); an annotation reaches 910 above the
    # baseline and a character 0 below it: the next line's annotation
    # pokes 10 units into this line's characters.
    built = project(plan=FontPlan(hhea_ascent=700))
    assert built.findings() == ["geometry/line-gap"]


# ---- the rules themselves -------------------------------------------------


def test_two_lookups_that_substitute_differently_for_one_context(project):
    built = project(plan=FontPlan(conflicting_rule=True))
    assert built.findings() == ["context/rule-conflict"]


def test_a_rule_that_an_earlier_rule_with_the_same_match_hides(project):
    built = project(plan=FontPlan(shadowed_rule=True))
    assert built.findings() == ["context/unreachable-rule"]


def test_a_reading_chosen_by_a_feature_that_is_off_by_default(project):
    built = project(plan=FontPlan(reading_feature="ss01"))
    assert built.findings() == ["context/feature-always-on"]


def test_a_reading_chosen_by_a_feature_that_is_on_by_default(project):
    assert project(plan=FontPlan(reading_feature="calt")).findings() == []


def test_the_spec_says_which_features_are_on(project):
    plan = FontPlan(reading_feature="ss01")
    built = project(plan=plan, context={"default_features": ["rclt", "ss01"]})
    assert built.findings() == []
    built = project(plan=FontPlan(), context={"default_features": ["calt"]})
    assert built.findings() == ["context/feature-always-on"]


def test_the_rule_checks_say_which_rule(project):
    from yomilint.runner import run

    plan = FontPlan(shadowed_rule=True, conflicting_rule=True)
    built = project(plan=plan)
    messages = {f.check: f for f in run(built.font, built.spec)}
    assert messages["context/unreachable-rule"].subject.startswith("lookup ")
    assert "lookup" in messages["context/rule-conflict"].message


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
