__author__ = 'Gareth Coles'

from system.help.exceptions import UnknownTopicException


class Topic(object):
    name = ""
    root = ""
    type = None
    parent = None

    topics = {}

    def __init__(self, name, _type):
        self.name = name
        self.type = _type

        self.root = name

        if "/" in name:
            self.root = name.split("/", 1)[0]

    def add_topic(self, name, topic):
        if "/" in name:
            root, nodes = name.split("/", 1)
            _topic = self.get_topic(root)

            if _topic is not None:
                return _topic.add_topic(nodes, topic)
            raise UnknownTopicException("Unknown topic: %s" % name)
        else:
            _topic = self.get_topic(name)

            if _topic is None:
                topic.parent = self
                self.topics[name] = topic
                return True
            return False

    def get_topic(self, name=None):
        if name is None:
            return self

        root = name
        nodes = None

        if "/" in name:
            root, nodes = name.split("/", 1)

        if root in self.topics:
            return self.topics[root].get_topic(nodes)
        return None

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
                del _topic.parent
                del self.topics[name]
                return True
            raise UnknownTopicException("Unknown topic: %s" % name)

    def remove_all_topics(self):
        for topic in self.topics.keys():
            t = self.topics.get(topic)
            t.remove_all_topics()
            del t.parent
            del t
            del self.topics[topic]

    def __str__(self):
        raise NotImplementedError("Topics must be string-representable!")


class StringTopic(Topic):
    content = ""

    def __init__(self, name, _type, content):
        super(StringTopic, self).__init__(name, _type)

        self.content = content

    def __str__(self):
        return self.content
