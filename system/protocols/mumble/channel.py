__author__ = 'Sean'


class Channel(object):
    def __init__(self, channel_id, name, parent, position, links):
        self.channel_id = channel_id
        self.name = name
        self.parent = parent
        self.position = position
        self.links = links

    def add_link(self, channel_id):
        if channel_id not in self.links:
            self.links.append(channel_id)

    def remove_link(self, channel_id):
        if channel_id in self.links:
            self.links.remove(channel_id)
