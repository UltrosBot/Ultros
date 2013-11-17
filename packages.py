"""
Packages manager for Ultros. Pulls package info and files from the
Ultros-contrib repo, which can be found at the following link..

https://github.com/McBlockitHelpbot/Ultros-contrib

In the root of the repo is a packages.yml files containing information on each
of the available packages. Sub-folders in the repo contain the actual
packages, including their information and version history files.
"""

__author__ = 'Gareth Coles'

import sys
import urllib

try:
    import pip
except ImportError:
    url = "https://raw.github.com/pypa/pip/master/contrib/get-pip.py"
    print "Installing pip.."
    print ""
    r = urllib.urlopen(url)
    d = r.read()
    exec d
    import pip
    print ""

from utils.packages.packages import Packages

operations = ["install", "update", "uninstall", "list", "list-installed",
              "info", "help"]


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
    print "uninstall <package>      Remove a package"
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

    print ">> Downloading package list.."

    try:
        packages = Packages()
    except Exception as e:
        print ">> Error retrieving packages - %s" % e
        return exit(1)

    print ">> Found %s package(s)." % len(packages)

    operation = operation.lower()

    if operation == "help":
        output_help()
        return exit(0)
    elif operation == "list":
        for x in packages.packages:
            package = packages.data[x]
            print ""
            print "%s v%s: %s" % (x, package["version"],
                                  package["description"])

            if package["requires"]["modules"]:
                print "- Required modules: %s" \
                      % (", ".join(package["requires"]["modules"]))

            if package["requires"]["packages"]:
                print "- Required packages: %s" \
                      % (", ".join(package["requires"]["packages"]))
    elif operation == "info":
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
    elif operation == "install":
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
            packages.install_package(package)
        except Exception as e:
            print ">> Error installing package: %s" % e
            return exit(1)
        print ">> Version %s installed successfully." \
              % packages.config["installed"][package]
    elif operation == "uninstall":
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

if __name__ == "__main__":
    args = sys.argv[1:]
    main(args)
