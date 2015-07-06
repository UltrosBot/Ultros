Coding
======

Formatting
----------

This project follows the [PEP8](https://www.python.org/dev/peps/pep-0008/)
style guide for all Python code. Flake8 is run alongside other tests on our
CI server at every commit to ensure compliance. We do however have a few
exceptions. Docstrings are allowed to take up the full 79 characters, and there
is no complexity check. Additionally, as
[A Foolish Consistency is the Hobgoblin of Little Minds]
(https://www.python.org/dev/peps/pep-0008/#id10), the `# noqa` comment may be
freely added to a line to skip validation.

We recommend anyone committing code to setup a flake8 pre-commit hook.

Structure
---------

For a more complete understanding of any particular module, we suggest checking
out the API docs, or scanning over the source code, but below is a simple
high-level overview of the entire system.

**TODO:** This
