#!/usr/bin/env python
# coding=utf-8

"""
Packages manager for Ultros. Pulls package info and files from the
Ultros-contrib repo, which can be found at the following link..

https://github.com/McBlockitHelpbot/Ultros-contrib

In the root of the repo is a packages.yml files containing information on each
of the available packages. Sub-folders in the repo contain the actual
packages, including their information and version history files.
"""
import traceback

__author__ = 'Gareth Coles'

import os
import sys
import tempfile
import urllib

if os.path.dirname(sys.argv[0]):
    os.chdir(os.path.dirname(sys.argv[0]))

try:
    import pip
except ImportError:
    url = "https://raw.github.com/pypa/pip/master/contrib/get-pip.py"
    print "Installing pip.."
    print ""
    r = urllib.urlopen(url)
    d = r.read()
    exec d
    import pip  # flake8: noqa
    print ""

from utils.packages.packages import Packages
from utils.misc import string_split_readable

operations = ["install", "update", "uninstall", "list", "list-installed",
              "info", "help", "setup"]


def output_help():
    """
    Print the commandline help info.
    :return: None
    """

    print "Usage: python packages.py <operation> [arguments]"
    print ""
    print "=== Management operations ==="
    print "install <package>        Install a package"
    print "update <package>         Update a package"
    print "update all               Update all packages"
    print "uninstall <package>      Remove a package"
    print ""
    print "setup                    Sets up Ultros' dependencies"
    print ""
    print "=== Informational operations ==="
    print "list                     List all available packages"
    print "list-installed           List only installed packages"
    print "info <package>           Show information for a package"
    print ""
    print "=== Other operations ==="
    print "help                     Show this help message"


def main(args):
    """
    Run the package manager. This will parse commandline arguments and action
    them.

    :param args: Command-line arguments
    :type args: list
    :return: None
    """

    if not args:
        print ">> Please specify an operation"
        print ""
        print "=============================="
        print ""
        output_help()
        exit(1)

    operation = args[0]

    if not operation.lower() in operations:
        print ">> Unknown operation: %s" % operation
        print ""
        print "=============================="
        print ""
        output_help()
        exit(1)

    operation = operation.lower()

    def get_packages(get=True):
        if get:
            print ">> Downloading package list.."

        try:
            _packages = Packages(get)
        except Exception as e:
            print ">> Error retrieving packages - %s" % e
            return exit(1)

        if get:
            print ">> Found %s package(s)." % len(_packages)

        return _packages

    if operation == "help":
        output_help()
        return exit(0)

    elif operation == "list":
        packages = get_packages()
        _list(args, packages)

    elif operation == "list-installed":
        packages = get_packages(False)
        _list_installed(args, packages)

    elif operation == "info":
        packages = get_packages()
        info(args, packages)

    elif operation == "install":
        packages = get_packages()
        install(args, packages)

    elif operation == "uninstall":
        packages = get_packages()
        uninstall(args, packages)

    elif operation == "setup":
        setup()

    elif operation == "update":
        packages = get_packages()
        if len(args) > 1 and args[1] == "all":
            if not len(packages.config["installed"].keys()):
                print ">> No packages are installed. Nothing to do."
                exit(0)
            for package in packages.config["installed"].keys():
                args[1] = package

                uninstall(args, packages)
                install(args, packages)
        else:
            uninstall(args, packages)
            install(args, packages)
    else:
        print ">> This isn't implemented yet, go bitch at the developers!"


def _list(args, packages):
    print ""
    print "+%s+%s+%s+" % ("-" * 17, "-" * 7, "-" * 82)
    print "| %s | %s | %s |" % ("Name".ljust(15), "Vers.",
                                "Description".ljust(80))
    print "+%s+%s+%s+" % ("-" * 17, "-" * 7, "-" * 82)
    for x in packages.packages:
        package = packages.data[x]
        version = package["version"]
        desc = package["description"]

        chunks = string_split_readable(desc, 80)
        i = False
        for chunk in chunks:
            if not i:
                print "| %s | %s | %s |" % (x.ljust(15), version.ljust(5),
                                            chunk.ljust(80))
                i = True
            else:
                print "| %s | %s | %s |" % ("".ljust(15), "".ljust(5),
                                            chunk.ljust(80))

        if package["requires"]["modules"]:
            needed = "Needed modules: %s" \
                     % (", ".join(package["requires"]["modules"]))
            chunks = string_split_readable(needed, 78)
            for chunk in chunks:
                print "| %s | %s | > %s |" % ("".ljust(15), "".ljust(5),
                                              chunk.ljust(78))

        if package["requires"]["packages"]:
            needed = "Needed packages: %s" \
                     % (", ".join(package["requires"]["packages"]))
            chunks = string_split_readable(needed, 78)
            for chunk in chunks:
                print "| %s | %s | > %s |" % ("".ljust(15), "".ljust(5),
                                              chunk.ljust(78))
    print "+%s+%s+%s+" % ("-" * 17, "-" * 7, "-" * 82)


def _list_installed(args, packages):
    print ""
    print "+%s+%s+" % ("-" * 17, "-" * 7)
    print "| %s | %s |" % ("Name".ljust(15), "Vers.")
    print "+%s+%s+" % ("-" * 17, "-" * 7)
    for x in packages.get_installed_packages().keys():
        version = packages.get_installed_packages()[x]

        print "| %s | %s |" % (x.ljust(15), version.ljust(5))

    print "+%s+%s+" % ("-" * 17, "-" * 7)


def install(args, packages):
    if len(args) < 2:
        print ">> Syntax: 'python packages.py install <package>'"
        print ">> Try 'python packages.py help' if you're stuck"
        return exit(1)

    package = args[1]

    print ">> Installing package '%s'." % package

    if packages.package_installed(package):
        print ">> Package is already installed. Nothing to do."
        return exit(1)

    try:
        conflicts = packages.install_package(package)
    except Exception as e:
        print ">> Error installing package: %s" % e
        exc_type, exc_value, exc_traceback = sys.exc_info()
        data = traceback.format_exception(exc_type, exc_value,
                                          exc_traceback)
        print "==============================="
        print " ".join(data)
        return exit(1)
    print ">> Version %s installed successfully." \
          % packages.config["installed"][package]
    files = conflicts["files"]
    folders = conflicts["folders"]
    if len(files) or len(folders):
        print ">> The following conflicts were found."
        if len(folders):
            print "   | Directories: %s" % len(folders)
            for path in folders:
                print "   + %s" % path
        if len(files):
            print "   | Files: %s" % len(folders)
            for path in files:
                print "   + %s" % path
        print ">> These files were not modified but may be removed if " \
              "you uninstall the package."


def uninstall(args, packages):
    if len(args) < 2:
        print ">> Syntax: 'python packages.py uninstall <package>'"
        print ">> Try 'python packages.py help' if you're stuck"
        return exit(1)

    package = args[1]

    print ">> Uninstalling package '%s'." % package

    if not packages.package_installed(package):
        print ">> Package is not installed. Nothing to do."
        return exit(1)

    try:
        packages.uninstall_package(package)
    except Exception as e:
        print ">> Error uninstalling package: %s" % e
        return exit(1)
    print ">> Package uninstalled successfully."


def info(args, packages):
    if len(args) < 2:
        print ">> Syntax: 'python packages.py info <package>'"
        print ">> Try 'python packages.py help' if you're stuck"
        return exit(1)

    package = args[1]

    if package not in packages.data:
        print ">> Package not found: %s" % package
        return exit(1)

    print ">> Downloading information.."

    info = packages.get_package_info(package)
    versions = packages.get_package_versions(package)

    print ""
    print "=== Information ==="
    print "Name: %s" % info["name"]
    print "Latest version: v%s" % info["current_version"]["number"]
    if packages.package_installed(package):
        print "Installed: v%s" % packages.config["installed"][package]
    print "Files: %s" % len(info["files"])
    print "Documentation: %s" % info["documentation"]
    print ""
    print "=== Description ==="
    print info["description"]
    print "=== Latest version ==="
    print "Version: %s" % info["current_version"]["number"]
    print "- %s other versions." % len(versions.keys())
    print ""
    print info["current_version"]["info"]


def setup():
    windows = os.name == "nt"

    if not windows:
        pip.main(["install", "-r", "requirements.txt"])

        print ">> Presuming everything installed okay, you should now be " \
              "ready to run Ultros!"
    else:
        reqs = open("requirements.txt", "r").read()
        reqs = reqs.replace("\r", "")
        reqs = reqs.split()

        if "" in reqs:
            reqs.remove("")

        for x in ["pyopenssl", "twisted"]:
            if x in reqs:
                reqs.remove(x)

        urls = {
            "Twisted": [
                ["https://pypi.python.org/packages/2.7/T/Twisted/Twisted-"
                 "13.2.0.win32-py2.7.msi", "twisted.msi"]
            ],
            "OpenSSL and PyOpenSSL": [
                ["http://slproweb.com/download/Win32OpenSSL-1_0_1g.exe",
                 "openssl.exe"],
                ["https://pypi.python.org/packages/2.7/p/pyOpenSSL/pyOpenSSL-0"
                 ".13.1.win32-py2.7.exe", "pyopenssl.exe"]
            ]
        }

        pip.main(["install"] + reqs)

        print ""
        print ">> There are some things pip can't install."
        print ">> I will now attempt to download and install them manually."
        print ">> Please be ready to click through dialogs!"
        print ">> Please note, these files only work with Python 2.7!"
        print ""

        tempdir = tempfile.gettempdir()

        print ">> Files will be downloaded to %s" % tempdir
        print ""
        print ">> OpenSSL will complain about a command prompt being open."
        print ">> This is fine, just click \"OK\" to continue."
        print ""

        for k in urls.keys():
            print ">> Downloading files for %s" % k

            files = urls[k]

            for x in files:
                print " -> %s" % x[1]

                try:
                    urllib.urlretrieve(x[0], tempdir + "/ultros." + x[1])

                    os.system(tempdir + "/ultros." + x[1])
                finally:
                    os.remove(tempdir + "/ultros." + x[1])

        print ">> Presuming everything installed okay, you should now be " \
              "ready to run Ultros!"

if __name__ == "__main__":
    args = sys.argv[1:]
    main(args)
