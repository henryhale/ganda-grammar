"""Rule engine. Each family module has RULES (id → description, source) and edits(text, tokens) → [Edit]."""
from . import agreement, elision, joining, orthography
from .base import Edit, Result, apply, luganda_tokens, sentences

FAMILIES = (agreement, elision, joining, orthography)  # where two edits overlap, the earlier family's wins
RULES = {rid: rule for f in FAMILIES for rid, rule in f.RULES.items()}


def correct(text):
    kept = []
    for start, end in sentences(text):
        toks = luganda_tokens(text, start, end)
        found = [e for f in FAMILIES for e in f.edits(text, toks)]
        ours = []  # edits stay inside their sentence, so overlaps are only checked within it
        for e in found:
            if all(e.end <= k.start or e.start >= k.end for k in ours):
                ours.append(e)
        kept += sorted(ours, key=lambda e: e.start)
    return Result(apply(text, kept), kept)


__all__ = ["RULES", "Edit", "Result", "correct"]
