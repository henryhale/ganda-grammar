# Usage

## Python

```python
import ganda_grammar as gg

r = gg.correct("Na abantu bagenda mukibuga.")
r.text   # "N'abantu bagenda mu kibuga."
r.edits  # [Edit(rule='ELISION_NA', start=1, end=3, before='a ', after="'"),
         #  Edit(rule='SPLIT_LOC', start=18, end=26, before='mukibuga', after='mu kibuga')]

gg.RULES["SPLIT_LOC"]  # (description, source)
```

`start` and `end` are offsets into the original text, so an editor can underline each edit and explain it from
`RULES`.

## Command line

### correct

```
ganda-grammar correct "na abantu"               # n'abantu
echo "ebitabo kyange" | ganda-grammar correct   # ebitabo byange
ganda-grammar correct --json "na bo"            # the text and every edit, as JSON
```

### fix

`fix` writes a corrected copy of a dataset into a new folder and never overwrites the input.

```
ganda-grammar fix corpus/ -o fixed/
ganda-grammar fix data.jsonl -o fixed/ --field text --field luganda --log changes.jsonl
ganda-grammar fix --hf sulaimank/luganda_text_wiki_bukedde_radio_flores -o fixed/
```

- **`.txt` files are corrected line by line.** In `.jsonl` files, only the fields named with `--field` are corrected
  (default `text`). Everything else is copied byte for byte.
- **`--log`** writes one row per change, with the original, the correction and its edits, enough to review or undo it.
- **`--workers`** sets the number of processes (default: one per CPU).
- **`--hf`** reads a Hugging Face dataset and needs `pip install 'ganda-grammar[mine]'`.

### mine

`mine` writes only the sentences the rules changed, as before/after pairs, for example to train a correction model.

```
ganda-grammar mine corpus/ -o corrections.jsonl
```
