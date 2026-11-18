"""ganda-grammar: Luganda spelling and grammar correction by cited rules."""
from importlib.metadata import PackageNotFoundError, version

from .rules import RULES, Edit, Result, correct

try:
    __version__ = version("ganda-grammar")  # set from the git tag at build time (hatch-vcs)
except PackageNotFoundError:  # not installed, e.g. the copy a self-contained notebook writes
    __version__ = "unknown"

__all__ = ["RULES", "Edit", "Result", "correct"]
