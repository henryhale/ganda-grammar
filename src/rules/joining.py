"""Word division: words the official orthography writes as one, and words it writes apart."""
from pathlib import Path

from .agreement import NOUNS
from .base import APOSTROPHES, Edit, looks_luganda

SRC = "Walusimbi, Empandiika y'Oluganda Entongole (2015)"
RULES = {
    "JOIN_NA_PRONOUN": ("na and a pronoun are one word: na bo → nabo, na nze → nange", f"{SRC}, §1.3(a)"),
    "JOIN_FIXED": ("words written as one: buli jjo → bulijjo, mpola mpola → mpolampola, eky'okulabirako → ekyokulabirako",
                   f"{SRC}, §1.3(n), (w), (z)"),
    "SPLIT_NE": ("narrative ne is a word of its own: nebagenda → ne bagenda", f"{SRC}, §1.3(b)"),
    "SPLIT_LOC": ("mu and ku are words of their own: mukibuga → mu kibuga", f"{SRC}, §1.3(d)"),
}

NA_PRONOUN = {"nze": "nange", "ggwe": "naawe", "ye": "naye", "ffe": "naffe", "mmwe": "nammwe", "bo": "nabo",
              "kyo": "nakyo", "byo": "nabyo", "zo": "nazo", "gwo": "nagwo", "gyo": "nagyo", "lyo": "nalyo",
              "bwo": "nabwo", "lwo": "nalwo"}
TWO_WORDS = {  # §1.3(n) bulijjo; §1.3(w) a word said twice is written once
    ("buli", "jjo"): "bulijjo", ("mpola", "mpola"): "mpolampola", ("katono", "tono"): "katonotono",
    ("ddala", "ddala"): "ddaladdala", ("wonna", "wonna"): "wonnawonna", ("okukola", "kola"): "okukolaakola",
    ("okutema", "tema"): "okutemaatema", ("okubuusa", "buusa"): "okubuusabuusa", ("okudaala", "daala"): "okudaaladaala",
}
# §1.3(z) nouns: ekyokulya 'food'. After a class 7/8 word, eky'okulya means 'for eating' (ekintu eky'okulya) and stays.
COMPOUNDS = {"eky": {"okulya", "okulabirako", "okulwanyisa", "okunywa", "okwegezaamu"},
             "eby": {"okulya", "okulabirako", "okulwanyisa", "okunywa", "enjigiriza", "obulamu", "obufuzi"}}
CLASS_7_8 = ("eki", "ebi", "eky", "eby", "ki", "bi")

VERBS = frozenset(line for line in Path(__file__).with_name("verbs.txt").read_text(encoding="utf-8").splitlines()
                  if line and not line.startswith("#"))
# ne + subject prefix + verb stem. Only prefixes whose noun forms start with a or o: n'abagamba sounds nabagamba, so a
# joined nebagamba can only be ne bagamba. Not ki, bi, li, zi, gi: nebikolwa sounds the same as n'ebikolwa.
NE_PREFIXES = ("ba", "tu", "mu", "gu", "ga", "lu", "ka", "bu", "ku")
# The listed nouns without their augment, as they follow mu and ku: ekibuga → kibuga, erinnya → linnya
BARE_NOUNS = frozenset("l" + n[2:] if n.startswith("er") else n[1:] for n in NOUNS)


def _join(first, word):
    return word[0].upper() + word[1:] if first[0].isupper() else word


def edits(text, toks):
    out = []
    for prev, a, b in zip([None] + toks, toks, toks[1:]):
        gap = text[a.end:b.start]
        if not a.text[1:].islower():
            continue
        key = (a.text.lower(), b.text)
        if gap.strip(" \t") == "" and gap and not (a.start and text[a.start - 1] in APOSTROPHES + "-"):
            if key[0] == "na" and b.text in NA_PRONOUN:
                out.append(Edit("JOIN_NA_PRONOUN", a.start, b.end, text[a.start:b.end], _join(a.text, NA_PRONOUN[b.text])))
            elif key in TWO_WORDS:
                out.append(Edit("JOIN_FIXED", a.start, b.end, text[a.start:b.end], _join(a.text, TWO_WORDS[key])))
        elif (len(gap) == 1 and gap in APOSTROPHES and b.text in COMPOUNDS.get(key[0], ())
              and not (prev and not text[prev.end:a.start].strip() and prev.text.lower().startswith(CLASS_7_8))):
            out.append(Edit("JOIN_FIXED", a.end, b.start, gap, ""))
    for t in toks:
        low = t.text[0].lower() + t.text[1:]
        whole = not t.start or not (text[t.start - 1].isalnum() or text[t.start - 1] in APOSTROPHES + "-")
        if not whole or not looks_luganda(low):
            continue
        if low[:2] == "ne" and low[2:4] in NE_PREFIXES and low[4:] in VERBS:
            out.append(Edit("SPLIT_NE", t.start, t.end, t.text, f"{t.text[:2]} {t.text[2:]}"))
        elif low[:2] in ("mu", "ku") and low[2:] in BARE_NOUNS and low[2:] not in VERBS:  # mulinnya 'you climb'
            out.append(Edit("SPLIT_LOC", t.start, t.end, t.text, f"{t.text[:2]} {t.text[2:]}"))
    return out
