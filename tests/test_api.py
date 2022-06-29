import doctest
from functools import reduce
from inspect import cleandoc

from texted import api
from texted.api import (
    add_prefix,
    edit,
    find,
    negate,
    remove_prefix,
    select_until,
    select_while,
)

example = """
# [testenv:typecheck]
# deps = mypy

[testenv:docs]
deps = sphinx
"""


def apply_selection(text, *select):
    lines = cleandoc(text).splitlines()
    all_lines = slice(len(lines))  # we start with all the lines selected
    selected = reduce(lambda new_select, x: x(lines, new_select), select, all_lines)
    print(f"{selected=}")
    return "\n".join(lines[selected])


def test_find():
    text = apply_selection(example, find(lambda line: "mypy" in line))
    assert text == "# deps = mypy"
    text = apply_selection(example, find(negate(bool)))
    assert text == ""


def test_select_until():
    text = apply_selection(
        example,
        find(lambda line: "mypy" in line),
        select_until(lambda line: "sphinx" in line),
    )
    assert text == "# deps = mypy\n\n[testenv:docs]"


def test_select_while():
    text = apply_selection(
        example,
        find(lambda line: "typecheck" in line),
        select_while(bool),
    )
    assert text == "# [testenv:typecheck]\n# deps = mypy"


def test_add_prefix():
    print(f"{apply_selection(example, find(negate(bool)), select_while(bool))=}")
    text = edit(
        cleandoc(example),
        add_prefix("# "),
        find(negate(bool)),  # <- find the empty line
        select_while(bool),  # <- select all contiguous non-empty
    )
    expected = """
    # [testenv:typecheck]
    # deps = mypy

    # [testenv:docs]
    # deps = sphinx
    """
    # Add prefix should skip empty lines by default
    assert text == cleandoc(expected)


def test_remove_prefix():
    text = edit(
        cleandoc(example),
        remove_prefix("# "),
        # When no selection is given, the whole text is selected
    )
    expected = """
    [testenv:typecheck]
    deps = mypy

    [testenv:docs]
    deps = sphinx
    """
    # Remove prefix should skip files without prefix by default
    assert text == cleandoc(expected)
