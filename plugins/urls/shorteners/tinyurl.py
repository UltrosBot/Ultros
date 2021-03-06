# coding=utf-8

__author__ = 'Gareth Coles'

from txrequests import Session

from plugins.urls.shorteners.base import Shortener


class TinyURLShortener(Shortener):
    base_url = "http://tinyurl.com/api-create.php"
    name = "tinyurl"

    def do_shorten(self, context):
        session = Session()

        params = {"url": unicode(context["url"])}

        d = session.get(self.base_url, params=params)

        d.addCallbacks(
            self.shorten_success, self.shorten_error
        )

        return d

    def shorten_success(self, response):
        """
        :type response: requests.Response
        """

        return response.text

    def shorten_error(self, error):
        """
        :type error: twisted.python.failure.Failure
        """

        self.urls_plugin.logger.warning(
            "[TinyURL] Error fetching URL: {0}".format(error.getErrorMessage())
        )

        return error
