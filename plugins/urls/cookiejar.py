# coding=utf-8

from cookielib import MozillaCookieJar
from plugins.urls.constants import COOKIE_MODES, COOKIE_MODE_DISCARD, \
    COOKIE_MODE_SESSION, COOKIE_MODE_SAVE, COOKIE_MODE_UPDATE

__author__ = 'Gareth Coles'


class ChocolateCookieJar(MozillaCookieJar):
    # Because chocolate cookies are /clearly/ better

    mode = "save"  # Save, update, discard?

    def set_mode(self, mode):
        if mode not in COOKIE_MODES:
            raise ValueError(
                'Cookie jar mode should be one of: {}'.format(
                    ", ".join(COOKIE_MODES)
                )
            )

        self.mode = mode

    def set_cookie(self, cookie):
        """
        Set a cookie, checking whether or not it should be set.
        """

        if self.mode == COOKIE_MODE_DISCARD:
            return

        c = self._cookies

        with self._cookies_lock:
            if self.mode in (COOKIE_MODE_SAVE, COOKIE_MODE_SESSION):
                if cookie.domain not in c:
                    c[cookie.domain] = {}

                c2 = c[cookie.domain]

                if cookie.path not in c2:
                    c2[cookie.path] = {}

                c3 = c2[cookie.path]
                c3[cookie.name] = cookie
            elif self.mode == COOKIE_MODE_UPDATE:
                if cookie.domain not in c:
                    return

                c2 = c[cookie.domain]

                if cookie.path not in c2:
                    return

                c3 = c2[cookie.path]

                if cookie.name not in c3:
                    return

                c3[cookie.name] = cookie
            else:
                raise ValueError(
                    'Cookie jar mode should be one of: {}'.format(
                        ", ".join(COOKIE_MODES)
                    )
                )

    def save(self, filename=None, ignore_discard=False, ignore_expires=False):
        if self.mode not in ("discard", "session"):
            return LWPCookieJar.save(self, filename, ignore_discard,
                                     ignore_expires)
