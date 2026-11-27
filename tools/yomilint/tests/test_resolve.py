import pytest

from yomilint.font import FontUnderTest
from yomilint.resolve import make_resolver
from yomilint.spec import load_spec


@pytest.mark.parametrize("kind", ["components", "names"])
def test_a_glyph_shows_the_reading_it_was_built_with(project, kind):
    built = project(kind=kind)
    font = FontUnderTest(built.font)
    resolver = make_resolver(load_spec(built.spec), font)
    assert resolver.reading("uni7740") == "zhe"
    assert resolver.reading("uni7740.ss01") == "zhe"
    assert resolver.reading("uni7740.ss02") == "zhuó"
    assert resolver.reading("uni4E00") == "yī"
    assert resolver.reading("uni624B") == "shǒu"


@pytest.mark.parametrize("kind", ["components", "names"])
def test_a_glyph_without_annotation_has_no_reading(project, kind):
    built = project(kind=kind)
    font = FontUnderTest(built.font)
    resolver = make_resolver(load_spec(built.spec), font)
    assert resolver.reading("uni7740.ss00") is None
    assert resolver.reading(".notdef") is None


def test_shaping_applies_the_contextual_rules(project):
    font = FontUnderTest(project().font)
    assert font.shape("着手") == ["uni7740.ss02", "uni624B"]
    assert font.shape("背着手") == ["uni80CC", "uni7740", "uni624B"]
