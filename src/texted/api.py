"""
Compact DSL for editing plain text files.

This DSL is line-oriented and  focus on simple text editing operations that
operates on independent chunks of text (for example commenting/uncommenting lines).

It is not suitable for complex changes. If you need those, please consider
using a library that is syntax-aware, like :pypi:`configupdater` for ``.ini/.cfg``
files, :pypi:`tomlkit` for ``.toml`` and :pypi:`libCST` or :pypi:`refactor` for
Python files.

When using the DSL there are 2 kinds of operations you can do with text, a
select operation (``SelectOp``) and an edit operation (``EditOp``).

One of the most basic select operation can be created with :func:`find`. This
operation will select the first line that matches a criteria. For example::

    find(lambda line: "[testenv:typecheck]" in line)

will select the first line of a text that contains the ``"[testenv:typecheck]"`` string.
We can then *extend* this selection for all the contiguous lines that are not
empty with::

    select_while(bool)  # => bool is handy! bool("") == False, bool("not empty") == True

After you have selected the block of lines, you can apply a edit operation.
For example::

    add_prefix("# ")  # => equivalent to: replace(lambda line: "# " + line)

will add the `# ` to all the non empty lines in the selection.

Note that all these functions are lazy and don't do anything until they are
called with ``edit``::

    >>> from inspect import cleandoc
    >>> example = '''
    ... # [testenv:typecheck]
    ... # deps = mypy
    ... # commands = python -m mypy {posargs:src}
    ... [testenv:docs]
    ... deps = sphinx
    ... changedir = docs
    ... commands = python -m sphinx -W --keep-going . {toxinidir}/build/html
    ... '''
    >>> text = cleandoc(example)
    >>> new_text = edit(
    ...    text,
    ...    remove_prefix("# "),
    ...    find(lambda line: "[testenv:typecheck]" in line),
    ...    select_until(lambda line: line.startswith("[textenv") or not line),
    ... )
    >>> print(new_text)
    [testenv:typecheck]
    deps = mypy
    commands = python -m mypy {posargs:src}
    [testenv:docs]
    deps = sphinx
    changedir = docs
    commands = python -m sphinx -W --keep-going . {toxinidir}/build/html

.. note:: This library supports only `\\n` line endings.
"""
from functools import partial, reduce
from itertools import chain, islice
from textwrap import indent
from typing import TYPE_CHECKING, Callable, Iterator, List, Type, cast

if TYPE_CHECKING:
    from typing_extensions import Self  # import from stdlib once Python >= 3.11
    from typing_extensions import TypeAlias  # import from stdlib once Python >= 3.10

    Predicate: TypeAlias = Callable[[str], bool]
    SelectOp: TypeAlias = Callable[[List[str], slice], slice]
    EditOp: TypeAlias = Callable[[List[str], slice], List[str]]
    Change: TypeAlias = Callable[[str], str]
else:
    Predicate = "Predicate"
    SelectOp = "SelectOp"
    EditOp = "EditOp"
    Change = "Change"


def negate(pred: Predicate) -> Predicate:
    """Logical ``not`` that can be applied to a predicate.

    >>> 1 + 1
    55
    >>> predicate = lambda line: "python" in line.lower()
    >>> predicate("Python is a programming language")
    True
    >>> opposite_predicate = negate(predicate)
    >>> opposite_predicate("Python is a programming language")
    False
    """
    return lambda line: not pred(line)


def find(pred: Predicate) -> SelectOp:
    r"""Find the first line for which the predicate function evaluates to ``True``.

    >>> fn = find(lambda line: "write" in line)
    >>> lines = 'import sys\n\nsys.stdout.write("hello world")\n'.splitlines()
    >>> fn(lines, slice(len(lines)))
    slice(2, 3)
    """

    def _find(lines: List[str], select: slice) -> slice:
        return next(_find_all(pred, lines, select), select)

    return _find


def _find_all(pred: Predicate, lines: List[str], select: slice) -> Iterator[slice]:
    return (slice(i, i + 1) for i, line in enumerate(lines[select]) if pred(line))


def select_while(pred: Predicate) -> SelectOp:
    r"""Extend the current selection for contiguous lines while the predicate
    function evaluates to ``True``.

    >>> lines = '0\n1\n2\n3\n4\n5\n6\n7\n8\n9\n10'.splitlines()
    >>> fn = select_while(lambda line: int(line) < 5)
    >>> fn(slice(0, 1))
    slice(0, 5)
    """
    return select_until(negate(pred))


def select_until(pred: Predicate) -> SelectOp:
    r"""Extend the current selection for contiguous lines stopping just before
    the predicate function evaluates to ``True``.

    >>> lines = '0\n1\n2\n3\n4\n5\n6\n7\n8\n9\n10'.splitlines()
    >>> fn = select_until(lambda line: int(line) == 5)
    >>> fn(slice(0, 1))
    slice(0, 5)
    """
    return cast(SelectOp, partial(_until, pred))


def _until(pred: Predicate, lines: List[str], select: slice) -> slice:
    """Extend an existing selection until a line matching the predicate is found"""
    len_lines = len(lines)
    start = select.start or 0
    stop = select.stop or len(lines)
    selections = (slice(start, i) for i in range(stop, len_lines) if pred(lines[i]))
    return next(selections, select)


def replace(fn: Change) -> EditOp:
    """Replace a chunk of text.
    The provided function will be called with the selected text as argument
    and its return value will be used as replacement.
    """
    return cast(EditOp, partial(_replace, fn))


def _replace(fn: Change, lines: List[str], select: slice) -> List[str]:
    print(f"{select=}")
    replacement = fn("\n".join(lines[select])).splitlines()
    start = select.start or 0
    stop = select.stop or len(lines)
    res_ = lines[:start] + replacement + lines[stop:]
    print(f"{start=} {stop=} {replacement=} {res_=}")
    return res_


def skip_whitespace(line: str) -> bool:
    return bool(line.strip())


def add_prefix(prefix: str, skip: Predicate = skip_whitespace) -> EditOp:
    """Add a fixed prefix string to every line in the selection for which the
    ``skip`` function does not evaluate to ``True``.
    When no ``skip`` function is provided, empty lines are skipped.
    """
    return replace(lambda text: indent(text, prefix, skip))


def _dedent(text: str, prefix: str, skip: Predicate) -> str:
    lines = text.splitlines()
    i = len(prefix)
    return "\n".join(
        line[i:] if not skip(line) and line.startswith(prefix) else line
        for line in lines
    )


def remove_prefix(prefix, skip: Predicate = skip_whitespace) -> EditOp:
    """Remove a fixed prefix string to every line in the selection for which the
    ``skip`` function does not evaluate to ``True``.
    Please note that if the line does not start with the prefix, it is skipped.
    """
    return replace(lambda text: _dedent(text, prefix, skip))


def edit(text: str, change: EditOp, *select: SelectOp) -> str:
    """Apply the operations to a text. You can stack a series of select operations,
    but only one edit operation is allowed.
    """
    lines = text.splitlines()
    all_text = slice(len(lines))
    new_select = reduce(lambda new_select, x: x(lines, new_select), select, all_text)
    print(f"{new_select=}")
    return "\n".join(change(lines, new_select))
