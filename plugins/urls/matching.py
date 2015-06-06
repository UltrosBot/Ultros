__author__ = 'Gareth Coles'

import re

from utils.misc import str_to_regex_flags

# Want to play with the regex?
# See https://regex101.com/r/bD7xH7/2

regex = """(?P<prefix>[^\w\s\\n]+|)
(?P<protocol>[\w]+)
:/[/]{1,}
(?P<basic>[\w]+:[\w]+|)(?:@|)
(?P<domain>[^/:\\n\s]+|)
(?P<port>:[0-9]+|)
(?P<url>[^\s\\n]+|)"""

r = re.compile(regex, str_to_regex_flags("iux"))


def extract_urls(text):
    return re.findall(r, text)


regex_type = type(r)
