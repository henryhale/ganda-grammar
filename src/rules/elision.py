"""Elision: a short word ending in a vowel loses it before a vowel-initial word, marked with an apostrophe."""
from .base import APOSTROPHES, Edit, looks_luganda

SRC = "Walusimbi, Empandiika y'Oluganda Entongole (2015)"
RULES = {
    "ELISION_NA": ("na/ne before a vowel: na abantu → n'abantu", f"{SRC}, §1.1.4, §1.3(b)"),
    "ELISION_NGA": ("nga before a vowel: nga ali → ng'ali", f"{SRC}, §1.3(c)"),
    "ELISION_POSS": ("a possessive before a vowel: kya okulya → ky'okulya", f"{SRC}, §1.3(g)"),
    "ELISION_REL": ("bwe, gye in set phrases: bwe atyo → bw'atyo, gye ali → gy'ali", f"{SRC}, §1.3(j)"),
}

# wa is left out: it is also "where?" and stays whole (Ogula wa emmere?, §1.3(r))
TRIGGERS = {"na": "ELISION_NA", "ne": "ELISION_NA", "nga": "ELISION_NGA"} | dict.fromkeys(
    "kya bya lya gwa gya za lwa twa bwa kwa ka ga ya ba".split(), "ELISION_POSS")
NOT_AFTER_POSSESSIVE = {"era", "ate", "oba"}  # conjunctions: a possessive before them ends a phrase
# Only set phrases: bwe, gye, we are also possessives (obulamu bwe, omwana we ali), and those are never elided (§1.3(s))
RELATIVE = {"bwe": {"atyo", "otyo", "etyo", "ati", "oti", "eti"}, "gye": {"ali", "oli"}}


def edits(text, toks):
    out = []
    for a, b in zip(toks, toks[1:]):
        rule = TRIGGERS.get(a.text.lower()) if a.text[1:].islower() else None
        if b.text in RELATIVE.get(a.text.lower(), ()) and a.text[1:].islower():
            rule = "ELISION_REL"
        if (rule and b.text[0] in "aeiou" and len(b.text) > 1 and looks_luganda(b.text)
                and a.end < b.start and not text[a.end:b.start].strip(" \t")
                and not (a.start and text[a.start - 1] in APOSTROPHES + "-")
                and not (rule == "ELISION_POSS" and b.text in NOT_AFTER_POSSESSIVE)):
            out.append(Edit(rule, a.end - 1, b.start, text[a.end - 1:b.start], "'"))
    return out
