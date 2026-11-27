"""Each check passes on the good font and notices the font broken its way."""

from fontmaker import READINGS, FontPlan


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
