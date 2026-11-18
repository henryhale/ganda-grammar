# Development

```
pip install '.[test]'   # reinstall after changing src/
pytest
```

The package is `src/` itself, installed as `ganda_grammar`. There's no editable install, so reinstall before
running the tests.

## Adding a rule

Each rule family in `src/rules/` (`agreement`, `elision`, `joining`, `orthography`) has:
- `RULES`: `{rule_id: (description, source)}`
- `edits(text, tokens)`: returns a list of `Edit`

**A rule's description is its test.** Write it as `what it corrects: before → after, before → after`. The test suite
checks that each example is corrected exactly that way, by that rule alone. When you add an exception, also add the
text it protects to `test_left_alone` in `tests/test_rules.py`.

## Rule data

`src/rules/spellings.tsv` holds the misspellings `ORTH_LENGTH` corrects. `scripts/build_spellings.py` builds it from
the FSI glossary and corpus counts.

## Docs

```
pip install '.[docs]'
mkdocs serve
```

The rules table is generated from `RULES` when the docs are built.

## Releasing

Push a tag such as `v0.2.0`. The version comes from the tag, and the publish workflow runs the tests, uploads to
PyPI and creates a GitHub release.
