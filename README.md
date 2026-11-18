# ganda-grammar

Luganda spelling and grammar correction by rules, each one citing the published orthography or grammar it comes from.
Pure Python, no dependencies, about 50,000 words a second on one core.

```
$ ganda-grammar correct "Abantu bangi na abantu abalala bagenze mukibuga n'ebintu ekirungi."
Abantu bangi n'abantu abalala bagenze mu kibuga n'ebintu ekirungi.
```

## Install

```
pip install ganda-grammar               # from PyPI, once published
pip install .                           # from this repository
pip install '.[mine]'                   # also read Hugging Face datasets (fix --hf, mine --hf)
```

## Use

### From the command line

```
ganda-grammar correct "na abantu"                  # → n'abantu
echo "ebitabo kyange" | ganda-grammar correct      # stdin → ebitabo byange
ganda-grammar correct --json "na bo"               # the corrected text and every edit, as JSON
```

Correct a whole dataset into a new folder. `.txt` files are corrected line by line, `.jsonl` files in the fields you
name; everything else in a row, and every line the rules leave alone, is copied unchanged. The input is never
overwritten.

```
ganda-grammar fix corpus/ -o corpus_fixed/
ganda-grammar fix data.jsonl -o fixed/ --field text --field luganda --log changes.jsonl --workers 8
ganda-grammar fix --hf sulaimank/luganda_text_wiki_bukedde_radio_flores -o fixed/
```

`--log` writes one row per changed line or field, with the original, the correction and each edit, enough to review or
undo any change. `ganda-grammar mine` writes only the sentences the rules changed, as before/after pairs.

### From Python

```python
import ganda_grammar as gg

r = gg.correct("Na abantu bagenda mukibuga.")
r.text    # "N'abantu bagenda mu kibuga."
r.edits   # [Edit(rule='ELISION_NA', start=1, end=3, before='a ', after="'"),
          #  Edit(rule='SPLIT_LOC', start=18, end=26, before='mukibuga', after='mu kibuga')]
gg.RULES["SPLIT_LOC"]   # (description, source)
```

Edit offsets point into the original text, so an editor can underline each one and explain it from `RULES`.

## Rules

| Rule | What it corrects | Source |
|---|---|---|
| `ELISION_NA` | na/ne before a vowel: na abantu → n'abantu | Walusimbi 2015, §1.1.4, §1.3(b) |
| `ELISION_NGA` | nga before a vowel: nga ali → ng'ali | Walusimbi 2015, §1.3(c) |
| `ELISION_POSS` | a possessive before a vowel: kya okulya → ky'okulya | Walusimbi 2015, §1.3(g) |
| `ELISION_REL` | bwe, gye in set phrases: bwe atyo → bw'atyo | Walusimbi 2015, §1.3(j) |
| `JOIN_NA_PRONOUN` | na and a pronoun are one word: na bo → nabo, na nze → nange | Walusimbi 2015 |
| `JOIN_FIXED` | words written as one: buli jjo → bulijjo | Walusimbi 2015 |
| `SPLIT_NE` | narrative ne is a word of its own: nebagenda → ne bagenda | Walusimbi 2015 |
| `SPLIT_LOC` | mu and ku are words of their own: mukibuga → mu kibuga | Walusimbi 2015 |
| `ORTH_L_R` | r, not l, after e or i: ebilala → ebirala | Walusimbi 2015, §1.3 |
| `ORTH_VV_NC` | single vowel before a nasal + consonant: ensiimbi → ensimbi | Walusimbi 2015, §1.1.5, §1.1.7 |
| `ORTH_VV_CW` | single vowel after a consonant + w or y: omukyaala → omukyala | Walusimbi 2015, §1.1.6 |
| `ORTH_LENGTH` | vowel and consonant length as the dictionary spells it: gwanga → ggwanga | Walusimbi 2015, §1.1.1-1.1.2, §1.2; FSI Luganda Basic Course (1968) |
| `AGREE_ADJ` | an adjective takes its noun's class: ebintu ekirungi → ebintu ebirungi | Sternefeld & Sseguya, A Luganda Grammar (2015), §7 |
| `AGREE_POSS` | a possessive takes its noun's class: ebitabo kyange → ebitabo byange | Sternefeld & Sseguya 2015, §6 |

Walusimbi 2015 is *Empandiika y'Oluganda Entongole*, the official Luganda orthography. `RULES` holds the full
citations.

## Limits

- **It corrects only what the rules cover.** Other misspellings and most grammar errors pass through unchanged.
- **Agreement is checked after about 230 nouns** whose class is certain (`src/rules/agreement.py`), not after every
  noun, and not after a noun that follows an apostrophe (`y'ekibuga ebirungi`), where the adjective may belong to an
  earlier noun.
- **Sentences that don't read as Luganda are left alone**, judged by word shape and common foreign words. Mixed
  Luganda-English text can still get through.
- **The precision of each rule on real text hasn't been measured yet.** Review a sample of `--log` output before
  trusting `fix` on data that matters.

## The word list

`notebooks/build_wordlist.ipynb` counts every Luganda word form in 48 Hugging Face datasets and writes
`luganda_words.tsv`: each word, how often it occurs and in how many datasets, with machine-generated text counted
apart. It counts only sentences that read as Luganda, by the package's own test. `build_wordlist_selfcontained.ipynb`
is the same notebook with the package written into its first cells, so it runs on Kaggle with nothing to install.
The list is published as [henryhale/luganda-words](https://huggingface.co/datasets/henryhale/luganda-words) on
Hugging Face. Neither the notebooks nor the word list are part of the package.

## Development

```
pip install '.[test]'   # reinstall after changing src/
pytest
```

Every rule's description carries examples (`before → after`), and each one is a test. `scripts/` holds the tools that
build the rules' data (`build_spellings.py`) and bundle the package into a self-contained notebook
(`bundle_notebook.py`).

## Licence

Apache License 2.0 (see `LICENSE`).
