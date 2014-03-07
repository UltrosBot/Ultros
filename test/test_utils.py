__author__ = 'Gareth Coles'

"""
Tests for the utils module. There's a set of functions for each module..

config   - Configuration file objects
data     - Data file objects
html     - HTML utilities
irc      - Utilities for the IRC protocol
misc     - Uncategorised utilities
password - Password generation utilities
strings  - String manipulation utilities
"""

# Imports

import time
import sys

import nose.tools as nosetools
from utils import irc, misc, password, strings, html, console
# config, data, html,


class test_utils:
    """
    Test modules in the utils package
    """

    # Config

    # Console

    if sys.stdout.isatty():
        def test_console(self):
            """
            Test console size retrieval (when we are a TTY)
            """
            data = console.getTerminalSize()
            nosetools.assert_true(isinstance(data, tuple))
            nosetools.assert_true(isinstance(data[0], int))
            nosetools.assert_true(isinstance(data[1], int))
    else:
        @nosetools.raises(Exception)
        def test_console(self):
            """
            Test console size retrieval (when we are *NOT* a TTY)
            """
            console.getTerminalSize()

    # Data

    # HTML

    def test_html_parse(self):
        """
        Test HTML parser with HTML
        """

        result = html.html_to_text("<html><body>Some body that I used to "
                                   "know</body>")
        result_two = html.html_to_text("<html><body>Some body that I used to "
                                       "<br />know</body>")
        result_three = html.html_to_text("<html><body>Some body that I used to"
                                         " <p>know</p></body>")

        result_newlines = html.html_to_text("<html><body>Some body that I used"
                                            " to know</body>", newlines=True)
        result_newlines_two = html.html_to_text("<html><body>Some body that I "
                                                "<br />used to know</body>",
                                                newlines=True)
        result_newlines_three = html.html_to_text("<html><body>Some body that "
                                                  "I <p>used to know</p>"
                                                  "</body>",
                                                  newlines=True)

        nosetools.eq_(result, "Some body that I used to know")
        nosetools.eq_(result_two, "Some body that I used to know")
        nosetools.eq_(result_three, "Some body that I used to know")
        nosetools.eq_(result_newlines, "Some body that I used to know")
        nosetools.eq_(result_newlines_two, "Some body that I \nused to know")
        nosetools.eq_(result_newlines_three, "Some body that I "
                                             "\nused to know\n")

    def test_html_noparse(self):
        """
        Test HTML parser without HTML
        """

        result = html.html_to_text("Some body that I used to "
                                   "know")
        result_newlines = html.html_to_text("Some body that I used"
                                            " to know", newlines=True)

        result_newlines_two = html.html_to_text("Some body that I "
                                                "\nused to know",
                                                newlines=True)
        result_newlines_three = html.html_to_text("Some body that I "
                                                  "\nused to know\n",
                                                  newlines=True)

        nosetools.eq_(result, "Some body that I used to know")
        nosetools.eq_(result_newlines, "Some body that I used to know")
        nosetools.eq_(result_newlines_two, "Some body that I \nused to know")
        nosetools.eq_(result_newlines_three, "Some body that I "
                                             "\nused to know\n")

    # IRC

    def test_irc_split_hostmask(self):
        """
        Test IRC hostmask splitting
        """

        parts = irc.split_hostmask("aaa!bbb@ccc")

        nosetools.eq_("aaa", parts[0])
        nosetools.eq_("bbb", parts[1])
        nosetools.eq_("ccc", parts[2])

    @nosetools.raises(ValueError)
    def test_irc_split_hostmask_exception(self):
        """
        Test that IRC hostmask splitting throws the right exception
        """

        irc.split_hostmask("aaa!bbbccc")

    # Misc

    def test_misc_chunker(self):
        """
        Test iterable chunker
        """

        chunks = list(misc.chunker("xxxxxx", 6))
        nosetools.eq_(chunks, ["xxxxxx"], "One chunk")

        chunks = list(misc.chunker("xxxxxx", 3))
        nosetools.eq_(chunks, ["xxx", "xxx"], "Two chunks")

        chunks = list(misc.chunker("xxxxxx", 2))
        nosetools.eq_(chunks, ["xx", "xx", "xx"], "Three chunks")

        chunks = list(misc.chunker("xxxxxx", 1))
        nosetools.eq_(chunks, ["x", "x", "x", "x", "x", "x"], "Six chunks")

    def test_misc_string_split_readable(self):
        """
        Test readable string splitter
        """

        chunks = list(misc.string_split_readable("xxxxxx", 6))
        nosetools.eq_(chunks, ["xxxxxx"], "One chunk")

        chunks = list(misc.string_split_readable("xxx xxx", 3))
        nosetools.eq_(chunks, ["xxx", "xxx"], "Two chunks")

        chunks = list(misc.string_split_readable("xx xx xx", 2))
        nosetools.eq_(chunks, ["xx", "xx", "xx"], "Three chunks")

        chunks = list(misc.string_split_readable("x x x x x x", 1))
        nosetools.eq_(chunks, ["x", "x", "x", "x", "x", "x"], "Six chunks")

    @nosetools.raises(ValueError)
    def test_misc_string_split_exception(self):
        """
        Test that the readable string splitter throws the right exception
        """

        misc.string_split_readable("word", 3)

    # Password

    def test_password_conforms(self):
        """
        Test whether passwords conform to defined specifications
        """

        digits = "0123456789"
        lower = "abcdefghijklmnopqrstuvwxyz"
        upper = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"

        num_digits = 0
        num_lower = 0
        num_upper = 0
        num_invalid = 0

        passw = password.mkpasswd(10, 3, 3, 3)
        nosetools.eq_(10, len(passw))

        for char in passw:
            if char in digits:
                num_digits += 1
            elif char in lower:
                num_lower += 1
            elif char in upper:
                num_upper += 1
            else:
                num_invalid += 1

        nosetools.assert_true(num_digits > 2)
        nosetools.assert_true(num_lower > 2)
        nosetools.assert_true(num_upper > 2)

        nosetools.eq_(0, num_invalid)

    def test_password_short_password_uniqueness(self):
        """
        Test uniqueness of short generated passwords
        """
        passwords = []
        duplicates = []

        i = 0
        while i < 1000:
            passw = password.mkpasswd()

            if passw in duplicates:
                pass
            elif passw in passwords:
                duplicates.append(passw)
                print "Found duplicate: %s" % passw
            else:
                passwords.append(passw)

            i += 1

            time.sleep(0.001)
            # Race condition, but we're using random numbers..

        print "Found %s duplicates" % len(duplicates)

        nosetools.eq_(0, len(duplicates), "1000 passwords")

    def test_password_long_password_uniqueness(self):
        """
        Test uniqueness of long generated passwords
        """
        passwords = []
        duplicates = []

        i = 0
        while i < 1000:
            passw = password.mkpasswd(30)

            if passw in duplicates:
                pass
            elif passw in passwords:
                duplicates.append(passw)
                print "Found duplicate: %s" % passw
            else:
                passwords.append(passw)

            i += 1

            time.sleep(0.001)
            # Race condition, but we're using random numbers..

        print "Found %s duplicates" % len(duplicates)

        nosetools.eq_(0, len(duplicates), "1000 passwords")

    # Strings

    def test_strings_formatter_replacements(self):
        """
        Test non-blank replacements in the string formatter
        """

        formatter = strings.EmptyStringFormatter()

        nosetools.eq_("RED", formatter.format("{RED}", RED="RED"), "Uppercase")
        nosetools.eq_("blue", formatter.format("{blue}", blue="blue"),
                      "Lowercase")
        nosetools.eq_("blue", formatter.format("{BLUE}", BLUE="blue"),
                      "Lowercase replacement")
        nosetools.eq_("BLUE", formatter.format("{blue}", blue="BLUE"),
                      "Lowercase token")
        nosetools.eq_("GrEeN", formatter.format("{GrEeN}", GrEeN="GrEeN"),
                      "Mixed case")
        nosetools.eq_("a1", formatter.format("{a1}", a1="a1"),
                      "Contains a number")

    def test_strings_formatter_blanks(self):
        """
        Test blank replacements in the string formatter
        """

        formatter = strings.EmptyStringFormatter()

        nosetools.eq_("", formatter.format("{RED}"), "Uppercase")
        nosetools.eq_("", formatter.format("{blue}"), "Lowercase")
        nosetools.eq_("", formatter.format("{GrEeN}"), "Mixed case")
        nosetools.eq_("", formatter.format("{a1}"), "Contains a number")
