from functools import partial
from typing import TYPE_CHECKING, Callable, Iterator, List, TypeVar, cast

from ._predicate import Predicate, negate

if TYPE_CHECKING:
    from typing_extensions import Protocol  # import from stdlib once Python >= 3.8
    from typing_extensions import TypeAlias  # import from stdlib once Python >= 3.10

    _Select: TypeAlias = Callable[[List[str], slice], slice]
else:
    from abc import ABC as Protocol

    _Select = "_Select"


T = TypeVar("T", bound="Selection")


class Selection(Protocol):
    def _select(self, lines: List[str]) -> Iterator[slice]:
        ...

    def __rshift__(self: T, op: _Select) -> T:
        ...


class _SingleSelection:
    def __init__(self, op: _Select):
        self._op: _Select = op._op if isinstance(op, _SingleSelection) else op

    def _select(self, lines: List[str]) -> Iterator[slice]:
        yield self(lines, slice(len(lines)))

    def __call__(self, lines: List[str], base: slice) -> slice:
        return self._op(lines, base)

    def __rshift__(self, op: _Select) -> "_SingleSelection":
        other_op = op._op if isinstance(op, _SingleSelection) else op
        self_op = self._op

        def _chain(lines: List[str], base: slice) -> slice:
            return other_op(lines, self_op(lines, base))

        return _SingleSelection(_chain)


def until(pred: Predicate) -> _SingleSelection:
    r"""Extend the current selection for contiguous lines stopping just before
    the predicate function evaluates to ``True``.

    >>> lines = '0\n1\n2\n3\n4\n5\n6\n7\n8\n9\n10'.splitlines()
    >>> fn = until(lambda line: int(line) == 5)
    >>> fn(lines, slice(0, 1))
    slice(0, 5, None)
    """
    return _SingleSelection(cast(_Select, partial(_until, pred)))


def whilist(pred: Predicate) -> _SingleSelection:
    r"""Extend the current selection for contiguous lines while the predicate
    function evaluates to ``True``.

    >>> lines = '0\n1\n2\n3\n4\n5\n6\n7\n8\n9\n10'.splitlines()
    >>> fn = whilist(lambda line: int(line) < 5)
    >>> fn(lines, slice(0, 1))
    slice(0, 5, None)
    """
    return until(negate(pred))


def _until(pred: Predicate, lines: List[str], select: slice) -> slice:
    """Extend an existing selection until a line matching the predicate is found"""
    len_lines = len(lines)
    start = select.start or 0
    stop = select.stop or len_lines
    # print(f"----------- {stop=}, {lines[stop]=}, {pred(lines[stop])=}")
    selections = (
        slice(start, i)
        # slice(start, min(i + 1, len_lines))
        for i in range(stop, len_lines)
        if pred(lines[i])
    )
    return next(selections, select)


def find(pred: Predicate) -> _Select:
    r"""Select the first line for which the predicate function evaluates to ``True``.

    >>> fn = find(lambda line: "write" in line)
    >>> lines = 'import sys\n\nsys.stdout.write("hello world")\n'.splitlines()
    >>> fn(lines, slice(len(lines)))
    slice(2, 3, None)
    """

    def _find(lines: List[str], select: slice) -> slice:
        return next(_find_all(pred, lines, select), select)

    return _SingleSelection(_find)


def _find_all(pred: Predicate, lines: List[str], select: slice) -> Iterator[slice]:
    return (slice(i, i + 1) for i, line in enumerate(lines[select]) if pred(line))


def everything(_lines: List[str], select: slice) -> slice:
    return select
