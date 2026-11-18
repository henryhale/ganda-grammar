# ganda-grammar

Luganda spelling and grammar correction by rules. Each rule cites the official orthography,
[Empandiika y'Oluganda Entongole](https://learnluganda.com/empandiika), or a published grammar. It's pure Python with
no dependencies, and it needs no model and no network.

```
pip install ganda-grammar
```

```
$ ganda-grammar correct "Abantu bangi na abantu abalala bagenze mukibuga."
Abantu bangi n'abantu abalala bagenze mu kibuga.
```

## How it works

1. **The text is split into sentences.**
2. **Sentences that don't read as Luganda are left alone.** A sentence reads as Luganda when most of its words are
   made of Luganda syllables and it has no common English, Swahili or Chichewa function words.
3. **Each [rule](rules.md) suggests edits:** elision, word division, spelling and agreement.
4. **Overlaps are resolved and the edits applied.** When two edits overlap, agreement wins over elision, elision over
   word division, and word division over spelling.

Every edit records the rule that made it and its position in the original text, so it can be explained or undone.

## Limits

- **It corrects only what its rules cover.** Other misspellings and most grammar errors pass through unchanged.
- **The rules favour precision.** Ambiguous cases are left alone. For example, agreement is checked only after about
  230 nouns whose class is certain.
- **Mixed Luganda-English text can still get through** the Luganda check.
- **The precision of each rule on real text hasn't been measured yet.** Review a sample of `fix --log` output before
  trusting it on data that matters.
