# coding=utf-8

# Special IRC chars
COLOUR = "\x03"  # Colour code
BOLD = "\x02"  # Bold code
UNDERLINE = "\x1F"  # Underline code
ITALIC = "\x1D"  # Italics code
REVERSE = "\x16"  # Reverse code
NORMAL = "\x0F"  # Normalizing code
CTCP = "\x01"  # CTCP code
BEEP = "\x07"  # Bell character

# Typical IRC colour codes - these do not contain the COLOUR constant as that
# would stop them being usable as background colours (\x03FG,BG). They are also
# all made up of 2 characters, as single characters could confuse clients if
# the message after them starts with a digit.
COLOUR_WHITE = "00"
COLOUR_BLACK = "01"
COLOUR_BLUE = "02"
COLOUR_GREEN = "03"
COLOUR_RED_LIGHT = "04"
COLOUR_BROWN = "05"
COLOUR_PURPLE = "06"
COLOUR_ORANGE = "07"
COLOUR_YELLOW = "08"
COLOUR_GREEN_LIGHT = "09"
COLOUR_CYAN = "10"
COLOUR_CYAN_LIGHT = "11"
COLOUR_BLUE_LIGHT = "12"
COLOUR_PINK = "13"
COLOUR_GREY = "14"
COLOUR_GREY_LIGHT = "15"