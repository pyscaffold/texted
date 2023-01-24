from __future__ import annotations

from abc import ABC, abstractmethod
from functools import partial
from typing import TYPE_CHECKING, Callable, Iterator, TypeVar, cast

from ._predicate import Predicate, negate

if TYPE_CHECKING:
    from typing_extensions import TypeAlias  # import from stdlib once Python >= 3.10

    _Select: TypeAlias = Callable[[list[str], slice | None], slice]
else:
    _Select = "_Select"


T = TypeVar("T", bound="Selection")


class Selection(ABC):
    @abstractmethod
    def _select(self, lines: list[str]) -> Iterator[slice]:
        ...

    @abstractmethod
    def __rshift__(self: T, op: _Select) -> T:
        ...

    def enumerate(self, lines: list[str]) -> Iterator[tuple[int, str]]:
        """Iterate over the selected lines"""
        len_ = len(lines)
        for _slice in self._select(lines):
            _range = range(_slice.start or 0, _slice.stop or len_, _slice.step or 1)
            yield from zip(_range, lines[_slice])


class _SingleSelection(Selection):
    def __init__(self, op: _Select):
        self._op: _Select = op._op if isinstance(op, _SingleSelection) else op

    def _select(self, lines: list[str]) -> Iterator[slice]:
        yield self(lines, None)

    def __call__(self, lines: list[str], base: slice | None) -> slice:
        return self._op(lines, base)

    def __rshift__(self, op: _Select) -> _SingleSelection:
        other_op = op._op if isinstance(op, _SingleSelection) else op
        self_op = self._op

        def _chain(lines: list[str], base: slice | None) -> slice:
            return other_op(lines, self_op(lines, base))

        return _SingleSelection(_chain)


def _until(pred: Predicate, lines: list[str], base: slice | None) -> slice:
    """Extend an existing selection until a line matching the predicate is found"""
    len_lines = len(lines)
    base = base or slice(0)
    start = base.start or 0
    stop = base.stop or start
    step = base.step or 1

    selections = (
        slice(start, i, step) for i in range(stop, len_lines, step) if pred(lines[i])
    )
    return next(selections, slice(start, len_lines, step))


def until(pred: Predicate) -> _SingleSelection:
    r"""Extend the current selection for contiguous lines stopping just before
    the predicate function evaluates to ``True``.

    >>> lines = "a b c d e f g h i j k l".split()
    >>> select = until(lambda line: "f" in line)
    >>> for i, line in select.enumerate(lines):
    ...     print(f"# {i} - {line}")
    # 0 - a
    # 1 - b
    # 2 - c
    # 3 - d
    # 4 - e
    >>> select = (
    ...     find(lambda line: "c" in line) >>  # select the first line
    ...     until(lambda line: "f" in line)    # add continuous lines
    ... )
    >>> for i, line in select.enumerate(lines):
    ...     print(f"# {i} - {line}")
    # 2 - c
    # 3 - d
    # 4 - e
    """
    return _SingleSelection(cast(_Select, partial(_until, pred)))


def whilist(pred: Predicate) -> _SingleSelection:
    r"""Extend the current selection for contiguous lines while the predicate
    function evaluates to ``True``.

    >>> lines = "a b c d e f g h i j k l".split()
    >>> select = whilist(lambda line: ord(line) < ord("f"))
    >>> for i, line in select.enumerate(lines):
    ...     print(f"# {i} - {line}")
    # 0 - a
    # 1 - b
    # 2 - c
    # 3 - d
    # 4 - e
    >>> select = (
    ...     find(lambda line: "c" in line) >>         # select the first line
    ...     whilist(lambda l: ord(l) <= ord("d")) >>  # add continuous lines
    ...     whilist(lambda l: ord(l) > ord("f"))      # no continuous lines to add ...
    ... )
    >>> for i, line in select.enumerate(lines):
    ...     print(f"# {i} - {line}")
    # 2 - c
    # 3 - d
    """
    return until(negate(pred))


def find(pred: Predicate) -> _Select:
    r"""Select the first line for which the predicate function evaluates to ``True``.

    >>> select = find(lambda line: "write" in line)
    >>> lines = 'import sys\n\nsys.stdout.write("hello world")\n'.splitlines()
    >>> for i, line in select.enumerate(lines):
    ...     print(f"# {i} - {line}")
    # 2 - sys.stdout.write("hello world")
    """

    def _find(lines: list[str], base: slice | None) -> slice:
        return next(_find_all(pred, lines, base), slice(0))

    return _SingleSelection(_find)


def _find_all(pred: Predicate, lines: list[str], base: slice | None) -> Iterator[slice]:
    base = base or slice(0, len(lines))
    return (slice(i, i + 1) for i, line in enumerate(lines[base]) if pred(line))


def everything(lines: list[str], base: slice | None) -> slice:
    return base or slice(0, len(lines))
