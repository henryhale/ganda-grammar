"""Write a self-contained copy of a notebook, carrying ganda-grammar in its first cells.

    python scripts/bundle_notebook.py notebooks/build_wordlist.ipynb
    → notebooks/build_wordlist_selfcontained.ipynb (or name the output as a second argument)

The copy starts with one %%writefile cell per file of the package (src/, written as ganda_grammar/, with its data files)
and of scripts/, all under BUNDLE, which goes first on sys.path. Its own cells then find BUNDLE defined, so the notebook
runs with no copy of this repository attached and nothing to install: the rules engine is pure Python.
"""
import json
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
BUNDLE = "/tmp/ganda_grammar_bundle"
PARTS = {"src": "ganda_grammar", "scripts": "scripts"}  # repository folder → folder in the bundle


def files():
    for folder, target in PARTS.items():
        for p in sorted((REPO / folder).rglob("*")):
            if p.is_file() and "__pycache__" not in p.parts:
                yield p, f"{BUNDLE}/{target}/{p.relative_to(REPO / folder).as_posix()}"


def cell(kind, text, n):
    c = {"cell_type": kind, "id": f"bundle{n:02d}", "metadata": {}, "source": text.splitlines(keepends=True)}
    if kind == "code":
        c |= {"execution_count": None, "outputs": []}
    return c


def version():
    try:
        rev = subprocess.run(["git", "-C", str(REPO), "describe", "--always", "--dirty"], capture_output=True, text=True,
                             check=True).stdout.strip()
        return f"commit {rev}"
    except (OSError, subprocess.CalledProcessError):
        return "no git revision"


def main(source, out=None):
    source = Path(source)
    out = Path(out) if out else source.with_name(source.stem + "_selfcontained.ipynb")
    nb = json.loads(source.read_text(encoding="utf-8"))
    bundled = list(files())
    folders = sorted({str(Path(target).parent) for _, target in bundled})
    head = [
        cell("markdown", f"""## ganda-grammar, carried by this notebook

This copy of `{source.name}` carries ganda-grammar ({version()}). The cells below write its package (`src/`, as
`ganda_grammar`) and `scripts/` to `{BUNDLE}` and put that first on `sys.path`, so the notebook needs no copy of the
repository as an input. Made by `scripts/bundle_notebook.py`; rebuild it after changing the code.
""", 0),
        cell("code", f"""import sys
from pathlib import Path

BUNDLE = Path("{BUNDLE}")
for folder in {folders!r}:
    Path(folder).mkdir(parents=True, exist_ok=True)
sys.path.insert(0, str(BUNDLE))
""", 1),
    ]
    for p, target in bundled:
        head.append(cell("code", f"%%writefile {target}\n{p.read_text(encoding='utf-8')}", len(head)))
    nb["cells"] = head + nb["cells"]
    out.write_text(json.dumps(nb, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"{out}: {len(bundled)} files bundled, {len(nb['cells'])} cells")


if __name__ == "__main__":
    main(*sys.argv[1:])
