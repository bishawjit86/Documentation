"""
    sphinx.util.rst
    ~~~~~~~~~~~~~~~

    reST helper functions.

    :copyright: Copyright 2007-2019 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

import re
from collections import defaultdict
from contextlib import contextmanager
from unicodedata import east_asian_width

from docutils.parsers.rst import roles
from docutils.parsers.rst.languages import en as english
from docutils.utils import Reporter
from jinja2 import environmentfilter

from sphinx.locale import __
from sphinx.util import docutils
from sphinx.util import logging

if False:
    # For type annotation
    from typing import Callable, Dict, Generator  # NOQA
    from docutils.statemachine import StringList  # NOQA
    from jinja2 import Environment  # NOQA

logger = logging.getLogger(__name__)

docinfo_re = re.compile(':\\w+:.*?')
symbols_re = re.compile(r'([!-\-/:-@\[-`{-~])')  # symbols without dot(0x2e)
SECTIONING_CHARS = ['=', '-', '~']

# width of characters
WIDECHARS = defaultdict(lambda: "WF")   # type: Dict[str, str]
                                        # WF: Wide + Full-width
WIDECHARS["ja"] = "WFA"  # In Japanese, Ambiguous characters also have double width


def escape(text):
    # type: (str) -> str
    text = symbols_re.sub(r'\\\1', text)
    text = re.sub(r'^\.', r'\.', text)  # escape a dot at top
    return text


def textwidth(text, widechars='WF'):
    # type: (str, str) -> int
    """Get width of text."""
    def charwidth(char, widechars):
        # type: (str, str) -> int
        if east_asian_width(char) in widechars:
            return 2
        else:
            return 1

    return sum(charwidth(c, widechars) for c in text)


@environmentfilter
def heading(env, text, level=1):
    # type: (Environment, str, int) -> str
    """Create a heading for *level*."""
    assert level <= 3
    width = textwidth(text, WIDECHARS[env.language])  # type: ignore
    sectioning_char = SECTIONING_CHARS[level - 1]
    return '%s\n%s' % (text, sectioning_char * width)


@contextmanager
def default_role(docname, name):
    # type: (str, str) -> Generator
    if name:
        dummy_reporter = Reporter('', 4, 4)
        role_fn, _ = roles.role(name, english, 0, dummy_reporter)
        if role_fn:
            docutils.register_role('', role_fn)
        else:
            logger.warning(__('default role %s not found'), name, location=docname)

    yield

    docutils.unregister_role('')


def prepend_prolog(content, prolog):
    # type: (StringList, str) -> None
    """Prepend a string to content body as prolog."""
    if prolog:
        pos = 0
        for line in content:
            if docinfo_re.match(line):
                pos += 1
            else:
                break

        if pos > 0:
            # insert a blank line after docinfo
            content.insert(pos, '', '<generated>', 0)
            pos += 1

        # insert prolog (after docinfo if exists)
        for lineno, line in enumerate(prolog.splitlines()):
            content.insert(pos + lineno, line, '<rst_prolog>', lineno)

        content.insert(pos + lineno + 1, '', '<generated>', 0)


def append_epilog(content, epilog):
    # type: (StringList, str) -> None
    """Append a string to content body as epilog."""
    if epilog:
        content.append('', '<generated>', 0)
        for lineno, line in enumerate(epilog.splitlines()):
            content.append(line, '<rst_epilog>', lineno)
