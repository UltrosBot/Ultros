"""
Classes for working with the Ultros-contrib repository

These can be used within a plugin, but they're mostly used by the package
management script.
"""

__author__ = 'Gareth Coles'

import os
import urllib
import urllib2
import yaml


class Packages(object):

    """
    Class responsible for loading up plugin info, retrieving files
    and generally handling GitHub and the filesystem.
    """

    data = {}
    packages = []

    base_file_url = "https://raw.github.com/McBlockitHelpbot/Ultros-contrib/" \
                    "master/"

    info_file = "packages.yml"
    package_info_file = "package.yml"
    package_versions_file = "versions.yml"

    def __init__(self):
        info_url = self.base_file_url + self.info_file
        response = urllib2.urlopen(info_url)
        data = response.read()

        self.data = yaml.load(data)
        self.packages = sorted(self.data.keys())

    def _get_file(self, base_path, path):
        if os.path.exists(path):
            raise ValueError("A file at `%s` already exists" % path)

        constructed_path = self.base_file_url + base_path + path
        urllib.urlretrieve(constructed_path, path)

    def get_package_info(self, package):
        if package in self.packages:
            url = self.base_file_url + package + "/" \
                                     + self.package_info_file

            response = urllib2.urlopen(url)
            data = response.read()

            return yaml.load(data)
        return None

    def get_package_versions(self, package):
        if package in self.packages:
            url = self.base_file_url + package + "/" \
                                     + self.package_versions_file

            response = urllib2.urlopen(url)
            data = response.read()

            return yaml.load(data)
        return None

    def __len__(self):
        return len(self.data)
