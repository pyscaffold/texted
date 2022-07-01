from ._edit import Edit, add_prefix, edit, remove_prefix, replace
from ._predicate import (
    Predicate,
    blank,
    contains,
    endswith,
    fullmatch,
    glob,
    match,
    negate,
    pred,
    search,
    startswith,
)
from ._single_selection import Selection, everything, find, until, whilist
from ._version import __version__

__all__ = [
    "__version__",
    # _predicate
    "Predicate",
    "blank",
    "contains",
    "endswith",
    "fullmatch",
    "glob",
    "match",
    "negate",
    "pred",
    "search",
    "startswith",
    # _single_selection
    "Selection",
    "everything",
    "find",
    "until",
    "whilist",
    # _edit
    "Edit",
    "add_prefix",
    "edit",
    "remove_prefix",
    "replace",
]
