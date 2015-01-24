__author__ = 'Gareth Coles'

import gettext
import os

from system.singleton import Singleton

DOMAIN = "ultros"
DEFAULT = "en_GB"
DIRECTORY = "./translations"


class Translations(object):
    __metaclass__ = Singleton

    language = DEFAULT
    m_language = DEFAULT
    logger = None
    translation = None

    known = []

    def __init__(self, lang=None, mlang=None, log=True):
        self.log = log
        self.set_language(lang, mlang)

    def set_language(self, lang=None, mlang=None):
        if lang is None:
            lang = DEFAULT

        if mlang is None:
            mlang = DEFAULT

        self.get_known()

        if self.log and self.logger is None:
            from system.logging.logger import getLogger

            self.logger = getLogger("Translations")

        if lang not in self.known:
            if self.logger is None:
                print "Unknown language '%s', defaulting to '%s'" \
                      % (lang, DEFAULT)
            else:
                self.logger.warn("Unknown language '%s', defaulting to '%s'"
                                 % (lang, DEFAULT))

            lang = DEFAULT

        if mlang not in self.known:
            if self.logger is None:
                print "Unknown language '%s', defaulting to '%s'" \
                      % (mlang, DEFAULT)
            else:
                self.logger.warn("Unknown language '%s', defaulting to '%s'"
                                 % (mlang, DEFAULT))

            mlang = DEFAULT

        self.language = lang
        self.m_language = mlang
        self.reload()

    def get_known(self):
        self.known = os.listdir(DIRECTORY)
        return self.known

    def reload(self):
        self.translation = gettext.translation(DOMAIN, DIRECTORY,
                                               [self.language, DEFAULT])

    def get(self, domain=None, lang=None):
        if domain is None:
            domain = DOMAIN
        if lang is None:
            lang = self.language

        if domain == DOMAIN and lang == self.language:
            return self.translation.gettext

        d = gettext.translation(domain, DIRECTORY, [lang, DEFAULT])
        return d.gettext

    def get_m(self, domain=None, lang=None):
        if domain is None:
            domain = DOMAIN
        if lang is None:
            lang = self.m_language

        if domain == DOMAIN and lang == self.language:
            return self.translation.gettext

        d = gettext.translation(domain, DIRECTORY, [lang, DEFAULT])
        return d.gettext
