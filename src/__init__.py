"""ganda-grammar: Luganda spelling and grammar correction, by cited rules or by a fine-tuned ByT5-small model."""
from .rules import RULES, Edit, Result
from .rules import correct as _correct_rules

__version__ = "0.1.0"


def correct(text: str, engine: str = "rules", **model_options) -> Result:
    """Correct Luganda text. engine="rules" (default), or "model" after pip install 'ganda-grammar[model]'.

    model_options go to the model engine: model (Hugging Face id or path), device, batch_size, num_beams.
    """
    if engine == "rules":
        return _correct_rules(text)
    if engine == "model":
        from .model import correct as _correct_model
        return _correct_model(text, **model_options)
    raise ValueError(f"engine must be 'rules' or 'model', not {engine!r}")


__all__ = ["RULES", "Edit", "Result", "correct"]
