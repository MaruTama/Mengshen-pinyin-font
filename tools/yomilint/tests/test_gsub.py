"""The model of the substitution rules: what a rule matches and does, which
rule hides which, and which features reach which lookups."""

from types import SimpleNamespace as NS

from fontTools.feaLib.builder import addOpenTypeFeaturesFromString
from fontTools.fontBuilder import FontBuilder
from fontTools.pens.ttGlyphPen import TTGlyphPen
from yomilint.gsub import GlyphSet, GsubModel, subtable_rules

GLYPHS = [".notdef", "a", "b", "c", "d", "e", "f", "a.alt", "b.alt", "c.alt"]


def model_of(fea: str) -> GsubModel:
    """The model of a font whose GSUB is built from `fea`."""
    builder = FontBuilder(1000, isTTF=True)
    builder.setupGlyphOrder(GLYPHS)
    builder.setupCharacterMap({ord(g): g for g in "abcdef"})
    empty = TTGlyphPen(None).glyph()
    builder.setupGlyf({name: empty for name in GLYPHS})
    builder.setupHorizontalMetrics({name: (500, 0) for name in GLYPHS})
    builder.setupHorizontalHeader()
    addOpenTypeFeaturesFromString(builder.font, fea)
    return GsubModel(builder.font)


def s(*glyphs: str) -> GlyphSet:
    return GlyphSet(frozenset(glyphs))


def rule_of(*, backtrack=(), input=(), lookahead=(), lookup=0):
    """A rule as `subtable_rules` makes them, for the tests of `covers`."""
    from yomilint.gsub import Rule

    return Rule(lookup, 0, 0, tuple(backtrack), tuple(input), tuple(lookahead), ())


# ---- glyph sets ----------------------------------------------------------


def test_a_set_holds_another_when_it_has_all_its_glyphs():
    assert s("a", "b").holds(s("a"))
    assert not s("a").holds(s("a", "b"))


def test_the_rest_of_the_font_holds_what_it_leaves_out_of_its_list():
    rest = GlyphSet(frozenset({"a"}), negated=True)  # everything but a
    assert rest.holds(s("b", "c"))
    assert not rest.holds(s("a", "b"))
    assert rest.holds(GlyphSet(frozenset({"a", "b"}), negated=True))
    assert not GlyphSet(frozenset({"a", "b"}), negated=True).holds(rest)
    # A list of glyphs can never hold "the rest": the font may have more.
    assert not s("a", "b").holds(rest)


def test_a_set_knows_its_members():
    assert s("a").has("a") and not s("a").has("b")
    rest = GlyphSet(frozenset({"a"}), negated=True)
    assert rest.has("b") and not rest.has("a")


# ---- reading the subtables ----------------------------------------------


def test_chain_rules_of_format_1():
    model = model_of(
        "lookup L {sub a by a.alt;} L;"
        "feature calt { sub b a' lookup L c; sub b a' lookup L d; } calt;"
    )
    rules = model.rules(1)
    assert [r.text() for r in rules] == ["b a' c", "b a' d"]
    assert rules[0].backtrack == (s("b"),)
    assert rules[0].input == (s("a"),)
    assert rules[0].lookahead == (s("c"),)
    assert rules[0].actions == ((0, 0),)


def test_chain_rules_of_format_3_have_the_backtrack_nearest_first():
    model = model_of(
        "lookup L {sub a by a.alt;} L;"
        "feature calt { sub d b a' lookup L [c e]; } calt;"
    )
    (rule,) = model.rules(1)
    assert rule.backtrack == (s("b"), s("d"))
    assert rule.lookahead == (s("c", "e"),)
    assert rule.text() == "d b a' [c e]"


def test_extension_lookups_are_read_through():
    model = model_of(
        "lookup L {sub a by a.alt;} L;"
        "lookup M useExtension { sub b a' lookup L c; } M;"
        "feature calt { lookup M; } calt;"
    )
    assert [r.text() for r in model.rules(1)] == ["b a' c"]


def test_an_ignore_rule_has_no_action():
    model = model_of(
        "lookup L {sub a by a.alt;} L;"
        "feature calt { ignore sub b a' c; sub a' lookup L; } calt;"
    )
    assert model.rules(1)[0].actions == ()


def test_chain_rules_of_format_2_give_the_rest_of_the_font_for_class_0():
    table = NS(
        LookupType=6,
        Format=2,
        Coverage=NS(glyphs=["a", "b", "c"]),
        BacktrackClassDef=NS(classDefs={"d": 1}),
        InputClassDef=NS(classDefs={"a": 1, "b": 1, "c": 2}),
        LookAheadClassDef=NS(classDefs={"e": 1}),
        ChainSubClassSet=[
            None,
            NS(
                ChainSubClassRule=[
                    # class 1 input, class 1 backtrack, class 0 lookahead
                    NS(
                        Backtrack=[1],
                        Input=[],
                        LookAhead=[0],
                        SubstLookupRecord=[NS(SequenceIndex=0, LookupListIndex=3)],
                    )
                ]
            ),
            NS(
                ChainSubClassRule=[
                    NS(Backtrack=[], Input=[0], LookAhead=[], SubstLookupRecord=[])
                ]
            ),
        ],
    )
    first, second = subtable_rules(table, lookup=2, subtable=0)
    assert first.input == (s("a", "b"),)
    assert first.backtrack == (s("d"),)
    assert first.lookahead == (GlyphSet(frozenset({"e"}), negated=True),)
    assert first.actions == ((0, 3),)
    # The second glyph of the input is class 0: no class listed for it.
    assert second.input == (s("c"), GlyphSet(frozenset({"a", "b", "c"}), True))
    assert second.actions == ()


def test_a_rule_whose_set_is_empty_is_left_out():
    table = NS(
        LookupType=6,
        Format=3,
        BacktrackCoverage=[NS(glyphs=[])],
        InputCoverage=[NS(glyphs=["a"])],
        LookAheadCoverage=[],
        SubstLookupRecord=[],
    )
    assert subtable_rules(table, lookup=0, subtable=0) == []


def test_context_rules_of_the_three_formats_have_no_surroundings():
    format1 = NS(
        LookupType=5,
        Format=1,
        Coverage=NS(glyphs=["a", "b"]),
        SubRuleSet=[
            NS(SubRule=[NS(Input=["c"], SubstLookupRecord=[])]),
            None,
        ],
    )
    (rule,) = subtable_rules(format1, lookup=0, subtable=0)
    assert (rule.input, rule.backtrack, rule.lookahead) == (
        (s("a"), s("c")),
        (),
        (),
    )
    format2 = NS(
        LookupType=5,
        Format=2,
        Coverage=NS(glyphs=["a", "b"]),
        ClassDef=NS(classDefs={"a": 1, "b": 1, "c": 2}),
        SubClassSet=[
            None,
            NS(SubClassRule=[NS(Class=[2], SubstLookupRecord=[])]),
        ],
    )
    (rule,) = subtable_rules(format2, lookup=0, subtable=0)
    assert rule.input == (s("a", "b"), s("c"))
    format3 = NS(
        LookupType=5,
        Format=3,
        Coverage=[NS(glyphs=["a"]), NS(glyphs=["b", "c"])],
        SubstLookupRecord=[NS(SequenceIndex=1, LookupListIndex=0)],
    )
    (rule,) = subtable_rules(format3, lookup=0, subtable=0)
    assert rule.input == (s("a"), s("b", "c"))
    assert rule.actions == ((1, 0),)


def test_other_lookup_types_have_no_rules():
    model = model_of("feature calt { sub a by a.alt; } calt;")
    assert model.rules(0) == []


# ---- what a rule matches --------------------------------------------------


def test_a_rule_covers_one_with_the_same_match():
    one = rule_of(backtrack=[s("b")], input=[s("a")], lookahead=[s("c")])
    assert one.covers(one)


def test_a_rule_covers_one_with_narrower_sets():
    wide = rule_of(input=[s("a", "b")], lookahead=[s("c", "d")])
    narrow = rule_of(input=[s("a")], lookahead=[s("c")])
    assert wide.covers(narrow)
    assert not narrow.covers(wide)


def test_a_rule_with_less_around_it_covers_one_with_more():
    bare = rule_of(input=[s("a")])
    bounded = rule_of(backtrack=[s("b")], input=[s("a")], lookahead=[s("c")])
    assert bare.covers(bounded)
    assert not bounded.covers(bare)


def test_the_surroundings_are_compared_from_the_input_outwards():
    near = rule_of(backtrack=[s("b")], input=[s("a")])
    far = rule_of(backtrack=[s("b"), s("d")], input=[s("a")])
    assert near.covers(far)
    assert not rule_of(backtrack=[s("d")], input=[s("a")]).covers(far)


def test_rules_with_inputs_of_different_lengths_do_not_cover_each_other():
    one = rule_of(input=[s("a")])
    two = rule_of(input=[s("a"), s("b")])
    assert not one.covers(two) and not two.covers(one)


# ---- hidden rules --------------------------------------------------------


def hidden(fea: str):
    """(text, actions) of each hidden rule and of the rule hiding it."""
    return [
        ((r.text(), r.actions), (by.text(), by.actions))
        for r, by in model_of(fea).hidden_rules()
    ]


def test_a_rule_after_one_with_the_same_match_is_hidden():
    found = hidden(
        "lookup L {sub a by a.alt;} L;"
        "feature calt { ignore sub b a' c; sub b a' lookup L c; } calt;"
    )
    assert found == [(("b a' c", ((0, 0),)), ("b a' c", ()))]


def test_a_rule_after_a_more_general_one_is_hidden():
    found = hidden(
        "lookup L {sub a by a.alt;} L;"
        "feature calt { sub a' lookup L; sub b a' lookup L c; } calt;"
    )
    assert [(r[0], by[0]) for r, by in found] == [("b a' c", "a'")]


def test_a_rule_after_a_more_specific_one_is_not_hidden():
    found = hidden(
        "lookup L {sub a by a.alt;} L;"
        "feature calt { sub b a' lookup L c; sub a' lookup L; } calt;"
    )
    assert found == []


def test_a_rule_the_earlier_one_covers_only_in_part_is_not_hidden():
    found = hidden(
        "lookup L {sub a by a.alt;} L;"
        "feature calt { sub a' lookup L [b c]; sub a' lookup L [c d]; } calt;"
    )
    assert found == []


def test_the_same_match_in_two_lookups_is_not_hidden():
    found = hidden(
        "lookup L {sub a by a.alt;} L;"
        "lookup M { sub b a' lookup L c; } M;"
        "lookup N { sub b a' lookup L c; } N;"
        "feature calt { lookup M; lookup N; } calt;"
    )
    assert found == []


def test_a_lookup_no_feature_uses_is_not_looked_at():
    found = hidden(
        "lookup L {sub a by a.alt;} L;"
        "lookup M { sub b a' lookup L c; sub b a' lookup L c; } M;"
        "feature calt { sub a by a.alt; } calt;"
    )
    assert found == []


# ---- rules that claim one context ----------------------------------------

TWO = (
    "lookup L {sub a by a.alt;} L;"
    "lookup K {sub a by b.alt;} K;"
    "lookup J {sub a by a.alt;} J;"
)


def claims(fea: str):
    return [
        (first.where(), second.where())
        for first, second in model_of(fea).conflicting_rules()
    ]


def test_two_lookups_of_a_feature_with_one_match_and_different_results():
    found = claims(
        TWO + "lookup M { sub b a' lookup L c; } M;"
        "lookup N { sub b a' lookup K c; } N;"
        "feature calt { lookup M; lookup N; } calt;"
    )
    assert found == [("lookup 3 subtable 0 rule 0", "lookup 4 subtable 0 rule 0")]


def test_the_same_result_by_another_lookup_is_no_conflict():
    found = claims(
        TWO + "lookup M { sub b a' lookup L c; } M;"
        "lookup N { sub b a' lookup J c; } N;"
        "feature calt { lookup M; lookup N; } calt;"
    )
    assert found == []


def test_an_ignore_in_another_lookup_is_no_conflict():
    found = claims(
        TWO + "lookup M { sub b a' lookup L c; } M;"
        "lookup N { ignore sub b a' c; } N;"
        "feature calt { lookup M; lookup N; } calt;"
    )
    assert found == []


def test_another_match_is_no_conflict():
    found = claims(
        TWO + "lookup M { sub b a' lookup L c; } M;"
        "lookup N { sub b a' lookup K d; } N;"
        "feature calt { lookup M; lookup N; } calt;"
    )
    assert found == []


def test_lookups_of_two_features_are_not_compared():
    found = claims(
        TWO + "lookup M { sub b a' lookup L c; } M;"
        "lookup N { sub b a' lookup K c; } N;"
        "feature calt { lookup M; } calt;"
        "feature rclt { lookup N; } rclt;"
    )
    assert found == []


def test_one_lookup_does_not_conflict_with_itself():
    found = claims(
        TWO + "feature calt { sub b a' lookup L c; sub b a' lookup K c; } calt;"
    )
    assert found == []


# ---- reaching the lookups -----------------------------------------------


def test_the_features_know_their_lookups_and_the_lookups_they_call():
    model = model_of(
        "lookup L {sub a by a.alt;} L;"
        "lookup M { sub b a' lookup L c; } M;"
        "feature calt { lookup M; } calt;"
        "feature ss01 { sub b by b.alt; } ss01;"
    )
    assert model.features["calt"] == [1]
    assert model.reachable({"calt"}) == {0, 1}
    assert model.reachable({"ss01"}) == {2}
    assert model.reachable({"liga"}) == set()


def test_a_font_without_gsub_has_nothing():
    builder = FontBuilder(1000, isTTF=True)
    builder.setupGlyphOrder([".notdef"])
    model = GsubModel(builder.font)
    assert model.rules(0) == [] and model.features == {}
    assert model.hidden_rules() == [] and model.conflicting_rules() == []
