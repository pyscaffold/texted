from inspect import cleandoc

from texted import add_prefix, blank, edit, find, remove_prefix, whilist

example = cleandoc(
    """
    # [testenv:typecheck]
    # deps = mypy

    [testenv:docs]
    deps = sphinx
    """
)


def test_add_prefix():
    text = edit(
        example,
        find(blank),
        add_prefix("%%", skip=None),
    )
    expected = """
    # [testenv:typecheck]
    # deps = mypy
    %%
    [testenv:docs]
    deps = sphinx
    """
    assert text == cleandoc(expected)

    # Add prefix should skip blank lines by default
    text = edit(
        example,
        find(blank) >> whilist(~blank),
        add_prefix("# "),
    )
    expected = """
    # [testenv:typecheck]
    # deps = mypy

    # [testenv:docs]
    # deps = sphinx
    """
    # Add prefix should skip blank lines by default
    assert text == cleandoc(expected)


def test_remove_prefix():
    text = edit(
        example,
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
