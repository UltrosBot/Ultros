__author__ = 'Gareth Coles'

from system.command_manager import CommandManager
from system.help.topics.generic import Topic


class ComandListTopic(Topic):
    def __init__(self, name, _type):
        super(ComandListTopic, self).__init__(name, _type)

    def __str__(self):
        manager = CommandManager()

        if manager.commands:
            return "Commands: %s" % ", ".join(manager.commands.keys())
        return "Commands: None"


class AliasListTopic(Topic):
    def __init__(self, name, _type):
        super(AliasListTopic, self).__init__(name, _type)

    def __str__(self):
        manager = CommandManager()

        if manager.aliases:
            return "Aliases: %s" % ", ".join(
                ["%s: %s" % (x[0], x[1]) for x in manager.aliases.items()]
            )
        return "Aliases: None"
