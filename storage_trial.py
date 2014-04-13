__author__ = 'Gareth Coles'

import os

from system.storage.manager import StorageManager
from plugins.dialectizer import Plugin
from system.storage.formats import *
from twisted.internet import reactor

if os.path.exists("data/test.sqlite"):
    os.remove("data/test.sqlite")

i = StorageManager()
d = Plugin()
f = i.get_file(d, "data", DBAPI, "sqlite3:data/test.sqlite",
               "data/test.sqlite", check_same_thread=False)

print f


done = False


def printout(r):
    print r

    done = True


def find(r):
    with f as c:
        c.runQuery("SELECT * FROM urls").addCallback(printout)


def insert(r):
    with f as c:
        c.runOperation("INSERT INTO urls VALUES (?, ?, ?)",
                       ("http://herp.derp",
                        "tinyurl",
                        "http://tinyurl.com/herp.derp")).addCallback(find)

with f as c:
    c.runOperation("""CREATE TABLE IF NOT EXISTS urls (url TEXT,
                      shortener TEXT, result TEXT)""").addCallback(insert)

reactor.run()
