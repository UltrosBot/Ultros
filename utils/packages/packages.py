"""
Classes for working with the Ultros-contrib repository

These can be used within a plugin, but they're mostly used by the package
management script.
"""

__author__ = 'Gareth Coles'

import calendar
import datetime
import os
import pip
import shutil
import urllib2
import yaml

from system.singleton import Singleton
from system.storage.formats import YAML
from system.storage.manager import StorageManager

from system.translations import Translations
_ = Translations().get()


class Packages(object):

    __metaclass__ = Singleton

    """
    Class responsible for loading up plugin info, retrieving files
    and generally handling GitHub and the filesystem.

    I was a little lazy in writing this - but plugins aren't really supposed
    to use this anyway. Of course, that doesn't mean they can't!
    """

    data = {}
    packages = []
    config = None
    storage = None

    base_file_url = "https://raw.github.com/McBlockitHelpbot/Ultros-contrib/" \
                    "master/"

    info_file = "packages.yml"
    package_info_file = "package.yml"
    package_versions_file = "versions.yml"

    def __init__(self, get=True):
        self.storage = StorageManager()
        if get:
            info_url = self.base_file_url + self.info_file
            response = urllib2.urlopen(info_url)
            data = response.read()
            self.data = yaml.load(data)
            self.packages = sorted(self.data.keys())

        self.config = self.storage.get_file(self, "data", YAML, "packages.yml")

        with self.config:
            if not "installed" in self.config:
                self.config["installed"] = {}
            if not "etags" in self.config:
                self.config["etags"] = {}

    def _get_file(self, base_path, path, overwrite=False):
        if os.path.exists(path) and not overwrite:
            raise ValueError("A file at `%s` already exists" % path)

        constructed_path = self.base_file_url + base_path + path
        etag = None

        opener = urllib2.build_opener()
        request = urllib2.Request(constructed_path)
        stream = opener.open(request)

        if "ETag" in stream.headers:
            etag = stream.headers["ETag"]

        if os.path.exists(path):
            if etag is not None and path in self.config["etags"]:
                if etag == self.config["etags"][path]:
                    raise urllib2.HTTPError(
                        constructed_path,
                        304,
                        "Matching ETag",
                        stream.headers,
                        stream
                    )

        with open(path, 'wb') as fp:
            fp.write(stream.read())
            fp.flush()

        if etag is not None:
            with self.config:
                self.config["etags"][path] = etag

    def get_installed_packages(self):
        return self.config["installed"]

    def get_package_info(self, package):
        """
        Load up the package info file for a package and return its data
        as a dict.
        :param package: Package to load data for
        :return: Dict representing the package info, otherwise None
        """
        if package in self.packages:
            url = self.base_file_url + package + "/" \
                                     + self.package_info_file

            response = urllib2.urlopen(url)
            data = response.read()

            return yaml.load(data)
        return None

    def get_package_versions(self, package):
        """
        Load up the package version history file for a package and return its
        data as a dict.
        :param package: Package to load data for
        :return: Dict representing the package versions, otherwise None
        """
        if package in self.packages:
            url = self.base_file_url + package + "/" \
                                     + self.package_versions_file

            response = urllib2.urlopen(url)
            data = response.read()

            return yaml.load(data)
        return None

    def package_installed(self, package):
        """
        Check whether a package is installed.
        :param package: The package to look for
        :return: Whether the package is installed
        """
        return package in self.config["installed"]

    def install_package(self, package, overwrite=False):
        """
        Attempt to install a package.
        :param package: The package to try to install
        :param overwrite: Whether to just overwrite an installed package
        :return: Any conflicts that were detected
        """
        if self.package_installed(package) and not overwrite:
            raise ValueError("Package '%s' is already installed"
                             % package)
        info = self.get_package_info(package)
        files = info["files"]

        conflicts = {"files": [], "folders": []}

        total_files = 0
        total_folders = 0

        for _file in files:
            if _file[-1] == "/":
                total_folders += 1
            else:
                total_files += 1

        print ">> %s files to download." % total_files

        current_file = 1
        current_folder = 1

        for _file in files:
            if _file[-1] == "/":
                if not os.path.exists(_file):
                    print ">> Folder | Creating (%s/%s): %s" % \
                          (current_folder, total_folders, _file)
                    os.mkdir(_file)
                else:
                    print ">> Folder | Already exists (%s/%s): %s" % \
                          (current_folder, total_folders, _file)
                    path = _file
                    if not overwrite:
                        conflicts["folders"].append(path)
                current_folder += 1
            else:
                if not os.path.exists(_file) or overwrite:
                    try:
                        self._get_file(package + "/", _file, overwrite)
                        print ">>   File | Downloaded (%s/%s): %s" % \
                            (current_file, total_files, _file)
                    except urllib2.HTTPError as e:
                        if e.code == 304:
                            print ">>   File | Skipping (%s/%s): %s " \
                                  "[Matching ETag]" % \
                                (current_file, total_files, _file)
                        else:
                            print ">>   File | Failed (%s/%s): %s" % \
                                  (current_file, total_files, _file)
                            raise
                else:
                    print ">>   File | Conflict (%s/%s): %s" % \
                          (current_file, total_files, _file)
                    path = _file
                    conflicts["files"].append(path)
                current_file += 1

        requirements = info["requires"]
        for module in requirements["modules"]:
            try:
                __import__(module)
            except ImportError:
                pip.main(["install", module])

        for new_package in requirements["packages"]:
            if not self.package_installed(new_package):
                self.install_package(new_package)

        with self.config:
            self.config["installed"][package] =\
                info["current_version"]["number"]

        return conflicts

    def update_package(self, package):
        """
        Update a package (in reality, reinstall it.)
        :param package: Package to reinstall
        :return:
        """
        if not self.package_installed(package):
            raise ValueError("Package '%s' is not installed"
                             % package)

        self.uninstall_package(package)
        self.install_package(package)

    def uninstall_package(self, package):
        """
        Uninstall a package.
        :param package: Package to uninstall
        :return:
        """
        if not self.package_installed(package):
            raise ValueError("Package '%s' is not installed"
                             % package)

        info = self.get_package_info(package)
        files = info["files"]
        files.reverse()

        for _file in files:
            if os.path.exists(_file):
                if os.path.isdir(_file):
                    shutil.rmtree(_file)
                else:
                    os.remove(_file)

        with self.config:
            del self.config["installed"][package]

    def __len__(self):
        return len(self.data)
