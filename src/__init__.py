"""ganda-grammar: Luganda spelling and grammar correction by cited rules."""
from .rules import RULES, Edit, Result, correct

__version__ = "0.1.0"

__all__ = ["RULES", "Edit", "Result", "correct"]
