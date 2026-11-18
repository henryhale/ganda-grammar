# ganda-grammar

[![PyPI](https://img.shields.io/pypi/v/ganda-grammar)](https://pypi.org/project/ganda-grammar/)
[![Tests](https://github.com/henryhale/ganda-grammar/actions/workflows/tests.yml/badge.svg)](https://github.com/henryhale/ganda-grammar/actions/workflows/tests.yml)
[![Docs](https://github.com/henryhale/ganda-grammar/actions/workflows/docs.yml/badge.svg)](https://henryhale.github.io/ganda-grammar/)
[![License](https://img.shields.io/badge/license-Apache--2.0-blue)](https://github.com/henryhale/ganda-grammar/blob/main/LICENSE)
[![Word list](https://img.shields.io/badge/%F0%9F%A4%97-luganda--words-yellow)](https://huggingface.co/datasets/henryhale/luganda-words)

Luganda spelling and grammar correction by rules, each one citing the official orthography,
[Empandiika y'Oluganda Entongole](https://learnluganda.com/empandiika), or a published grammar.
Pure Python, with no dependencies.

```
pip install ganda-grammar
```

```
$ ganda-grammar correct "Abantu bangi na abantu abalala bagenze mukibuga."
Abantu bangi n'abantu abalala bagenze mu kibuga.
```

```python
import ganda_grammar as gg

r = gg.correct("Na abantu bagenda mukibuga.")
r.text   # "N'abantu bagenda mu kibuga."
r.edits  # [Edit(rule='ELISION_NA', ...), Edit(rule='SPLIT_LOC', ...)]
```

It can also correct whole datasets: `ganda-grammar fix corpus/ -o fixed/`.

**[Documentation](https://henryhale.github.io/ganda-grammar/)**: usage, the rules and their sources, and their limits.

## Licence

[Apache-2.0](https://github.com/henryhale/ganda-grammar/blob/main/LICENSE)
