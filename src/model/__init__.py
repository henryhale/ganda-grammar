"""Model engine: google/byt5-small fine-tuned to correct Luganda sentences (see notebooks/train_byt5.ipynb).

Each sentence is rewritten by the model; the edits are the character differences, with rule "MODEL".
"""
import difflib
from functools import lru_cache

from ..rules.base import Edit, Result, apply, sentences

MODEL = "henryhale/ganda-grammar-byt5-small"
# ponytail: a rewrite further from the input than this is taken as a hallucination and dropped; tune on a dev set
MIN_SIMILARITY = 0.8


@lru_cache(maxsize=None)
def load(model=MODEL, device=None):
    try:
        import torch
        from transformers import AutoModelForSeq2SeqLM, AutoTokenizer
    except ImportError as e:
        raise ImportError("the model engine needs: pip install 'ganda-grammar[model]'") from e
    device = device or ("cuda" if torch.cuda.is_available() else "cpu")
    return AutoTokenizer.from_pretrained(model), AutoModelForSeq2SeqLM.from_pretrained(model).to(device).eval()


def correct(text, model=MODEL, device=None, batch_size=16, num_beams=4):
    import torch

    tok, net = load(model, device)
    spans = list(sentences(text))
    outputs = []
    for i in range(0, len(spans), batch_size):
        batch = tok([text[s:e] for s, e in spans[i:i + batch_size]], return_tensors="pt", padding=True).to(net.device)
        with torch.no_grad():  # ByT5 works on bytes: the output is about as long as the input
            ids = net.generate(**batch, num_beams=num_beams, max_new_tokens=int(batch.input_ids.shape[1] * 1.2) + 8)
        outputs += tok.batch_decode(ids, skip_special_tokens=True)
    edits = []
    for (s, e), new in zip(spans, outputs):
        old = text[s:e]
        diff = difflib.SequenceMatcher(None, old, new, autojunk=False)
        if new != old and diff.ratio() >= MIN_SIMILARITY:
            edits += [Edit("MODEL", s + i1, s + i2, old[i1:i2], new[j1:j2])
                      for op, i1, i2, j1, j2 in diff.get_opcodes() if op != "equal"]
    return Result(apply(text, edits), edits)
