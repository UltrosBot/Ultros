"""General events that are not specific to any protocols."""

__author__ = 'Gareth Coles'

from system.events.base import BaseEvent


class GeneralEvent(BaseEvent):
    """A general event, not tied to a protocol.

    If an event subclasses this, chances are it's a protocol-agnostic event.
    This can be thrown from anywhere - even from a protocol. You should avoid
    throwing it from your plugins, though - use a PluginEvent for that (see
    base.py)
    """

    def __init__(self, caller):
        super(GeneralEvent, self).__init__(caller)


class PluginsLoadedEvent(GeneralEvent):
    """This event is fired when all of the plugins have been loaded.

    The caller will be the factory manager instead of a protocol.
    This also includes a dictionary of all loaded plugins.
    """

    loaded_plugins = {}

    def __init__(self, caller, plugins):
        """Initialise the event object."""

        self.loaded_plugins = plugins

        super(PluginsLoadedEvent, self).__init__(caller)


class ReactorStartedEvent(GeneralEvent):
    """This event is fired just after the reactor is started.

    The caller will be the factory manager instead of a protocol.
    """

    def __init__(self, caller):
        """Initialise the event object."""

        super(ReactorStartedEvent, self).__init__(caller)


class PreConnectEvent(GeneralEvent):
    """Thrown just before we connect. Includes the configuration of the
    protocol that threw the event.
    """

    config = None

    def __init__(self, caller, config):
        """Initialise the event object."""

        self.config = config

        super(PreConnectEvent, self).__init__(caller)


class PostConnectEvent(GeneralEvent):
    """Thrown just after we connect, before we do any logging in or such.

    Includes the configuration of the protocol that threw the event.
    """

    config = None

    def __init__(self, caller, config):
        """Initialise the event object."""

        self.config = config

        super(PostConnectEvent, self).__init__(caller)


class PreSetupEvent(GeneralEvent):
    """Thrown just before we do our setup, post-connect.

    Includes the configuration of the protocol that threw the event.
    """

    config = None

    def __init__(self, caller, config):
        """Initialise the event object."""

        self.config = config

        super(PreSetupEvent, self).__init__(caller)


class PostSetupEvent(GeneralEvent):
    """Thrown after before we do our setup.

    Includes the configuration of the protocol that threw the event.
    """

    config = None

    def __init__(self, caller, config):
        """Initialise the event object."""

        self.config = config

        super(PostSetupEvent, self).__init__(caller)


class PreMessageReceived(GeneralEvent):
    """Thrown when we receive a message, before we parse or otherwise do
    anything with it.

    The following attributes are available.

    * caller: The protocol that received the message
    * source: The User object of the person that send the message
    * target: The User or Channel object of the message target.
        This can also be None or a string. Do type-checking!
    * message: A string, containing the raw, un-parsed and un-sanitized
        message. You can modify this if you need, but note that every other
        plugin listening for this event will see the modified message.
    * type: The message type. This is a string, and may differ
        between protocols.
    * printable: A boolean that specifies whether the message should be
        output in the logs. You can modify this; could be useful for things
        like password inputs. Defaults to True.
    """

    source = None
    target = None
    message = ""
    type = ""
    printable = True

    def __init__(self, caller, source, target, message, typ, printable=True):
        """Initialise the event object."""

        self.source = source
        self.target = target
        self.message = message
        self.type = typ
        self.printable = printable

        super(PreMessageReceived, self).__init__(caller)

    def __str__(self):
        return "<%s at %s | type: %s | target: %s | source: %s | " \
               "printable: %s | message: %s>" % (self.__class__.__name__,
                                                 hex(id(self)), self.type,
                                                 str(self.target),
                                                 str(self.source),
                                                 self.printable,
                                                 repr(self.message))


class MessageReceived(GeneralEvent):
    """Thrown when we get a message.

    This is a "clean", parsed message, and you can presume that it's already
    been printed to the log. See the `PreMessageReceived` event for param info.
    """

    source = None
    target = None
    message = ""
    type = ""

    def __init__(self, caller, source, target, message, typ):
        """Initialise the event object."""

        self.source = source
        self.target = target
        self.message = message
        self.type = typ

        super(MessageReceived, self).__init__(caller)

    def __str__(self):
        return "<%s at %s | type: %s | target: %s | source: %s | " \
               "message: %s>" % (self.__class__.__name__, hex(id(self)),
                                 self.type, str(self.target),
                                 str(self.source), repr(self.message))


class MessageSent(GeneralEvent):
    """Thrown when we send a message - plugins are free to catch this and even
    modify the message before it actually gets sent out.

    The params available are as follows..

    * caller: As usual, the protocol that threw the event
    * type: String describing what type of message this is
    * target: Where the message is going; a string
    * message: The actual message
    * printable: A boolean specifying whether we should print the message
        or not
    """

    type = ""
    target = ""
    message = ""
    printable = ""

    def __init__(self, caller, typ, target, message, printable=True):
        """Initialise the event object."""

        self.type = typ
        self.target = target
        self.message = message
        self.printable = printable

        super(MessageSent, self).__init__(caller)

    def __str__(self):
        return "<%s at %s | type: %s | target: %s | message: %s | " \
               "printable: %s>" % (self.__class__.__name__, hex(id(self)),
                                   self.type, str(self.target),
                                   repr(self.message), self.printable)


class NameChangedSelf(GeneralEvent):
    """Thrown whenever our name is changed."""

    name = ""

    def __init__(self, caller, name):
        """Initialise the event object."""

        self.name = name

        super(NameChangedSelf, self).__init__(caller)


class NameChanged(GeneralEvent):
    """Thrown whenever someone else's name is changed."""

    old_name = ""
    user = None

    def __init__(self, caller, user, old_name):
        """Initialise the event object."""

        self.old_name = old_name
        self.user = user

        super(NameChanged, self).__init__(caller)


class UserDisconnected(GeneralEvent):
    """Thrown when a user disconnects."""

    user = None

    def __init__(self, caller, user):
        """Initialise the event object."""

        self.user = user

        super(UserDisconnected, self).__init__(caller)


class PreCommand(GeneralEvent):
    """Thrown just before a command is called.

    Don't action your commands here, this is more for stats collection
    and output modification, as well as perhaps a little duck-punching.
    """

    command = ""
    args = []
    source = None
    target = None
    printable = ""
    message = ""

    def __init__(self, caller, command, args, source, target, printable,
                 message):
        """Initialise the event object."""

        self.command = command
        self.args = args
        self.source = source
        self.target = target
        self.printable = printable
        self.message = message

        super(PreCommand, self).__init__(caller)

    def __str__(self):
        return "<%s at %s | command: %s | args: %s | source: %s | target: " \
               "%s | printable: %s>" % (self.__class__.__name__, hex(id(self)),
                                        self.command, self.args, self.source,
                                        self.target, self.printable)


class UnknownCommand(GeneralEvent):
    """Thrown when someone tries to run a command that doesn't exist.

    The uses of this are debatable, but we'll leave that up to you,
    the developers, to decide upon.
    """

    protocol = None
    command = ""
    args = ""
    source = None
    target = None

    def __init__(self, caller, protocol, command, args, source, target):
        """Initialise the event object."""

        self.protocol = protocol
        self.command = command
        self.args = args
        self.source = source
        self.target = target

        super(UnknownCommand, self).__init__(caller)

    def __str__(self):
        return "<%s at %s | protocol: %s | command: %s | args: %s | source: " \
               "%s | target: %s>" % (self.__class__.__name__, hex(id(self)),
                                     self.protocol, self.command, self.args,
                                     self.source, self.target)


class ActionSent(GeneralEvent):
    """Thrown when we send a action - plugins are free to catch this and even
    modify the action before it actually gets sent out.

    The params available are as follows..

    * caller: As usual, the protocol that threw the event
    * type: String describing what type of message this is
    * target: Where the message is going; a string
    * message: The actual action
    * printable: A boolean specifying whether we should print the message
        or not?
    """

    target = ""
    message = ""
    printable = ""

    def __init__(self, caller, target, message, printable=True):
        """Initialise the event object."""

        self.target = target
        self.message = message
        self.printable = printable

        super(ActionSent, self).__init__(caller)

    def __str__(self):
        return "<%s at %s | target: %s | message: %s | " \
               "printable: %s>" % (self.__class__.__name__, hex(id(self)),
                                   str(self.target),
                                   repr(self.message), self.printable)
