# coding=utf-8

"""
Help manager. Long overdue!

This is supposed to be used for the management of help topics, which will
be accessible from all other parts of the bot.
"""

__author__ = 'Gareth Coles'

from weakref import WeakValueDictionary

from system.enums import HelpTopicType
from system.help.exceptions import UnknownTopicException, UnknownTypeException
from system.help.topics.default import AliasListTopic, ComandListTopic
from system.singleton import Singleton

from system.logging.logger import getLogger


class HelpManager(object):
    """
    Help topics manager singleton.
    """

    __metaclass__ = Singleton

    topics = {}
    commands = WeakValueDictionary()

    def __init__(self):
        self.logger = getLogger("Help")
        self.add_topic(
            AliasListTopic("aliases", HelpTopicType.GenericTopic)
        )
        self.add_topic(
            ComandListTopic("commands", HelpTopicType.GenericTopic)
        )

    def add_topic(self, topic):
        name = topic.name
        _type = topic.type

        if self.get_topic(name):
            return False

        if _type is HelpTopicType.CommandTopic:
            return self._add_topic_command(topic)
        elif _type is HelpTopicType.GenericTopic:
            return self._add_topic_generic(topic)
        else:
            raise UnknownTypeException("Unknown help topic type: %s" % _type)

    def _add_topic_command(self, topic):
        r = self._add_topic_generic(topic)

        if r:
            self.commands[topic.command] = topic

        return r

    def _add_topic_generic(self, topic):
        try:
            self._add_topic(topic)
        except UnknownTopicException:
            return False
        return True

    def _add_topic(self, topic):
        name = topic.name

        if "/" in name:
            root, nodes = name.split("/", 1)

            _topic = self.get_topic(root)

            if _topic is not None:
                return _topic.add_topic(nodes, topic)
            raise UnknownTopicException("Unknown topic: %s" % name)
        else:
            _topic = self.get_topic(name)

            if _topic:
                return False

            self.topics[name] = topic
            return True

    def remove_topic(self, name):
        if "/" in name:
            root, nodes = name.split("/", 1)

            _topic = self.get_topic(root)

            if _topic is not None:
                return _topic.remove_topic(nodes)
            raise UnknownTopicException("Unknown topic: %s" % name)
        else:
            _topic = self.get_topic(name)

            if _topic is not None:
                if _topic.parent:
                    del _topic.parent

                del self.topics[name]

                if _topic.type == HelpTopicType.CommandTopic:
                    if _topic.root in self.commands:
                        del self.commands[_topic]

                return True
            raise UnknownTopicException("Unknown topic: %s" % name)

    def get_topic(self, name):
        """
        :type name: str
        :param name:
        :return:
        """

        if name in self.commands:
            return self.commands.get(name)

        if "/" in name:
            root, nodes = name.split("/", 1)

            if root in self.topics:
                return self.topics.get(root).get_topic(nodes)
        elif name in self.topics:
            return self.topics.get(name)
        return None

    def topic_names(self):
        return self.topics.keys()

    def command_topics(self):
        return self.commands.keys()
