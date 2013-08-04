# coding=utf-8
import yaml, sys, os

from system.constants import *

class yaml_loader(object):
    def __init__(self, plugin=False, pluginName=None):
        self.plugin = plugin
        if self.plugin:
            if not pluginName:
                raise Exception("Tried to create a YAML loader for a plugin without specifying the plugin name")
        self.pluginName = pluginName
        self.data = {}

    def load(self, filename, default=None):
        if not default: default = {}
        if self.plugin:
            if not os.path.exists("plugins/data/%s" % self.pluginName):
                os.mkdir("plugins/data/%s" % self.pluginName)
            if not os.path.exists("plugins/data/%s/%s.yml" % (self.pluginName, filename)):
                open("plugins/data/%s/%s.yml" % (self.pluginName, filename), "w").close()
                self.data = default
                self.save(filename)
            else:
                self.data = yaml.load(file("plugins/data/%s/%s.yml" % (self.pluginName, filename), "r"))
        else:
            if not os.path.exists(filename):
                open(filename, "w").close()
                self.data = default
                self.save(filename)
            else:
                self.data = yaml.load(file(filename, "r"))
        return self.data

    def save(self, filename):
        done = [False, ""]
        try:
            if self.plugin:
                fh = open("plugins/data/%s/%s.yml" % (self.pluginName, filename), "w")
                fh.write(yaml.dump(self.data))
                fh.flush()
                fh.close()
            else:
                fh = open(filename, "w")
                fh.write(yaml.dump(self.data))
                fh.flush()
                fh.close()
        except:
            done = [False, sys.exc_info()[0]]
        else:
            done = [True, ""]
        return done

    def save_data(self, filename, data):
        if isinstance(data, dict):
            self.data = data
        else:
            raise TypeError("Data must be a dictionary!")
        self.save(filename)

    def __getitem__(self, item):
        return self.data[item]

    def __setitem__(self, key, value):
        self.data[key] = value

    def __delitem__(self, key):
        del self.data[key]

    def __contains__(self, item):
        return item in self.data

    def __iter__(self):
        return self.data.__iter__()

    def __len__(self):
        return self.data.__len__()

    def iterkeys(self):
        return self.data.iterkeys()

    def keys(self):
        return self.data.keys()

    def items(self):
        return self.data.items()

    def isTrue(self):
        return bool(self.data)

