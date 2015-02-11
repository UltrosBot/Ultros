__author__ = 'Gareth Coles'

import re

from plugins.urls.handlers.handler import URLHandler

from utils.misc import str_to_regex_flags


class WebsiteHandler(URLHandler):

    name = "website"

    criteria = {
        "protocol": re.compile(u"http|https", str_to_regex_flags("iu"))
    }

    def call(self, url, context):
        # TODO: Implement
        return False
