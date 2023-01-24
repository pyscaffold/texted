.. These are examples of badges you might want to add to your README:
   please update the URLs accordingly

    .. image:: https://api.cirrus-ci.com/github/<USER>/texted.svg?branch=main
        :alt: Built Status
        :target: https://cirrus-ci.com/github/<USER>/texted
    .. image:: https://readthedocs.org/projects/texted/badge/?version=latest
        :alt: ReadTheDocs
        :target: https://texted.readthedocs.io/en/stable/
    .. image:: https://img.shields.io/coveralls/github/<USER>/texted/main.svg
        :alt: Coveralls
        :target: https://coveralls.io/r/<USER>/texted
    .. image:: https://img.shields.io/pypi/v/texted.svg
        :alt: PyPI-Server
        :target: https://pypi.org/project/texted/
    .. image:: https://img.shields.io/conda/vn/conda-forge/texted.svg
        :alt: Conda-Forge
        :target: https://anaconda.org/conda-forge/texted
    .. image:: https://pepy.tech/badge/texted/month
        :alt: Monthly Downloads
        :target: https://pepy.tech/project/texted
    .. image:: https://img.shields.io/twitter/url/http/shields.io.svg?style=social&label=Twitter
        :alt: Twitter
        :target: https://twitter.com/texted

.. image:: https://img.shields.io/badge/-PyScaffold-005CA0?logo=pyscaffold
    :alt: Project generated with PyScaffold
    :target: https://pyscaffold.org/

|

======
texted
======


    Compact *domain specific language* (DSL) for editing blocks of plain text

``texted`` is a line-oriented DSL that focus on simple text editing operations,
operating on independent chunks of text (for example commenting/uncommenting lines).

It is not suitable for complex changes. If you need those, please consider
using a library that is syntax-aware, like configupdater_ for ``.ini/.cfg``
files, tomlkit_ for ``.toml`` and libCST_ or refactor_ for Python files.


.. _configupdater: https://configupdater.readthedocs.io/en/latest/
.. _tomlkit: https://github.com/sdispater/tomlkit/blob/master/docs/quickstart.rst
.. _libCST: https://libcst.readthedocs.io/en/latest/
.. _refactor: https://refactor.readthedocs.io/en/latest/


Installation
============

You can install ``texted`` with the help of ``pip``:

.. code-block:: bash

   $ pip install texted

After doing that you will be able to use ``texted`` in your Python scripts.


Quickstart
==========

Using ``texted`` involves the following workflow:

1. Select the relevant lines of a given text.
2. Perform an edition operation over the selection.

This is workflow is shown in the example below::

    >>> from texted import edit, find, until, contains, startswith, blank, remove_prefix
    >>> example = """\
    ... # [testenv:typecheck]
    ... # deps = mypy
    ... # commands = python -m mypy {posargs:src}
    ... [testenv:docs]
    ... deps = sphinx
    ... changedir = docs
    ... commands = python -m sphinx -W --keep-going . {toxinidir}/build/html
    ... """
    >>> new_text = edit(
    ...    example,
    ...    find(contains("[testenv:typecheck]")) >> until(startswith("[testenv") | blank),
    ...    remove_prefix("# "),
    ... )
    >>> print(new_text)
    [testenv:typecheck]
    deps = mypy
    commands = python -m mypy {posargs:src}
    [testenv:docs]
    deps = sphinx
    changedir = docs
    commands = python -m sphinx -W --keep-going . {toxinidir}/build/html


One of the most basic kinds of select operations can be created with ``find``.
This operation will select the first line that matches a criteria. For example::

    find(lambda line: "[testenv:typecheck]" in line)

… will select the first line of a text that contains the ``"[testenv:typecheck]"`` string.
We can then *extend* (``>>``) this selection for all the contiguous lines that are not
empty with::

    find(lambda line: "[testenv:typecheck]" in line) >> whilist(bool)
    # => bool is handy! bool("") == False, bool("not empty") == True

After you have selected the block of lines, you can apply a edit operation.
For example::

    add_prefix("# ")  # => equivalent to: replace(lambda line: "# " + line)

… will add the prefix ``"# "`` to all the non empty lines in the selection.

Note that all these functions are lazy and don't do anything until they are
called with ``edit``.

.. note:: This library supports only ``\n`` line endings.

Note
====

This project has been set up using PyScaffold 4.4. For details and usage
information on PyScaffold see https://pyscaffold.org/.
