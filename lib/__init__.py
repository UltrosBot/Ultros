"""
Some library files we need to download but shouldn't really
be distributing.
"""

import json
import importlib
import os
import urllib2


def get_libs():
    print ">> Checking for libraries to download.."

    definitions = os.listdir("lib/definitions")

    tried = 0
    downloaded = 0
    failed = 0
    exists = 0

    for filename in definitions:
        if not filename.endswith(".json"):
            print "Unknown definition file type: %s" % filename

        try:
            fh = open("lib/definitions/%s" % filename, "r")
            tests = json.load(fh)
            packs = tests["packages"]
        except Exception as e:
            print "[ERROR] Unable to load definitions file %s - %s" % e
        else:
            for pack in packs:
                if not os.path.exists("lib/%s" % pack["filename"]):
                    tried += 1

                    print ">> Downloading library: %s" % pack["name"]
                    print " > Attribution: %s" % pack["attrib"]

                    if "." in pack["module"]:
                        folders = pack["module"].split(".")
                        folders.pop()

                        path = "lib/%s" % "/".join(folders)

                        try:
                            if not os.path.exists(path):
                                os.makedirs(path)

                                current_path = "lib/"

                                for folder in folders:
                                    current_path += (folder + "/")
                                    open("%s/__init__.py" % current_path, "w")

                        except Exception as e:
                            print "[ERROR] Unable to create path %s - %s" \
                                  % (path, e)
                            continue

                    try:
                        rq = urllib2.urlopen(pack["url"])
                    except Exception as e:
                        print "[ERROR] %s" % e
                        print "[ERROR] Please report this to the developers." \
                              " Attempted URL: %s" % pack["url"]
                        print ""
                        failed += 1
                    else:
                        try:
                            fh = open("lib/%s" % pack["filename"], "w")

                            data = rq.read()
                            data = data.replace("\r\n", "\n")

                            fh.write(data)
                            fh.flush()
                            fh.close()
                        except Exception as e:
                            print "[ERROR] Unable to write file: %s" % e
                            print "[ERROR] Do you have write access to this " \
                                  "file?"
                            print ""
                            failed += 1
                        else:
                            try:
                                importlib.import_module(
                                    "lib.%s" % pack["module"]
                                )
                            except Exception as e:
                                print "[ERROR] Unable to import module: %s" % e
                                print "[ERROR] Please report this to the " \
                                      "developers."
                                print ""
                                failed += 1
                            else:
                                downloaded += 1
                else:
                    exists += 1

    if not tried:
        print ">> All libraries are present. Nothing to do."
    else:
        print ""
        print ">> Done - %s failed / %s succeeded" % (failed, downloaded)

    print ""

    return {"tried": tried, "downloaded": downloaded,
            "failed": failed, "exists": exists}

get_libs()
