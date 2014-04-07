__author__ = 'Gareth Coles'

import re

token_regex = r"\{[^}]*\}"
compiled = re.compile(token_regex)

numerical_regex = r"\{[0-9]{1,}\}"
numerical_compiled = re.compile(numerical_regex)


def find_tokens(input):
    return re.findall(compiled, input)


def find_numerical_tokens(input):
    return re.findall(numerical_compiled, input)
