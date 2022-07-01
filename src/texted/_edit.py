from functools import partial
from typing import TYPE_CHECKING, Callable, List, Union, cast, overload

from ._predicate import Predicate, blank
from ._single_selection import Selection, everything

if TYPE_CHECKING:
    from typing_extensions import TypeAlias  # import from stdlib once Python >= 3.10

    Edit: TypeAlias = Callable[[List[str], slice], List[str]]
    Change: TypeAlias = Callable[[str], str]
else:
    Edit = "Edit"
    Change = "Change"


def replace(fn: Change) -> Edit:
    """Replace a chunk of text.
    The provided function will be called with the selected text as argument
    and its return value will be used as replacement.
    """
    return cast(Edit, partial(_replace, fn))


def _replace(fn: Change, lines: List[str], select: slice) -> List[str]:
    selected_lines = lines[select]
    if len(selected_lines) < 1:
        return lines

    print(f"{select=} {selected_lines}")
    replacement = _splitlines(fn("\n".join(selected_lines)))
    start = select.start or 0
    stop = select.stop or len(lines)
    print(f"{start=} {lines[:start]=}")
    print(f"{replacement=}")
    print(f"{stop=} {lines[stop:]=}")
    res_ = lines[:start] + replacement + lines[stop:]
    print(f"{res_=}")
    return res_


def add_prefix(prefix: str, skip: Union[Predicate, None] = blank) -> Edit:
    """Add a fixed prefix string to every line in the selection for which the
    ``skip`` function does not evaluate to ``True``.
    When no ``skip`` function is provided, blank lines are skipped.
    """
    pred = skip or (lambda _: False)
    return replace(lambda text: _indent(text, prefix, pred))


def remove_prefix(prefix, skip: Union[Predicate, None] = blank) -> Edit:
    """Remove a fixed prefix string to every line in the selection for which the
    ``skip`` function does not evaluate to ``True``.
    Please note that if the line does not start with the prefix, it is skipped.
    """
    pred = skip or (lambda _: False)
    return replace(lambda text: _dedent(text, prefix, pred))


def _dedent(text: str, prefix: str, skip: Predicate) -> str:
    i = len(prefix)
    return "\n".join(
        line[i:] if not skip(line) and line.startswith(prefix) else line
        for line in _splitlines(text)
    )


def _indent(text: str, prefix: str, skip: Predicate) -> str:
    return "\n".join(
        (prefix + line) if not skip(line) else line for line in _splitlines(text)
    )


def _splitlines(text: str):
    return [""] if text == "" else text.splitlines()


@overload
def edit(text: str, change: Edit) -> str:
    ...


@overload
def edit(text: str, select: Selection, change: Edit) -> str:
    ...


def edit(text, select, change=None):
    """Apply the operations to a text. You can stack a series of select operations,
    but only one edit operation is allowed.
    """
    if change is None:
        change = select
        select = everything

    lines = text.splitlines()
    all_text = slice(len(lines))
    new_select = select(lines, all_text)
    return "\n".join(change(lines, new_select))
