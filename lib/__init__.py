"""
Some library files we need to download but shouldn't really
be distributing.
"""

from collections import OrderedDict

import importlib
import os
import urllib2

tests = OrderedDict()

tests["socks.py"] = {
    "module": "socks",
    "url": "http://socksipy-branch.googlecode.com/svn/branches/1.00/"
           "socks.py",
    "name": "SocksiPy"
}
tests["socksipyhandler.py"] = {
    "module": "socksipyhandler",
    "url": "https://gist.githubusercontent.com/e000/869791/raw/"
           "7d579998d384ba72711f2ce0caf78e8566da5864/socksipyhandler.py",
    "name": "SocksiPyHandler"
}

print "Checking for libraries to download.."

tried = 0
downloaded = 0
failed = 0

for key in tests.keys():
    if not os.path.exists("lib/%s" % key):
        tried += 1

        print ">> Downloading library: %s" % tests[key]["name"]
        try:
            rq = urllib2.urlopen(tests[key]["url"])
        except Exception as e:
            print "[ERROR] %s" % e
            print "[ERROR] Please report this to the developers. Attempted " \
                  "URL: %s" % tests[key]["url"]
            print ""
            failed += 1
        else:
            try:
                fh = open("lib/%s" % key, "w")
                fh.write(rq.read())
                fh.flush()
                fh.close()
            except Exception as e:
                print "[ERROR] Unable to write file: %s" % e
                print "[ERROR] Do you have write access to this file?"
                print ""
                failed += 1
            else:
                try:
                    module = __import__("lib.%s" % tests[key]["module"])
                except Exception as e:
                    print "[ERROR] Unable to import module: %s" % e
                    print "[ERROR] Please report this to the developers."
                    print ""
                    failed += 1
                else:
                    downloaded += 1

if not tried:
    print ">> All libraries are present. Nothing to do."
else:
    print ""
    print ">> Done - %s failed / %s succeeded" % (failed, downloaded)

socks = importlib.import_module("lib.socks")
SocksiPyHandler = importlib.import_module(
    "lib.socksipyhandler"
).SocksiPyHandler

print ""
