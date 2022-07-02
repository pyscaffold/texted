from functools import reduce
from inspect import cleandoc

from texted import blank, contains, find, until, whilist

example = cleandoc(
    """
    # [testenv:typecheck]
    # deps = mypy

    [testenv:docs]
    deps = sphinx
    """
)


def apply_selection(text, *select):
    lines = cleandoc(text).splitlines()
    all_lines = slice(len(lines))  # we start with all the lines selected
    selected = reduce(lambda new_select, x: x(lines, new_select), select, all_lines)
    return "\n".join(lines[selected])


def test_find():
    text = apply_selection(example, find(contains("mypy")))
    assert text == "# deps = mypy"
    text = apply_selection(example, find(blank))
    assert text == ""


def test_until():
    fn = find(contains("mypy")) >> until(contains("sphinx"))
    text = apply_selection(example, fn)
    assert text == "# deps = mypy\n\n[testenv:docs]"


def test_until_first_line():
    fn = find(blank) >> until(blank)
    text = apply_selection(example, fn)
    assert text == "\n[testenv:docs]\ndeps = sphinx"


def test_whilist():
    fn = find(contains("typecheck")) >> whilist(~blank)
    text = apply_selection(example, fn)
    assert text == "# [testenv:typecheck]\n# deps = mypy"


def test_whilist_first_line():
    fn = find(blank) >> whilist(~blank)
    text = apply_selection(example, fn)
    assert text == "\n[testenv:docs]\ndeps = sphinx"
