__author__ = 'Gareth Coles'


class BaseEvent(object):

    """
    This is a basic event object. All other events should inherit this class.
    When you're re-implementing this, be sure to call your supers! That also
    goes for any subclasses of subclasses. Keep it clean and correct, people!

    For completeness, every event /must/ be a subclass of this class. This is
    a necessary, but very simple and easy limitation. If you don't like it,
    well.. Are you really a programmer?
    """

    caller = None

    def __init__(self, caller):
        """
        For filtering reasons, every event /must/ be supplied with the caller.
        If this isn't here, it'll be very difficult to work with the event
        in your plugins.

        @param caller: Who threw the event to the manager.
        @type caller: Simply an Object. Can be checked against Protocol or
            the other classes we use, such as the FactoryManager.
        """

        self.caller = caller


class PluginEvent(BaseEvent):

    """
    This is an event specifically thrown from a plugin. It'll only be thrown
    by a plugin, and plugins should only throw subclasses of this event.
    """

    def __init__(self, caller):
        super(PluginEvent, self).__init__(caller)
