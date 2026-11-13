# Luganda dictionary

15,655 Luganda words and phrases in the standard spelling, 11,496 of them attested (seen at least 2 times in the
texts below, or listed by two sources). Built by `notebooks/build_dictionary.ipynb` in the ganda-grammar repository.

Each entry: `headword`, `pos`, `noun_class`, `plural`, `english` (meanings), `sources`, `variants` (spellings the sources
used before the standard spelling was applied), `count` (occurrences in the texts; none for phrases) and `attested`.
Spellings were standardised with the ganda-grammar rules (Walusimbi, *Empandiika y'Oluganda Entongole*, 2015).

## Sources

| Source | Licence | Entries from it | Found only there |
|---|---|---|---|
| FSI Luganda Basic Course (1968), glossary | public domain (US government work) | 342 | 47 |
| FSI Luganda Basic Course (1968), lesson glossaries | public domain (US government work) | 99 | 10 |
| English-Luganda word list, version 2.0 | used with permission | 3,309 | 391 |
| ganda-grammar: nouns of the agreement rules | Apache-2.0 | 230 | 100 |
| ganda-grammar: verb stems (corpus counts and the English-Luganda list) | Apache-2.0 | 2,181 | 1,147 |
| pkyoyetera/luganda_english_dataset, entries of up to three words | Apache-2.0 (as tagged) | 16,509 | 6,559 |
| PanLex, via lbourdois/panlex | CC0-1.0 | 7,096 | 3,754 |
| English Wiktionary, Category:Luganda lemmas | CC BY-SA 4.0 | 162 | 35 |
| Wikidata lexemes, language Q33368 | CC0-1.0 | 9 | 2 |

Texts used only for counts:

| Text | Words counted (each sentence once) |
|---|---|
| the compiled local Luganda text (scripts/compile_luganda_text.py) | 1,856,114 |
| Common Voice Luganda sentences (CC0-1.0) | 1,340,481 |
| Makerere English-Luganda parallel corpus (CC BY 4.0) | 24,044 |
| henryhale/luganda-pretrain2 without tinystories-ganda | 27,181,836 |
| sagepond/luganda | 9,414,173 |
| goldfish-models/fish-food | 6,051,516 |
| kukuzaai/lug-cleaned-200M-tokens | 15,627,676 |
| sulaimank/luganda_text_wiki_bukedde_radio_flores | 4,242,875 |
| masakhane/masakhanews | 122,946 |
| michsethowusu/english-ganda_sentence-pairs_mt560 | 2,759,983 |
| aceuganda/lacuna-luganda-health-corpus | 644,535 |
| pkyoyetera/luganda_english_dataset | 37,286 |
| KMayanja/merged_txt_eng_lug | 18,200 |
| masakhane/afriscience_mt | 91,682 |
| BUAIR/Uganda-Multilingual-QA | 99,488 |
| akoksal/muri-it-language-split | 491 |
| ayymen/Pontoon-Translations | 15,929 |
| allandclive/Luganda_Sci-Math-Bio_Translations | 3,846 |
| keystats/luganda_asr_dataset | 36,070 |
| google/WaxalNLP | 157,282 |

## Licence

Each entry lists its sources, so it can be traced to its licence. Because it includes Wiktionary entries, the dictionary as a whole is under **CC BY-SA 4.0**; build it with `USE_WIKTIONARY = False` for a version without share-alike.
