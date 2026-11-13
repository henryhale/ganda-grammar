"""Build src/rules/spellings.tsv: misspellings of vowel length and doubled consonants, and their dictionary spelling.

    pdftotext -layout -f 364 -l 385 "FSI - Luganda Basic Course - Instructor and Student Text.pdf" glossary.txt
    python scripts/build_spellings.py glossary.txt English-Luganda_version_2_0.txt corpus.jsonl [...] > src/rules/spellings.tsv

1. The FSI Luganda Basic Course glossary (1968) gives each word in the standard spelling: long vowels and long
   consonants written double. Entries damaged by OCR are repaired when exactly one corpus word fits.
2. Each glossary word, its plural and its bare form (without the augment) is a correct spelling.
3. A misspelling is a correct spelling with one vowel or consonant lengthened or shortened, seen in the corpus at least
   twice and at least ten times less often, and not a word of its own: not in the English-Luganda dictionary, not a
   listed noun or verb, not English, not a minimal pair from the orthography guide, not in REVIEWED_OUT.
"""
import collections
import json
import re
import sys
from pathlib import Path

from ganda_grammar.rules.agreement import NOUNS  # the package installed: pip install -e .
from ganda_grammar.rules.joining import VERBS

# Both spellings are words (Walusimbi 2015, §1.1.1-1.1.2, §1.3): never correct one into the other
MINIMAL_PAIRS = "lega leega fuka fuuka siba siiba sima siima mala maala sera seera kola koola ekisero ekiseera".split()
# Words the guide spells that a variant could hit: the interrogatives of §1.3(r) (baluwa 'which ones', not bbaluwa 'letter')
GUIDE_WORDS = "kiruwa ziruwa biruwa aluwa baluwa galuwa".split()
# Found by reading the table: a word of its own, or not sure
REVIEWED_OUT = set("""ddaala ggye omuka obba okuweera okugala okusibula buuliri obuuliri okumaala muuka waala amakati
    entebbe ntebbe kusibula kubera emere""".split())
WORD = re.compile(r"[a-zŋ']+")
TOKEN = re.compile(r"[^\W\d_]+(?:['’][^\W\d_]+)*")  # as the rules tokenize, keeping elided words whole


def glossary(path, counts):
    """(word, class or perfect form, English meaning) from the FSI glossary text."""
    head = re.compile(r"^\s*(\(?[^\s(]+\)?)(?:\s*\(([^)]*)\))?\s{2,}(\S.*)$")
    by_len = collections.defaultdict(list)
    for w, n in counts.items():
        if n >= 3:
            by_len[len(w)].append(w)
    out = []
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        m = head.match(line)
        if not m or "LUGANDA" in line or m[1].lstrip("(").startswith("."):  # page headers, bound stems (.tegeevu)
            continue
        h = m[1].strip("()\"'·/").replace("·", "").replace("''", "")
        h = re.sub(r"^0", "o", h).replace("1", "l").lower().replace(".", "")
        if re.fullmatch(r"[a-zŋ']+", h):  # clean; OCR reads mw as 'row'
            if "row" in h and counts[h.replace("row", "mw")] > counts[h]:
                h = h.replace("row", "mw")
        elif re.search(r"[a-zŋ]{3}", h):  # damaged: junk is a wildcard; keep the repair only when one word fits
            pat = re.compile("".join(re.escape(ch) if WORD.fullmatch(ch) else "[a-zŋ]{0,2}" for ch in h)
                             .replace("row", "(?:mw|row)"))
            fits = sorted(((counts[w], w) for n in range(len(h) - 3, len(h) + 4) for w in by_len[n] if pat.fullmatch(w)),
                          reverse=True)
            if not fits or (len(fits) > 1 and fits[0][0] < 5 * fits[1][0]):
                continue
            h = fits[0][1]
        else:
            continue
        out.append((h, m[2] or "", re.split(r"\s{2,}", m[3])[0].strip()))
    return out


def plural(word, cls):
    """The plural where the FSI class makes it regular (ekyalo KI-BI → ebyalo), else None."""
    for sg, pl, k in (("eki", "ebi", "KI-BI"), ("eky", "eby", "KI-BI"), ("omu", "emi", "MU-MI"), ("omw", "emy", "MU-MI"),
                      ("aka", "obu", "KA-BU")):
        if cls.startswith(k) and word.startswith(sg):
            return pl + word[3:]


def forms(word, cls):
    """The word, its plural where the class makes it regular, and its bare form."""
    out = {word, plural(word, cls)} - {None}
    return out | {w[1:] for w in out if len(w) > 4 and w[0] in "aeo" and w[1] not in "aeiou"}


def variants(w):
    """w with one vowel or consonant made long or short (l, r, w, y are never doubled, §1.2)."""
    out, i = set(), 0
    while i < len(w):
        if w[i].isalpha() and w[i] not in "lrwy":
            if i + 1 < len(w) and w[i + 1] == w[i]:
                out.add(w[:i] + w[i + 1:])
                i += 2
                continue
            out.add(w[:i] + w[i] + w[i:])
        i += 1
    return out


def main(glossary_txt, dictionary_txt, *corpus):
    counts = collections.Counter()
    for path in corpus:
        for line in open(path, encoding="utf-8"):
            counts.update(TOKEN.findall(json.loads(line)["text"]))
    correct = {}
    for word, cls, _ in glossary(glossary_txt, counts):
        for f in forms(word, cls):
            correct[f] = word
    english = {w.strip().lower() for w in open("/usr/share/dict/words") if w.strip().isalpha()}
    dic = set(WORD.findall(Path(dictionary_txt).read_text(encoding="utf-8").lower())) - english
    real = (set(correct) | set(NOUNS) | VERBS | {"oku" + v for v in VERBS} | dic | {w[1:] for w in dic if w[:1] in "aeo"}
            | set(MINIMAL_PAIRS) | {"oku" + w for w in MINIMAL_PAIRS} | set(GUIDE_WORDS))
    rows = sorted({(v, g, counts[v], counts[g]) for g in correct if counts[g] >= 20 for v in variants(g)
                   if counts[v] >= 2 and counts[g] >= 10 * counts[v] and len(v) >= 4
                   and v not in real and v not in english and v not in REVIEWED_OUT}, key=lambda r: (-r[2], r[0]))
    print("# Misspellings of vowel length and doubled consonants (Walusimbi 2015, §1.1.1-1.1.2, §1.2), built by")
    print("# scripts/build_spellings.py from the FSI Luganda Basic Course glossary (1968) and corpus counts.")
    print("# misspelling\tspelling\tcount of the misspelling\tcount of the spelling")
    for v, g, nv, ng in rows:
        print(f"{v}\t{g}\t{nv}\t{ng}")


if __name__ == "__main__":
    main(*sys.argv[1:])
