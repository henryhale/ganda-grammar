"""Fix a dataset: write a corrected copy of every .txt and .jsonl file, or of a Hugging Face dataset.

.txt files are corrected line by line; .jsonl rows have their text fields corrected and every other field kept.
Lines and rows the rules leave alone are copied byte for byte. The input is never overwritten.

An optional log has one JSONL row per changed line or field: {"source", "line", "field", "original", "corrected",
"edits"}, with edit offsets into "original", enough to review a change or undo it.
"""
import json
import os
import time
from collections import Counter
from concurrent.futures import ProcessPoolExecutor
from dataclasses import astuple
from pathlib import Path

from .rules import correct

CHUNK = 2000  # lines a worker corrects at a time
SUFFIXES = (".txt", ".jsonl")


def _fix_line(kind, fields, line):
    """(the line to write, [(field, original, corrected, edits)] for each changed text)."""
    if kind == ".txt":
        r = correct(line)
        return (r.text, [(None, line, r.text, [astuple(e) for e in r.edits])]) if r.edits else (line, [])
    try:
        row = json.loads(line) if line.strip() else None
    except json.JSONDecodeError:
        return line, []  # not JSON: copied as it is
    if not isinstance(row, dict):
        return line, []
    changes = []
    for f in fields:
        if isinstance(row.get(f), str):
            r = correct(row[f])
            if r.edits:
                changes.append((f, row[f], r.text, [astuple(e) for e in r.edits]))
                row[f] = r.text
    if not changes:
        return line, []
    end = "\r\n" if line.endswith("\r\n") else "\n" if line.endswith("\n") else ""
    return json.dumps(row, ensure_ascii=False) + end, changes


def _fix_chunk(args):
    kind, fields, lines = args
    return [_fix_line(kind, fields, line) for line in lines]


def _chunks(lines, kind, fields):
    chunk = []
    for line in lines:
        chunk.append(line)
        if len(chunk) == CHUNK:
            yield kind, fields, chunk
            chunk = []
    if chunk:
        yield kind, fields, chunk


def files(paths, out):
    """(input, output) for each .txt and .jsonl file; a folder's files keep their place under out."""
    out = Path(out)
    for p in map(Path, paths):
        if p.is_dir():
            for f in sorted(x for x in p.rglob("*") if x.is_file() and x.suffix in SUFFIXES):
                yield f, out / f.relative_to(p)
        elif p.suffix in SUFFIXES:
            yield p, out / p.name
        else:
            raise ValueError(f"{p}: not a .txt or .jsonl file, nor a folder")


class Fixer:
    def __init__(self, fields=("text",), workers=None, log=None):
        self.fields = tuple(fields)
        self.workers = workers or os.cpu_count() or 1
        self.counts = Counter()  # edits per rule
        self.seen = self.changed = 0
        self.log = open(log, "w", encoding="utf-8") if log else None
        self.pool = ProcessPoolExecutor(self.workers) if self.workers > 1 else None

    def close(self):
        if self.pool:
            self.pool.shutdown()
        if self.log:
            self.log.close()

    def run(self, source, lines, write, kind):
        """Correct lines (an iterable) of one source, calling write for each output line in order."""
        chunks = _chunks(lines, kind, self.fields)
        results = self.pool.map(_fix_chunk, chunks) if self.pool else map(_fix_chunk, chunks)
        n = 0
        for chunk in results:
            for line, changes in chunk:
                n += 1
                write(line)
                self.changed += bool(changes)
                for field, before, after, edits in changes:
                    self.counts.update(e[0] for e in edits)
                    if self.log:
                        self.log.write(json.dumps({
                            "source": source, "line": n, "field": field, "original": before, "corrected": after,
                            "edits": [dict(zip(("rule", "start", "end", "before", "after"), e)) for e in edits],
                        }, ensure_ascii=False) + "\n")
        self.seen += n

    def fix_file(self, src, dst):
        if dst.resolve() == src.resolve():
            raise ValueError(f"{src}: the output would overwrite the input")
        dst.parent.mkdir(parents=True, exist_ok=True)
        with src.open(encoding="utf-8", errors="replace", newline="") as fin, \
                dst.open("w", encoding="utf-8", newline="") as fout:
            self.run(str(src), fin, fout.write, src.suffix)

    def fix_hf(self, repo, out, split="train"):
        """Write a Hugging Face dataset to out as JSONL, with its text fields corrected."""
        try:
            from datasets import load_dataset
        except ImportError as e:
            raise ImportError("fixing a Hugging Face dataset needs: pip install datasets") from e
        out = Path(out)
        out.parent.mkdir(parents=True, exist_ok=True)
        rows = (json.dumps(row, ensure_ascii=False, default=str) + "\n"
                for row in load_dataset(repo, split=split, streaming=True))
        with out.open("w", encoding="utf-8") as fout:
            self.run(f"{repo}:{split}", rows, fout.write, ".jsonl")


def fix(paths, out, fields=("text",), hf=None, split="train", workers=None, log=None):
    """Write corrected copies of paths (files or folders) under out, and of the dataset hf; return the Fixer's totals."""
    fixer = Fixer(fields, workers, log)
    start = time.time()
    try:
        for src, dst in files(paths, out):
            fixer.fix_file(src, dst)
        if hf:
            fixer.fix_hf(hf, Path(out) / f"{hf.replace('/', '__')}.{split}.jsonl", split)
    finally:
        fixer.close()
    fixer.seconds = time.time() - start
    return fixer
