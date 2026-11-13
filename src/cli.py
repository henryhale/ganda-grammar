"""ganda-grammar correct: correct Luganda text. ganda-grammar fix: write a corrected copy of a dataset.
ganda-grammar mine: collect corrections from a corpus."""
import argparse
import json
import sys
from dataclasses import asdict
from itertools import chain


def main(argv=None):
    ap = argparse.ArgumentParser(prog="ganda-grammar", description=__doc__)
    sub = ap.add_subparsers(dest="cmd", required=True)

    c = sub.add_parser("correct", help="correct text given as an argument, or on stdin")
    c.add_argument("text", nargs="?")
    c.add_argument("--json", action="store_true", help="print the corrected text and its edits as JSON")

    f = sub.add_parser("fix", help="write a corrected copy of .txt and .jsonl files, folders, or a Hugging Face dataset")
    f.add_argument("paths", nargs="*", help=".txt and .jsonl files, or folders of them")
    f.add_argument("-o", "--out", required=True, help="folder for the corrected copies (a folder's files keep their place)")
    f.add_argument("--hf", help="also correct this Hugging Face dataset, written to OUT as JSONL")
    f.add_argument("--split", default="train")
    f.add_argument("--field", action="append", metavar="FIELD",
                   help="text field of .jsonl rows and dataset rows to correct (repeatable; default: text)")
    f.add_argument("--workers", type=int, help="processes to use (default: one per CPU)")
    f.add_argument("--log", help="also write one JSONL row per changed line or field, with its edits")

    m = sub.add_parser("mine", help="run the rules over a corpus, write one JSONL row per corrected sentence")
    m.add_argument("paths", nargs="*", help=".txt and .jsonl files, or folders of them")
    m.add_argument("--hf", help="also stream this Hugging Face dataset, e.g. henryhale/luganda-pretrain2")
    m.add_argument("--split", default="train")
    m.add_argument("--exclude-source", action="append", default=[], metavar="SOURCE",
                   help="skip dataset rows whose source column is SOURCE (repeatable)")
    m.add_argument("--field", default="text", help="text field of .jsonl rows and dataset rows (default: text)")
    m.add_argument("--limit", type=int, help="stop after this many corrected sentences")
    m.add_argument("-o", "--out", default="corrections/corrections.jsonl",
                   help="output file; keep it in corrections/, the folder that is published (default: %(default)s)")

    a = ap.parse_args(argv)
    if a.cmd == "correct":
        from . import correct

        text = sys.stdin.read() if a.text is None else a.text
        r = correct(text)
        if a.json:
            print(json.dumps({"text": r.text, "edits": [asdict(e) for e in r.edits]}, ensure_ascii=False, indent=2))
        else:
            print(r.text, end="" if a.text is None else "\n")
    elif a.cmd == "fix":
        from .fix import fix

        if not a.paths and not a.hf:
            ap.error("fix needs paths, --hf, or both")
        try:
            r = fix(a.paths, a.out, a.field or ["text"], a.hf, a.split, a.workers, a.log)
        except ValueError as e:
            ap.error(str(e))
        for rule, n in r.counts.most_common():
            print(f"{rule}\t{n}")
        print(f"{r.changed:,} of {r.seen:,} lines changed in {r.seconds:.1f}s; wrote {a.out}", file=sys.stderr)
    else:
        from .mine import hf_texts, local_texts, mine

        if not a.paths and not a.hf:
            ap.error("mine needs paths, --hf, or both")
        texts = chain(local_texts(a.paths, a.field),
                      hf_texts(a.hf, a.split, a.field, set(a.exclude_source)) if a.hf else ())
        for rule, n in mine(texts, a.out, a.limit).most_common():
            print(f"{rule}\t{n}")
        print(f"wrote {a.out}", file=sys.stderr)


if __name__ == "__main__":
    main()
