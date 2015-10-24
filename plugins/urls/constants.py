# coding=utf-8

__author__ = "Gareth Coles"

STATUS_CODES = {
    # Informational
    100: "Continue",
    101: "Switching Protocols",
    102: "Processing",

    # Success
    200: "OK",
    201: "Created",
    202: "Accepted",
    203: "Non-Authoritative Information",
    204: "No Content",
    205: "Reset Content",
    206: "Partial Content",
    207: "Multi-Status",
    208: "Already Reported",
    226: "IM Used",

    # Redirection
    300: "Multiple Choices",
    301: "Moved Permanently",
    302: "Found",
    303: "See Other",
    304: "Not Modified",
    305: "Use Proxy",
    306: "Switch Proxy",
    307: "Temporary Redirect",
    308: "Permanent Redirect / Resume Incomplete",

    # Client Error
    400: "Bad Request",
    401: "Unauthorized",
    402: "Payment Required",
    403: "Forbidden",
    404: "Not Found",
    405: "Method Not Allowed",
    406: "Not Acceptable",
    407: "Proxy Authentication Required",
    408: "Request Timeout",
    409: "Conflict",

    410: "Gone",
    411: "Length Required",
    412: "Precondition Failed",
    413: "Request Entity Too Large",
    414: "Request-URI Too Long",
    415: "Unsupported Media Type",
    416: "Requested Range Not Satisfiable",
    417: "Expectation Failed",
    418: "I'm a Teapot",
    419: "Authentication Timeout",

    420: "Method Failure / Enhance Your Calm",
    421: "Misdirected Request",
    422: "Unprocessable Entity",
    423: "Locked",
    424: "Failed Dependency",
    426: "Upgrade Required",
    428: "Precondition Required",
    429: "Too Many Requests",

    431: "Request Header Fields Too Large",

    440: "Login Timeout",
    444: "No Response",
    449: "Retry With",

    450: "Blocked by Windows Parental Controls",
    451: "Redirect / Unavailable for Legal Reasons",

    494: "Request Header Too Large",
    495: "Cert Error",
    496: "No Cert",
    497: "HTTP to HTTPS",
    498: "Token expired/invalid",
    499: "Token Required / Client Closed Request",

    # Server Error
    500: "Internal Server Error",
    501: "Not Implemented",
    502: "Bad Gateway",
    503: "Service Unavailable",
    504: "Gateway Timeout",
    505: "HTTP Version Not Supported",
    506: "Variant Also Negotiates",
    507: "Insufficient Storage",
    508: "Loop Detected",
    509: "Bandwidth Limit Exceeded",

    510: "Not Extended",
    511: "Network Authentication Required",

    520: "Unknown Error",

    598: "Network Read Timeout Error",
    599: "Network Connect Timeout Error"
}

PREFIX_TRANSLATIONS = {
    # "Normal" bracket types

    u"(": u")",
    u"[": u"]",
    u"{": u"}",
    u"<": u">",

    # Angle brackets and chevrons

    u"⟨": u"⟩",
    u"〈": u"〉",
    u"《": u"》",

    # Guillemet

    u"‹": u"›",
    u"«": u"»",

    # Floor and ceiling

    u"⌊": u"⌋",
    u"⌈": u"⌉",

    # Quine corners

    u"⌜": u"⌝",

    # Half-brackets

    u"⸤": u"⸥",
    u"⸢": u"⸣",

    # Double/Strachey brackets

    u"⟦": u"⟧",

    # Swedish piggparenteser (mouse parentheses)

    u"⁅": u"⁆",

    # Asian

    u"「": u"」",
    u"﹁": u"﹂",
    u"『": u"』",
    u"﹃": u"﹄",
    u"【": u"】",
    u"（": u"）",
    u"［": u"］",
    u"＜": u"＞",
    u"｛": u"｝",

    # Large parenthesis parts

    u"⎛": u"⎞",
    u"⎜": u"⎟",
    u"⎝": u"⎠",

    # Large square bracket parts

    u"⎡": u"⎤",
    u"⎣": u"⎦",

    # Large curly brace parts

    u"⎧": u"⎫",
    u"⎨": u"⎬",
    u"⎩": u"⎭",

    # Other quotation marks

    u"„": u"”",
    u"‚": u"’",
}

COOKIE_MODE_DISCARD = "discard"
COOKIE_MODE_SAVE = "save"
COOKIE_MODE_SESSION = "session"
COOKIE_MODE_UPDATE = "update"

COOKIE_MODES = [COOKIE_MODE_DISCARD, COOKIE_MODE_SAVE,
                COOKIE_MODE_SESSION, COOKIE_MODE_UPDATE]
