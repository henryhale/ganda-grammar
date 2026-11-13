"""Clean the Luganda dictionary: drop duplicates, merge near-duplicates, repair broken entries. Writes a new copy.

    python scripts/clean_dictionary.py data/luganda_dictionary.jsonl
    → data/luganda_dictionary_clean.jsonl, data/luganda_dictionary_clean.tsv, and
      data/luganda_dictionary_clean.changes.tsv (one row per change, to review)

No entry is dropped except by merging it into the entry it duplicates; its sources, meanings and spellings are kept.
In order:

1. Exact duplicates: headwords equal after Unicode normalisation, one apostrophe, single spaces and lowercase.
2. Glued rows of the English-Luganda list: its PDF columns were cut so that a headword sometimes carries the next
   rows (`decide okusalawo decorate okutona` = decide → okusalawo, decorate → okutona). Split at the English words.
3. Meanings: drop FSI cross-references (`see under .wanga`) and Luganda that spilled into the English
   (`dinner eky'eggulo` → dinner), move FSI perfect forms (`(.liisizza) feed`) to `perfect`, close brackets, and
   drop repeated meanings.
4. Split words: `oku kyusa` → okukyusa, and any phrase whose spaces-removed form is itself an entry, except
   possessives (`a maanyi`, powerful, is not amaanyi, strength).
5. Listed misspellings (src/rules/spellings.tsv): merged into their spelling, kept in `variants`.
6. Bare nouns and infinitives (kitabo, kutendeka) that only repeat the full form (ekitabo, okutendeka): merged into it,
   kept in `bare` with its own count in `bare_count`. Not when the bare form is more frequent or means something else (kye, mu, musiru).
"""
import collections
import json
import re
import sys
import unicodedata
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
try:
    from ganda_grammar.rules.base import SHAPE
except ImportError:  # not installed: load src/ as ganda_grammar
    import importlib.util
    spec = importlib.util.spec_from_file_location("ganda_grammar", REPO / "src" / "__init__.py",
                                                  submodule_search_locations=[str(REPO / "src")])
    module = importlib.util.module_from_spec(spec)
    sys.modules["ganda_grammar"] = module
    spec.loader.exec_module(module)
    from ganda_grammar.rules.base import SHAPE

FIELDS = ["headword", "pos", "noun_class", "plural", "english", "sources", "variants", "count", "attested", "bare",
          "bare_count", "perfect"]
LISTS = {"english", "sources", "variants"}
APOSTROPHE = re.compile("[’ʼ‘`]")
ELIDED = re.compile(r"^([a-z]{1,3})'([a-z]+)$")  # eky'omugaso, n'abantu
NOUN_PREFIX = re.compile(r"^(oku|okw|omu|omw|aba|eki|eky|ebi|eby|obu|obw|olu|olw|ama|emi|emy|aka|enn|emm)")
CROSS_REF = re.compile(r"^see under \.")
PERFECT = re.compile(r"^\((\.[^)]*)\)\s*")  # FSI: (.liisizza) feed


def norm(s):
    s = APOSTROPHE.sub("'", unicodedata.normalize("NFC", s))
    return " ".join(s.split()).lower()


class Cleaner:
    def __init__(self, rows):
        self.log = []
        self.D = {}
        for r in rows:
            r = {f: r.get(f, [] if f in LISTS else None) for f in FIELDS}
            hw = norm(r["headword"])
            if hw in self.D:
                self.merge(r, self.D[hw], "duplicate")
            else:
                if hw != r["headword"]:
                    self.change("normalised", r["headword"], hw)
                r["headword"] = hw
                self.D[hw] = r
        # every word used in a meaning, to tell English from Luganda
        self.english_words = collections.Counter(t for r in self.D.values() for e in r["english"]
                                                 for t in re.findall(r"[a-z]+", e.lower()))
        self.luganda_words = {h for h, r in self.D.items() if " " not in h and r["attested"]}

    def change(self, kind, before, after, note=""):
        self.log.append((kind, before, after, note))

    def merge(self, src, dst, kind, keep_as=None, before=None):
        """Fold src into dst. keep_as: the field ("variants" or "bare") that remembers src's headword."""
        for f in ("sources", "variants"):
            dst[f] += [x for x in src[f] if x not in dst[f]]
        self.add_meanings(dst, src["english"])
        for f in ("pos", "noun_class", "plural", "count", "bare", "bare_count", "perfect"):
            if dst[f] is None:
                dst[f] = src[f]
        if keep_as == "variants" and src["headword"] not in dst["variants"]:
            dst["variants"].append(src["headword"])
        elif keep_as == "bare":
            dst["bare"], dst["bare_count"] = src["headword"], src["count"]
        self.change(kind, before or src["headword"], dst["headword"])

    @staticmethod
    def add_meanings(r, meanings):
        seen = {re.sub(r"\W+", " ", e.lower()).strip() for e in r["english"]}
        for e in meanings:
            k = re.sub(r"\W+", " ", e.lower()).strip()
            if k and k not in seen:
                seen.add(k)
                r["english"].append(e)

    def is_english(self, t):
        return self.english_words[t] >= 1 and t not in self.luganda_words and "'" not in t

    def is_luganda(self, t):
        t = t.strip("(),.;:!?").lower()
        m = ELIDED.match(t)
        if m:
            return m.group(1) not in ("o", "i") and SHAPE.fullmatch(m.group(2)) is not None  # not o'clock, i'm
        return (SHAPE.fullmatch(t) is not None and self.english_words[t] == 0
                and (t in self.luganda_words or NOUN_PREFIX.match(t) is not None))

    def put(self, r, kind):
        """Add a new or rebuilt entry, merging it into an existing one with its headword."""
        if r["headword"] in self.D:
            self.merge(r, self.D[r["headword"]], kind)
        else:
            self.D[r["headword"]] = r

    # 2
    def split_glued(self):
        for hw in [h for h, r in self.D.items() if r["sources"] == ["english-luganda-list"] and " " in h]:
            toks = hw.split()
            if not any(self.is_english(t) for t in toks):
                continue
            r = self.D.pop(hw)
            runs = [[False, []]]  # [english?, tokens]
            for t in toks:
                e = self.is_english(t)
                if runs[-1][1] and runs[-1][0] != e:
                    runs.append([e, []])
                runs[-1][0] = e
                runs[-1][1].append(t)
            meanings = list(r["english"])
            pairs = []  # (luganda, [english])
            for i, (eng, words) in enumerate(runs):
                if eng and i == 0:  # the end of the row's own meaning: excuse + "me owange" = excuse me
                    tail = " ".join(words)
                    meanings = [m for m in meanings if not all(self.is_luganda(w) for w in m.split())]
                    meanings = meanings[:-1] + [f"{meanings[-1]} {tail}"] if meanings else [tail]
                elif not eng:
                    pairs.append((" ".join(words), meanings if not pairs else [" ".join(runs[i - 1][1])]))
            # a trailing English run starts the row after this one; its Luganda is lost
            parts = []
            for j, (lg, en) in enumerate(pairs):
                new = {f: ([] if f in LISTS else None) for f in FIELDS}
                new.update(headword=lg, sources=["english-luganda-list"], english=list(en))
                if j == 0:
                    new.update(pos=r["pos"], noun_class=r["noun_class"], plural=r["plural"], variants=r["variants"])
                self.put(new, "split-glued (merged)")
                parts.append(f"{lg} = {'; '.join(en)}")
            self.change("split-glued", hw, " | ".join(parts))

    # 3
    def clean_meanings(self):
        for r in self.D.values():
            out = []
            for e in r["english"]:
                before = e
                e = e.strip().lstrip("#").strip()
                m = PERFECT.match(e)
                if m:
                    r["perfect"] = r["perfect"] or m.group(1).rstrip("·").strip()
                    e = e[m.end():].strip()
                if CROSS_REF.match(e):
                    e = ""
                toks = e.split()
                k = len(toks)
                while k > 0 and self.is_luganda(toks[k - 1]):
                    k -= 1
                e = " ".join(toks[:k])
                if e.count("(") > e.count(")"):
                    e += ")"
                if e != before:
                    self.change("meaning", r["headword"], e, before)
                if e:
                    out.append(e)
            r["english"] = []
            self.add_meanings(r, out)

    # 4
    def join_split_words(self):
        for hw in [h for h in self.D if " " in h]:
            if hw not in self.D:
                continue
            joined = hw.replace(" ", "")
            if hw.startswith("a "):  # a possessive, not a split word: a maanyi (powerful) is not amaanyi
                continue
            if hw.startswith("oku ") or joined in self.D:
                r = self.D.pop(hw)
                r["headword"] = joined
                if joined in self.D:
                    self.merge(r, self.D[joined], "split-word", before=hw)
                else:
                    self.D[joined] = r
                    self.change("split-word", hw, joined)

    # 5
    def merge_misspellings(self, spellings):
        for bad, good in spellings.items():
            if bad in self.D and good in self.D:
                self.merge(self.D.pop(bad), self.D[good], "misspelling", keep_as="variants")

    # 6
    def merge_bare_forms(self):
        for hw in [h for h in self.D if " " not in h and len(h) >= 4 and h[0] not in "aeiou"]:
            for aug in "aeo":
                full = self.D.get(aug + hw)
                if full is None or hw not in self.D:
                    continue
                bare = self.D[hw]
                if bare["pos"] not in (None, full["pos"]) or (bare["count"] or 0) > (full["count"] or 0):
                    continue
                b = {e.lower() for e in bare["english"]}
                if b and not b & {e.lower() for e in full["english"]}:
                    continue
                self.merge(self.D.pop(hw), full, "bare-form", keep_as="bare")
                break

    def rows(self):
        for r in sorted(self.D.values(), key=lambda r: r["headword"]):
            r["attested"] = (r["count"] or 0) >= 2 or len(r["sources"]) >= 2
            yield r


def main(path="data/luganda_dictionary.jsonl", out=None):
    path = Path(path)
    out = Path(out) if out else path.with_name("luganda_dictionary_clean.jsonl")
    rows = [json.loads(line) for line in path.open(encoding="utf-8") if line.strip()]
    spellings = dict(line.rstrip("\n").split("\t")[:2]
                     for line in (REPO / "src" / "rules" / "spellings.tsv").open(encoding="utf-8")
                     if line.strip() and not line.startswith("#"))

    c = Cleaner(rows)
    c.split_glued()
    c.clean_meanings()
    c.join_split_words()
    c.merge_misspellings(spellings)
    c.merge_bare_forms()
    clean = list(c.rows())

    with out.open("w", encoding="utf-8") as f:
        for r in clean:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    with out.with_suffix(".tsv").open("w", encoding="utf-8") as f:
        f.write("\t".join(FIELDS) + "\n")
        for r in clean:
            f.write("\t".join("; ".join(x.replace(";", ",") for x in r[k]) if k in LISTS
                              else "" if r[k] is None else str(r[k]) for k in FIELDS) + "\n")
    log = out.with_suffix(".changes.tsv")
    with log.open("w", encoding="utf-8") as f:
        f.write("change\tbefore\tafter\tnote\n")
        for row in c.log:
            f.write("\t".join(str(x).replace("\t", " ") for x in row) + "\n")

    kinds = collections.Counter(k for k, *_ in c.log)
    print(f"{len(rows):,} entries → {len(clean):,} ({sum(r['attested'] for r in clean):,} attested)")
    for k, n in kinds.most_common():
        print(f"  {k:22} {n:,}")
    print(f"wrote {out}, {out.with_suffix('.tsv')}, {log}")


if __name__ == "__main__":
    main(*sys.argv[1:])
