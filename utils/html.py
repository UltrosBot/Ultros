# coding=utf-8

"""
A few useful utilities for working with HTML.
This is especially useful for dealing with HTML-based protocols, such as
Mumble.
"""

__author__ = 'Gareth Coles'

from HTMLParser import HTMLParser
import htmlentitydefs


class HTMLTextExtractor(HTMLParser):
    """
    Class for extracting text from HTML snippets. This is done by removing
    all the tags and optionally inserting newlines at the relevant
    places.

    Don't use this directly, use the function below.
    """

    def __init__(self, newlines=True):
        HTMLParser.__init__(self)
        self.result = []
        self.newlines = newlines

    def handle_starttag(self, tag, attrs):
        if self.newlines:
            if tag == 'br':
                self.result.append('\n')
            elif tag == 'p':
                self.result.append('\n')

    def handle_endtag(self, tag):
        if self.newlines:
            if tag == 'p':
                self.result.append('\n')

    def handle_data(self, d):
        self.result.append(d)

    def handle_charref(self, number):
        if number[0] in (u'x', u'X'):
            codepoint = int(number[1:], 16)
        else:
            codepoint = int(number)
        self.result.append(unichr(codepoint))

    def handle_entityref(self, name):
        codepoint = htmlentitydefs.name2codepoint[name]
        self.result.append(unichr(codepoint))

    def get_text(self):
        return u''.join(self.result)


def html_to_text(html, newlines=False):
    """
    Given a HTML snippet, strip out all the HTML and leave just the text.

    :param html: HTML to strip
    :param newlines: Whether to replace <p>, <p/> and <br /> with newlines
    :return: The stripped snippet
    """
    s = HTMLTextExtractor(newlines)
    s.feed(html)
    return s.get_text()


def unescape_html_entities(text):
    return HTMLParser().unescape(text)
