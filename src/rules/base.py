"""What every rule family shares: edits, sentences, tokens, and the check that a word or sentence is Luganda."""
import re
from dataclasses import dataclass, field
from typing import NamedTuple

APOSTROPHES = "'’ʼ‘"


@dataclass(frozen=True)
class Edit:
    rule: str  # rule id, see RULES; "MODEL" for the model engine
    start: int  # character offsets into the original text
    end: int
    before: str
    after: str


@dataclass
class Result:
    text: str
    edits: list = field(default_factory=list)


class Token(NamedTuple):
    start: int
    end: int
    text: str


def apply(text, edits):
    """Apply non-overlapping edits, sorted by start."""
    out, pos = [], 0
    for e in edits:
        out += [text[pos:e.start], e.after]
        pos = e.end
    return "".join(out) + text[pos:]


SENTENCE = re.compile(r"[^\s.!?][^.!?\n]*[.!?]*")
WORD = re.compile(r"[^\W\d_]+")


def sentences(text):
    """(start, end) of each sentence, without surrounding whitespace."""
    for m in SENTENCE.finditer(text):
        yield m.start(), m.start() + len(m[0].rstrip())


# A Luganda word is a run of syllables (consonant cluster + short or long vowel) and ends in a vowel. Only the first
# syllable may start with a vowel: two different vowels in a row (believe, milieu) aren't written in Luganda.
GEMINATE = "(?:bb|cc|dd|ff|gg|jj|kk|mm|nn|pp|ss|tt|vv|zz|ŋŋ)"
NC = "(?:m[bpfv]|n[dtkzfgjsvc])"  # nasal + consonant (Walusimbi 2015, §1.1.5, §1.1.7)
ONSET = f"(?:(?:nny|ny|{GEMINATE}|{NC}|[bcdfgjklmnprstvzŋ])[wy]?|[wy])"
VOWEL = "(?:aa|ee|ii|oo|uu|[aeiou])"
SHAPE = re.compile(f"{VOWEL}?(?:{ONSET}{VOWEL})*")

# English words with a Luganda shape that a spelling rule would change, found in henryhale/luganda-pretrain2
ENGLISH = frozenset("""
mobile believe file milieu twee failure release tile mile missile silence angelo vile delaware relative envelope
bela relate elite ila accelerate delete jubilee milo bile simile deliverance nile eliminate timeline compile militia
relieve pile consuelo lilongwe delegate reliance elaborate facilitate pele voile leila utilize tensile silica cilia
dilute vila diligence affiliate mobilize deliberate relevance pipeline delicate fossilize silicate facile revile
sweetie silo reconcile futile dilemma vigilante elusive gentile defile resilience gila felice guile relocate
vigilance automobile delude antelope baseline docile vuvuzela volatile virile filipino smile while
""".split())

# Function words of languages that share Luganda's word shape (Swahili, Chichewa, Portuguese/Spanish) and of English,
# leaving out the ones that are also Luganda words (a, be, so, we)
FOREIGN = frozenset("""
ni katika kwamba lakini hii sana pia kuwa ambao ambaye hiyo wewe mimi yeye huo hilo wao sisi nini
anthu kuti ndi ndipo ine iye que ele ela dele pela pelo para uma com los las del por
the and of is are was were to in on at for with from by this that these those it its as an or not no have has had
will would can could which who what when where there here their they them he his she her you your our also only but if
than then into about after before
""".split())


def looks_luganda(word):
    """Lowercase, made of Luganda syllables, not a known English word, and not 30+ letters of glued-together text."""
    return word.islower() and len(word) <= 30 and word not in ENGLISH and SHAPE.fullmatch(word) is not None


def luganda_tokens(text, start, end):
    """The words of text[start:end], or [] when the sentence doesn't read as Luganda, so no rule touches it."""
    # ponytail: word shape + foreign function words; add a language-ID model (fastText lid.176) if mixed text gets through
    toks = [Token(m.start(), m.end(), m[0]) for m in WORD.finditer(text, start, end)]
    # an elided word before its apostrophe (the ky of ky'okulya) isn't a word to judge
    low = [t.text for t in toks if t.text.islower() and text[t.end:t.end + 1] not in tuple(APOSTROPHES)]
    if not low or FOREIGN.intersection(low) or sum(map(looks_luganda, low)) < 0.6 * len(low):
        return []
    return toks
