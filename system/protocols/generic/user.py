__author__ = 'Sean'

from system.translations import Translations
_ = Translations().get()


class User(object):

    authorized = False
    auth_name = ""

    def __init__(self, nickname, protocol=None, is_tracked=False):
        self.nickname = nickname
        self.protocol = protocol
        self.is_tracked = is_tracked

    @property
    def name(self):
        return self.nickname

    def respond(self, message):
        raise NotImplementedError(_("This method must be overridden"))

    # region permissions
    # Note: Not in a separate class, as in most cases it'd just end up as a
    # tightly coupled mess, and there aren't a whole lot of things you can
    # actually make generic between protocols anyway.

    def can_kick(self, user, channel):
        """
        Whether or not this User can kick user from channel. If unsure, this
        should return False. The calling code can always attempt a kick anyway
        if they so wish.
        Note: In some cases, user and/or channel may have no effect on
        """
        return False

    def can_ban(self, user, channel):
        """
        Whether or not this User can ban user from channel. If unsure, this
        should return False. The calling code can always attempt a kick anyway
        if they so wish.
        """
        return False

    # endregion
    pass  # Because otherwise the region doesn't end
