__author__ = 'Gareth Coles'

from cookielib import LWPCookieJar


class ChocolateCookieJar(LWPCookieJar):
    mode = "save"  # Save, update, discard?

    def set_mode(self, mode):
        self.mode = mode

    def set_cookie(self, cookie):
        """Set a cookie, without checking whether or not it should be set."""
        if self.mode == "discard":
            return

        c = self._cookies
        self._cookies_lock.acquire()
        try:
            if self.mode in ("save", "session"):
                if cookie.domain not in c:
                    c[cookie.domain] = {}

                c2 = c[cookie.domain]

                if cookie.path not in c2:
                    c2[cookie.path] = {}

                c3 = c2[cookie.path]
                c3[cookie.name] = cookie
            else:
                if cookie.domain not in c:
                    return

                c2 = c[cookie.domain]

                if cookie.path not in c2:
                    return

                c3 = c2[cookie.path]

                if cookie.name not in c3:
                    return

                c3[cookie.name] = cookie
        finally:
            self._cookies_lock.release()

    def save(self, filename=None, ignore_discard=False, ignore_expires=False):
        if self.mode not in ("discard", "session"):
            return LWPCookieJar.save(self, filename, ignore_discard,
                                     ignore_expires)
