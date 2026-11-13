import re

import pytest

import ganda_grammar as gg

# Every rule's description carries examples ("before → after"); each one is a test of that rule.
EXAMPLES = [(rule, before.strip(), after.strip())
            for rule, (description, _) in gg.RULES.items()
            for before, after in re.findall(r"([^:,;]+?) → ([^,;(]+)", description.split(": ", 1)[1])]


def test_every_rule_has_an_example_and_a_source():
    assert {rule for rule, _, _ in EXAMPLES} == set(gg.RULES)
    assert all(source for _, source in gg.RULES.values())


@pytest.mark.parametrize("rule, before, after", EXAMPLES, ids=[f"{r}:{b}" for r, b, _ in EXAMPLES])
def test_rule_example(rule, before, after):
    r = gg.correct(before)
    assert r.text == after
    assert [e.rule for e in r.edits] == [rule]


@pytest.mark.parametrize("before, after", [
    ("Abantu bangi na abantu abalala.", "Abantu bangi n'abantu abalala."),
    ("Yagenda mukibuga. Ebitabo kyange biri wano.", "Yagenda mu kibuga. Ebitabo byange biri wano."),
    ("Twagenda na bo.", "Twagenda nabo."),
])
def test_sentences(before, after):
    assert gg.correct(before).text == after


@pytest.mark.parametrize("text", [
    "",
    "The quick brown fox jumps over the lazy dog.",
    "Abantu bangi n'abantu abalala.",  # already right
    "Ogula wa emmere?",  # wa, "where?", is not elided
    "obulamu bwe obulungi",  # bwe is a possessive here, never elided
    "Twagenda e Kampala ne Entebbe.",
    "y'ekibuga ebirungi",  # after an apostrophe the adjective may belong to an earlier noun
])
def test_left_alone(text):
    assert gg.correct(text).edits == []


def test_edits_point_into_the_original():
    text = "Na abantu bagenda mukibuga. Ebitabo kyange biri wano, ebilala tebiriiwo."
    r = gg.correct(text)
    assert r.edits and all(text[e.start:e.end] == e.before for e in r.edits)
    assert all(a.end <= b.start for a, b in zip(r.edits, r.edits[1:]))


def test_long_text_is_corrected_like_its_sentences():
    para = "Na abantu bagenda mukibuga. Ebitabo kyange biri wano! Nebagenda na bo? "
    one = gg.correct(para)
    whole = gg.correct(para * 500)
    assert whole.text == one.text * 500
    assert len(whole.edits) == 500 * len(one.edits)
