#coding=UTF-8
__author__ = 'Gareth Coles'

from HTMLParser import HTMLParser
import htmlentitydefs


class HTMLTextExtractor(HTMLParser):
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


def html_to_text(html, newlines=True):
    s = HTMLTextExtractor(newlines)
    s.feed(html)
    return s.get_text()
