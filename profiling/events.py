__author__ = 'Gareth Coles'

import os
import sys
print os.getcwd()

sys.path.append(os.getcwd())  # Because herp derp

import cProfile

from profiling.fakes import FakePlugin, FakePluginEvent

from system.events.manager import EventManager

events = EventManager()


class EventPlugin(FakePlugin):
    def __init__(self, info):
        super(EventPlugin, self).__init__(info)

        events.add_callback("Test", self, self.event_callback, 0)

    def event_callback(self, event):
        pass


def do_profile():
    plugin = EventPlugin({"name": "FAAAAAAAAKE!"})
    cProfile.run("run()")


def run():
    for i in xrange(0, 1000):
        e = FakePluginEvent()
        events.run_callback("Test", e)


if __name__ == "__main__":
    do_profile()
