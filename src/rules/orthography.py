"""Spelling rules of the official orthography, applied inside single lowercase Luganda words."""
import re
from pathlib import Path

from .base import APOSTROPHES, NC, Edit, looks_luganda

SRC = "Walusimbi, Empandiika y'Oluganda Entongole (2015)"
RULES = {
    "ORTH_L_R": ("r, not l, after e or i: ebilala → ebirala", f"{SRC}, §1.3"),
    "ORTH_VV_NC": ("single vowel before a nasal + consonant (mb, nd, nj, nz…): ensiimbi → ensimbi", f"{SRC}, §1.1.5, §1.1.7"),
    "ORTH_VV_CW": ("single vowel after a consonant + w or y, except ggw and ggy: omukyaala → omukyala", f"{SRC}, §1.1.6"),
    "ORTH_LENGTH": ("long vowels and long consonants as the dictionary spells them: gwanga → ggwanga, omwaana → omwana",
                    f"{SRC}, §1.1.1-1.1.2, §1.2; spellings from the FSI Luganda Basic Course glossary (1968)"),
}
# misspelling → spelling, built by scripts/build_spellings.py
SPELLINGS = dict(line.split("\t")[:2] for line in Path(__file__).with_name("spellings.tsv").read_text(encoding="utf-8").splitlines()
                 if line and not line.startswith("#"))

PATTERNS = (
    ("ORTH_L_R", re.compile(r"(?<=[ei])l"), lambda m: "r"),
    ("ORTH_VV_NC", re.compile(rf"([aeiou])\1(?={NC})"), lambda m: m[1]),
    # Not after ny (one letter, §1.2), ggw/ggy (§1.1.6) or ngw, and not before a final -wo/-yo/-ko/-mu, which
    # lengthens the vowel of a one-syllable verb (§1.1.8: vaawo, faako).
    ("ORTH_VV_CW", re.compile(r"(?<=[bcdfgjklmnprstvzŋ][wy])(?<![gn]g[wy])(?<!ny)([aeiou])\1(?!(?:wo|yo|ko|mu)$)"),
     lambda m: m[1]),
)


def edits(text, toks):
    out = []
    for t in toks:
        after_apostrophe = t.start and text[t.start - 1] in APOSTROPHES
        if not looks_luganda(t.text) or (after_apostrophe and t.start > 1 and text[t.start - 2].isupper()):  # M'okelo
            continue
        found = [Edit(rule, t.start + m.start(), t.start + m.end(), m[0], fix(m))
                 for rule, rx, fix in PATTERNS for m in rx.finditer(t.text)]
        if not found and t.text in SPELLINGS:  # a guide pattern, when one applies, is the better explanation
            found = [Edit("ORTH_LENGTH", t.start, t.end, t.text, SPELLINGS[t.text])]
        out += found
    return out
