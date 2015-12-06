#!/usr/bin/env python
# coding=utf-8

__author__ = 'Gareth Coles'

"""
Packages manager for Ultros. Pulls package info and files from the
Ultros-contrib repo, which can be found at the following link..

https://github.com/McBlockitHelpbot/Ultros-contrib

In the root of the repo is a packages.yml files containing information on each
of the available packages. Sub-folders in the repo contain the actual
packages, including their information and version history files.
"""
import argparse
import os
import sys
import traceback

is_64bits = sys.maxsize > 2 ** 32

if os.path.dirname(sys.argv[0]):
    os.chdir(os.path.dirname(sys.argv[0]))

from system.translations import Translations

DESC = "The Ultros package manager"

operations = ["install", "update", "uninstall", "list", "list-installed",
              "info", "setup"]
if __name__ == "__main__":
    p = argparse.ArgumentParser(description=DESC)
    p.add_argument("-l", "--language", help="Specify which language to use")
    p.add_argument(
        "-ow",
        "--overwrite",
        action="store_true",
        help="Overwrite already-installed packages"
    )
    p.add_argument("operation", help="Specify what to do.", choices=operations)
    p.add_argument("target", nargs="?", default=None)

    args = p.parse_args()
    trans = Translations(args.language, log=False)
else:
    trans = Translations(log=False)

_ = trans.get()

import tempfile
import urllib

try:
    import pip
except ImportError:
    url = "https://raw.github.com/pypa/pip/master/contrib/get-pip.py"
    print(_("Installing pip.."))
    print("")
    r = urllib.urlopen(url)
    d = r.read()

    _args = sys.argv
    sys.argv = []
    try:
        exec d
    except SystemExit:
        pass

    sys.argv = _args
    import pip  # flake8: noqa
    print("")

try:
    from utils.packages.packages import Packages
except ImportError:
    Packages = None

from utils.misc import string_split_readable


def get_packages(get=True):
    if Packages is None:
        print(_(">> You need to run the setup steps first!"))
        return exit(1)
    if get:
        print(_(">> Downloading package list.."))

    try:
        _packages = Packages(get)
    except Exception as e:
        print(_(">> Error retrieving packages - %s") % e)
        return exit(1)

    if get:
        print(_(">> Found %s package(s).") % len(_packages))

    return _packages


def main():
    """
    Run the package manager. This will parse commandline arguments and action
    them.

    :return: None
    """

    operation = args.operation
    operation = operation.lower()

    if args.target is None:
        _args = [operation]
    else:
        _args = [operation, args.target]

    if operation == "list":
        packages = get_packages()
        _list(_args, packages)

    elif operation == "list-installed":
        packages = get_packages(False)
        _list_installed(_args, packages)

    elif operation == "info":
        packages = get_packages()
        info(_args, packages)

    elif operation == "install":
        packages = get_packages()
        install(_args, packages)

    elif operation == "uninstall":
        packages = get_packages()
        uninstall(_args, packages)

    elif operation == "setup":
        setup()

    elif operation == "update":
        packages = get_packages()
        if len(_args) > 1 and _args[1] == "all":
            if not len(packages.config["installed"].keys()):
                print _(">> No packages are installed. Nothing to do.")
                exit(0)
            for package in packages.config["installed"].keys():
                _args[1] = package

                if not args.overwrite:
                    uninstall(_args, packages)
                    install(_args, packages)
                else:
                    install(_args, packages, True)

        else:
            if not args.overwrite:
                uninstall(_args, packages)
                install(_args, packages)
            else:
                install(_args, packages, True)
    else:
        print _(">> Unknown operation: %s") % operation


def _list(args, packages):
    print ""
    print "+%s+%s+%s+" % ("-" * 17, "-" * 7, "-" * 82)
    print "| %s | %s | %s |" \
          % (_("Name").ljust(15), _("Version").ljust(10),
             _("Description").ljust(75))
    print "+%s+%s+%s+" % ("-" * 17, "-" * 12, "-" * 77)
    for x in packages.packages:
        package = packages.data[x]
        version = package["version"]
        desc = package["description"]

        chunks = string_split_readable(desc, 75)
        i = False
        for chunk in chunks:
            if not i:
                print "| %s | %s | %s |" % (x.ljust(15), version.ljust(10),
                                            chunk.ljust(75))
                i = True
            else:
                print "| %s | %s | %s |" % ("".ljust(15), "".ljust(10),
                                            chunk.ljust(75))

        if package["requires"]["modules"]:
            needed = _("Needed modules: %s") \
                     % (", ".join(package["requires"]["modules"]))
            chunks = string_split_readable(needed, 78)
            for chunk in chunks:
                print "| %s | %s | > %s |" % ("".ljust(15), "".ljust(10),
                                              chunk.ljust(73))

        if package["requires"]["packages"]:
            needed = _("Needed packages: %s") \
                     % (", ".join(package["requires"]["packages"]))
            chunks = string_split_readable(needed, 78)
            for chunk in chunks:
                print "| %s | %s | > %s |" % ("".ljust(15), "".ljust(10),
                                              chunk.ljust(73))
    print "+%s+%s+%s+" % ("-" * 17, "-" * 7, "-" * 82)


def _list_installed(args, packages):
    print ""
    print "+%s+%s+" % ("-" * 17, "-" * 7)
    print "| %s | %s |" % (_("Name").ljust(15), _("Version").ljust(10))
    print "+%s+%s+" % ("-" * 17, "-" * 12)
    for x in packages.get_installed_packages().keys():
        version = packages.get_installed_packages()[x]

        print "| %s | %s |" % (x.ljust(15), version.ljust(10))

    print "+%s+%s+" % ("-" * 17, "-" * 12)


def install(args, packages, overwrite=False):
    if len(args) < 2:
        print _(">> Syntax: 'python packages.py install <package>'")
        print _(">> Try 'python packages.py -h' if you're stuck")
        return exit(1)

    package = args[1]

    print _(">> Installing package '%s'.") % package

    if packages.package_installed(package) and not overwrite:
        print _(">> Package is already installed. Nothing to do.")
        return exit(1)

    try:
        conflicts = packages.install_package(package, overwrite)
    except Exception as e:
        print _(">> Error installing package: %s") % e
        exc_type, exc_value, exc_traceback = sys.exc_info()
        data = traceback.format_exception(exc_type, exc_value,
                                          exc_traceback)
        print "==============================="
        print " ".join(data)
        return exit(1)

    if conflicts is None:
        return

    print (_(">> Version %s installed successfully.")
           % packages.config["installed"][package])
    files = conflicts["files"]
    folders = conflicts["folders"]
    if len(files) or len(folders):
        print _(">> The following conflicts were found.")
        if len(folders):
            print "   | %s: %s" % (_("Directories"), len(folders))
            for path in folders:
                print "   + %s" % path
        if len(files):
            print "   | %s: %s" % (_("Files"), len(folders))
            for path in files:
                print "   + %s" % path
        print _(">> These files were not modified but may be removed if "
                "you uninstall the package.")


def uninstall(args, packages):
    if len(args) < 2:
        print _(">> Syntax: 'python packages.py uninstall <package>'")
        print _(">> Try 'python packages.py -h' if you're stuck")
        return exit(1)

    package = args[1]

    print _(">> Uninstalling package '%s'.") % package

    if not packages.package_installed(package):
        print _(">> Package is not installed. Nothing to do.")
        return exit(1)

    try:
        packages.uninstall_package(package)
    except Exception as e:
        print _(">> Error uninstalling package: %s") % e
        return exit(1)
    print _(">> Package uninstalled successfully.")


def info(args, packages):
    if len(args) < 2:
        print _(">> Syntax: 'python packages.py info <package>'")
        print _(">> Try 'python packages.py -h' if you're stuck")
        return exit(1)

    package = args[1]

    if package not in packages.data:
        print _(">> Package not found: %s") % package
        return exit(1)

    print _(">> Downloading information..")

    info = packages.get_package_info(package)
    versions = packages.get_package_versions(package)

    print ""
    print _("=== Information ===")
    print _("Name: %s") % info["name"]
    print _("Latest version: v%s") % info["current_version"]["number"]
    if packages.package_installed(package):
        print _("Installed: v%s") % packages.config["installed"][package]
    print _("Files: %s") % len(info["files"])
    print _("Documentation: %s") % info["documentation"]
    print ""
    print _("=== Description ===")
    print info["description"]
    print _("=== Latest version ===")
    print _("Version: %s") % info["current_version"]["number"]
    print _("- %s other versions.") % len(versions.keys())
    print ""
    print info["current_version"]["info"]


def setup(auto=False):
    windows = os.name == "nt"

    if not windows:
        pip.main(["install", "-r", "requirements.txt"])

        if not auto:
            print _(">> Presuming everything installed okay, you should now "
                    "be ready to run Ultros!")
    else:
        reqs = open("requirements.txt", "r").read()
        reqs = reqs.replace("\r", "")
        reqs = reqs.split()

        if "" in reqs:
            reqs.remove("")

        for x in ["pyopenssl", "twisted", "psutil"]:
            if x in reqs:
                reqs.remove(x)

        if not is_64bits:
            urls = {
                "Twisted": [
                    ["https://pypi.python.org/packages/2.7/T/Twisted/"
                     "Twisted-14.0.2.win32-py2.7.msi", "twisted.msi"]
                ],
                "OpenSSL and PyOpenSSL": [
                    ["https://slproweb.com/download/Win32OpenSSL-1_0_2a.exe",
                     "openssl.exe"],
                    ["https://pypi.python.org/packages/2.7/p/pyOpenSSL/"
                     "pyOpenSSL-0.13.1.win32-py2.7.exe", "pyopenssl.exe"]
                ],
                "PSUtil": [
                    ["https://pypi.python.org/packages/2.7/p/psutil/"
                     "psutil-2.1.2.win32-py2.7.exe", "psutil.exe"]
                ]
            }
        else:
            urls = {
                "Twisted": [
                    ["https://pypi.python.org/packages/2.7/T/Twisted/"
                     "Twisted-14.0.2.win-amd64-py2.7.msi", "twisted.msi"]
                ],
                "OpenSSL and PyOpenSSL": [
                    ["https://slproweb.com/download/Win64OpenSSL-1_0_1i.exe",
                     "openssl.exe"],
                    ["https://pypi.python.org/packages/2.7/p/pyOpenSSL/"
                     "pyOpenSSL-0.13.1.win-amd64-py2.7.exe", "pyopenssl.exe"]
                ],
                "PSUtil": [
                    ["https://pypi.python.org/packages/2.7/p/psutil/"
                     "psutil-2.1.2.win-amd64-py2.7.exe", "psutil.exe"]
                ]
            }

        pip.main(["install"] + reqs)

        if auto:
            print ">> This was an automatic installation."
            print ">> The following dependencies need to be installed " \
                  "manually:"

            for x in urls.keys():
                print "- %s" % x

                for u in urls[x]:
                    print "  - %s" % u
            return

        print ""
        print _(">> There are some things pip can't install.")
        print _(">> I will now attempt to download and install them manually.")
        print _(">> Please be ready to click through dialogs!")
        print _(">> Please note, these files only work with Python 2.7!")
        print ""

        tempdir = tempfile.gettempdir()

        print _(">> Files will be downloaded to %s") % tempdir
        print ""
        print _(">> OpenSSL will complain about a command prompt being open.")
        print _(">> This is fine, just click \"OK\" to continue.")
        print ""

        for k in urls.keys():
            print _(">> Downloading files for %s") % k

            files = urls[k]

            for x in files:
                print " -> %s" % x[1]

                try:
                    urllib.urlretrieve(x[0], tempdir + "/ultros." + x[1])

                    os.system(tempdir + "/ultros." + x[1])
                finally:
                    try:
                        os.remove(tempdir + "/ultros." + x[1])
                    except Exception as e:
                        print ">> Unable to remove file: %s" \
                              % tempdir + "/ultros." + x[1]
                        print ">> %s" % e

        print _(">> Presuming everything installed okay, you should now be "
                "ready to run Ultros!")

if __name__ == "__main__":
    main()
