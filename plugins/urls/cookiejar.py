__author__ = 'Gareth Coles'

from cookielib import LWPCookieJar


class ChocolateCookieJar(LWPCookieJar):
    mode = "save"  # Save, update, discard?

    def set_mode(self, mode):
        if mode not in ["discard", "save", "session", "update"]:
            raise ValueError(
                'Cookie jar mode should be one of: "discard", "save", '
                '"session", or "update"'
            )

        self.mode = mode

    def set_cookie(self, cookie):
        """
        Set a cookie, checking whether or not it should be set.
        """

        if self.mode == "discard":
            return

        c = self._cookies

        with self._cookies_lock:
            if self.mode in ("save", "session"):
                if cookie.domain not in c:
                    c[cookie.domain] = {}

                c2 = c[cookie.domain]

                if cookie.path not in c2:
                    c2[cookie.path] = {}

                c3 = c2[cookie.path]
                c3[cookie.name] = cookie
            elif self.mode == "update":
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
                    'Cookie jar mode should be one of: "discard", "save", '
                    '"session", or "update"'
                )

    def save(self, filename=None, ignore_discard=False, ignore_expires=False):
        if self.mode not in ("discard", "session"):
            return LWPCookieJar.save(self, filename, ignore_discard,
                                     ignore_expires)
