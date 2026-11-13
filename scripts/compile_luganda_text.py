"""Compile the Luganda text under a folder into chunked .txt files, the local input of notebooks/build_dictionary.ipynb.

    python scripts/compile_luganda_text.py ../ ../luganda-dictionary-inputs

Reads every .txt, .jsonl and .html file under the folder (except SKIP) and keeps the sentences that read as Luganda (the
ganda_grammar sentence check). Files are taken cleanest first (largest share of Luganda sentences); a file that is mostly
a copy of one already taken (DUPLICATE of its 5-word sequences seen before, like a re-OCR of the same book) is skipped,
and every sentence is written once. texts/luganda_text_NNN.txt get one paragraph a line, CHUNK_BYTES at most each;
texts/manifest.tsv says what each file gave, or which files were skipped as copies. sources/ gets the text layers of the
PDFs the notebook reads (pdftotext -layout), so it needs neither the PDFs nor poppler.
"""
import hashlib
import json
import re
import shutil
import subprocess
import sys
from html.parser import HTMLParser
from pathlib import Path

from ganda_grammar.rules.base import luganda_tokens, sentences

CHUNK_BYTES = 10_000_000
DUPLICATE = 0.5  # share of a file's 5-word sequences already written that makes it a copy
SKIP = {  # not Luganda (machine-translation and tokenizer experiments), or derived from the files kept here
    "minimind", "cross-lingual-group-tokenizer", "fastest-efficient-tokenizer", "brain.en", "grouptok", "grouptok-paper",
    "ganda-grammar", "luganda-dictionary-inputs", ".git", ".venv", "venv", "node_modules", "site-packages", "__pycache__",
    ".cache", ".ipynb_checkpoints",
}
RESOURCES = "gandalm/resources"
PDF_TEXT = {  # file in sources/: (PDF under RESOURCES, pdftotext page options)
    "fsi_glossary_layout.txt": ("FSI - Luganda Basic Course - Instructor and Student Text.pdf", ["-f", "364", "-l", "385"]),
    "english_luganda_layout.txt": ("English-Luganda_version_2_0.pdf", []),
}
FSI_TEXT = "FSI - Luganda Basic Course - Instructor and Student Text.txt"  # its lesson glossaries


class VisibleText(HTMLParser):  # the text of a page, without scripts and styles
    def __init__(self):
        super().__init__()
        self.parts, self.hidden = [], 0

    def handle_starttag(self, tag, attrs):
        self.hidden += tag in ("script", "style")

    def handle_endtag(self, tag):
        if tag in ("script", "style") and self.hidden:
            self.hidden -= 1

    def handle_data(self, data):
        if not self.hidden:
            self.parts.append(data)


def strings(x):  # every string in a JSON row: text fields, chat turns
    if isinstance(x, str):
        yield x
    elif isinstance(x, dict):
        for v in x.values():
            yield from strings(v)
    elif isinstance(x, list):
        for v in x:
            yield from strings(v)


def paragraphs(path):
    if path.suffix == ".jsonl":
        for line in path.open(encoding="utf-8", errors="replace"):
            try:
                yield from strings(json.loads(line))
            except ValueError:
                yield line
    elif path.suffix == ".html":
        page = VisibleText()
        page.feed(path.read_text(encoding="utf-8", errors="replace"))
        yield from "".join(page.parts).splitlines()
    else:
        yield from path.open(encoding="utf-8", errors="replace")


def files(root):
    for p in sorted(root.rglob("*")):
        if p.suffix in (".txt", ".jsonl", ".html") and p.is_file() and not SKIP.intersection(p.relative_to(root).parts):
            yield p


def luganda_paragraphs(path):
    """The file's paragraphs as lists of their Luganda sentences, and the share of its sentences that are Luganda."""
    out, total = [], 0
    for para in paragraphs(path):
        keep = []
        for s, e in sentences(para):
            total += 1
            if luganda_tokens(para, s, e):
                keep.append(re.sub(r"\s+", " ", para[s:e]).strip())
        if keep:
            out.append(keep)
    return out, sum(map(len, out)) / total if total else 0


def shingles(paras):
    words = " ".join(" ".join(p) for p in paras).lower().split()
    return {hash(tuple(words[i:i + 5])) for i in range(len(words) - 4)}


def main(root, out):
    root, out = Path(root).resolve(), Path(out)
    texts = out / "texts"
    texts.mkdir(parents=True, exist_ok=True)
    found = [(path, *luganda_paragraphs(path)) for path in files(root)]
    seen, written, manifest, n, size = set(), set(), [], 0, CHUNK_BYTES
    chunk = None
    for path, paras, share in sorted(found, key=lambda f: -f[2]):  # cleanest copy first
        if not paras:
            continue
        own = shingles(paras)
        if own and len(own & written) >= DUPLICATE * len(own):
            manifest.append((str(path.relative_to(root)), "copy", "skipped"))
            continue
        written |= own
        kept = words = 0
        for para in paras:
            keep = []
            for sent in para:
                key = hashlib.blake2b(sent.lower().encode(), digest_size=8).digest()
                if key not in seen:
                    seen.add(key)
                    keep.append(sent)
            if not keep:
                continue
            line = " ".join(keep) + "\n"
            if size + len(line.encode()) > CHUNK_BYTES:
                if chunk:
                    chunk.close()
                n += 1
                chunk, size = (texts / f"luganda_text_{n:03d}.txt").open("w", encoding="utf-8"), 0
            chunk.write(line)
            size += len(line.encode())
            kept += len(keep)
            words += len(line.split())
        if kept:
            manifest.append((str(path.relative_to(root)), kept, words))
    if chunk:
        chunk.close()
    with (texts / "manifest.tsv").open("w", encoding="utf-8") as f:
        f.write("file\tsentences\twords\n")
        f.writelines(f"{p}\t{k}\t{w}\n" for p, k, w in manifest)

    sources = out / "sources"
    sources.mkdir(exist_ok=True)
    for name, (pdf, pages) in PDF_TEXT.items():
        subprocess.run(["pdftotext", "-layout", *pages, str(root / RESOURCES / pdf), str(sources / name)], check=True)
    shutil.copy(root / RESOURCES / FSI_TEXT, sources / "fsi_course.txt")

    taken = [m for m in manifest if m[1] != "copy"]
    print(f"{len(taken)} files, {sum(k for _, k, _ in taken):,} sentences, {sum(w for *_, w in taken):,} words → {n} chunks "
          f"in {texts}; {len(manifest) - len(taken)} files skipped as copies")


if __name__ == "__main__":
    main(*sys.argv[1:])
