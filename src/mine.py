"""Mine corrections: run the rules over a corpus and write one JSONL row per corrected sentence.

Row: {"source", "original", "corrected", "edits": [{"rule", "start", "end", "before", "after"}]}, with offsets
into "original". Repeated sentences are written once.
"""
import json
from collections import Counter
from dataclasses import asdict
from pathlib import Path

from .rules import correct
from .rules.base import sentences


def local_texts(paths, field="text"):
    """(source, text) from .txt files (whole file) and .jsonl files (each row's field); folders are searched."""
    for p in map(Path, paths):
        for f in sorted(x for x in p.rglob("*") if x.suffix in (".txt", ".jsonl")) if p.is_dir() else [p]:
            if f.suffix == ".jsonl":
                for line in f.open(encoding="utf-8"):
                    row = json.loads(line) if line.strip() else {}
                    if isinstance(row, dict) and isinstance(row.get(field), str):
                        yield str(f), row[field]
            else:
                yield str(f), f.read_text(encoding="utf-8", errors="replace")


def hf_texts(repo, split="train", field="text", exclude_sources=()):
    """(source, text) streamed from a Hugging Face dataset, skipping rows whose "source" is in exclude_sources."""
    try:
        from datasets import load_dataset
    except ImportError as e:
        raise ImportError("mining a Hugging Face dataset needs: pip install datasets") from e
    for row in load_dataset(repo, split=split, streaming=True):
        src = row.get("source")
        if src not in exclude_sources:
            yield f"{repo}:{src}" if src else repo, row[field]


def mine(texts, out, limit=None):
    """Write the corrected sentences of (source, text) pairs to out; return the edit count per rule."""
    # ponytail: one process; split the input across processes if a Kaggle session runs out of time
    seen, counts, rows = set(), Counter(), 0
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w", encoding="utf-8") as f:
        for source, text in texts:
            for s, e in sentences(text):
                sentence = text[s:e]
                if hash(sentence) in seen:
                    continue
                r = correct(sentence)
                if not r.edits:
                    continue
                seen.add(hash(sentence))
                row = {"source": source, "original": sentence, "corrected": r.text, "edits": [asdict(x) for x in r.edits]}
                f.write(json.dumps(row, ensure_ascii=False) + "\n")
                counts.update(x.rule for x in r.edits)
                rows += 1
                if rows == limit:
                    return counts
    return counts
