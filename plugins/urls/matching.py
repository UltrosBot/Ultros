__author__ = 'Gareth Coles'

import re

from utils.misc import str_to_regex_flags

# Want to play with the regex?
# See https://regex101.com/r/bD7xH7/2

_regex = """(?P<prefix>[^\w\s\\n]+|)
(?P<protocol>[\w]+)
:/[/]{1,}
(?P<basic>[\w]+:[\w]+|)(?:@|)
(?P<domain>[^/:\\n\s]+|)
(?P<port>:[0-9]+|)
(?P<url>[^\s\\n]+|)"""

_r = re.compile(_regex, str_to_regex_flags("iux"))


def extract_urls(text):
    return re.findall(_r, text)


def is_url(text):
    return re.match(_r, text)


REGEX_TYPE = type(_r)
