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
    599: "Network Connect Timeout Error",

    # Inexcusable
    701: "Meh",
    702: "Emacs",
    703: "Explosion",
    704: "GOTO Fail",
    705: "I wrote the code and missed the necessary validation by an "
         "oversight",

    # Novelty Implementations
    710: "PHP",
    711: "Convenience Store",
    712: "NoSQL",
    719: "I Am Not a Teapot",

    # Edge cases
    720: "Unpossible",
    721: "Known Unknowns",
    722: "Unknown Unknowns",
    723: "Tricky",
    724: "This Line Should Be Unreachable",
    725: "It Works on My Machine",
    726: "It's a Feature, Not a Bug",
    727: "32 Bits is Plenty",

    # Fucking
    730: "Fucking Bower",
    731: "Fucking Rubygems",
    732: u"Fucking Unic\U0001F4A9de",
    733: "Fucking Deadlocks",
    734: "Fucking Deferreds",
    735: "Fucking IE",
    736: "Fucking Race Conditions",
    737: "FuckThreadsing",
    738: "Fucking Bundler",
    739: "Fucking Windows",

    # Meme-driven
    740: "Computer Says No",
    741: "Compiling",
    742: "A Kitten Dies",
    743: "I Thought I Knew Regular Expressions",
    744: "Y U NO Write Integration Tests?",
    745: "I Don't Always Test My Code, But When I Do, I Do It In Production",
    746: "Missed Ballmer Peak",
    747: "Motherfucking Snakes on the Motherfucking Plane",
    748: "Confounded by Ponies",
    749: "Reserved for Chuck Norris",

    # Syntax Errors
    750: "Didn't Bother to Compile It",
    753: "Syntax Error",
    754: "Too Many Semi-Colons",
    755: "Not Enough Semi-Colons",
    756: "Insufficiently Polite",
    757: "Excessively Polite",
    759: "Unexpected T_PAAMAYIM_NEKUDOTAYIM",

    # Substance-affected developer
    761: "Hungover",
    762: "Stoned",
    763: "Under-Caffeinated",
    764: "Over-Caffeinated",
    765: "Railscamp",
    766: "Sober",
    767: "Drunk",
    768: "Accidentally Took Sleeping Pills Instead Of Migraine Pills During "
         "Crunch Week",
    769: "Questionable Maturity Level",

    # Predictable problems
    771: "Cached For Too Long",
    772: "Not Cached Long Enough",
    773: "Not Cached At All",
    774: "Why Was This Cached?",
    775: "Out of Cash",
    776: "Error on the Exception",
    777: "Coincidence",
    778: "Off-By-One Error",
    779: "Off-By-Too-Many-To-Count Error",

    # Somebody else's problem
    780: "Project Owner Not Responding",
    781: "Operations",
    782: "QA",
    783: "It Was a Customer Request, Honestly",
    784: "Management, Obviously",
    785: "TPS Cover Sheet Not Attached",
    786: "Try it Now",
    787: "Further Funding Required",
    788: "Designer's Final Designs Weren't",

    # Internet crashed
    791: "The Internet Shut Down Due To Copyright Restrictions",
    792: "Climate Change-Driven Catastrophic Weather Event",
    793: "Zombie Apocalypse",
    794: "Someone Let PG Near a REPL",
    795: "#Heartbleed",
    797: "This is the Last Page Of The Internet - Go Back",
    799: "End of the World"
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
