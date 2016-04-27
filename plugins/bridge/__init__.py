# coding=utf-8

"""
Configurable message-bridging plugin.

This plugin is used to relay messages between any number of endpoints - that
is to say, between any channels or users on any connected protocol.

The API use of this plugin is.. debatable, but we've still decided to document
it.
"""

from system.events.general import MessageReceived, MessageSent, PreCommand, \
    UserDisconnected, ActionSent, ActionReceived
from system.events.irc import UserJoinedEvent, UserKickedEvent, \
    UserPartedEvent, UserQuitEvent, CTCPQueryEvent
from system.events.mumble import UserJoined, UserMoved, UserRemove

from system.plugins.plugin import PluginObject
from system.protocols.generic.channel import Channel
from system.protocols.generic.user import User
from system.storage.formats import YAML
from system.translations import Translations


__author__ = 'Gareth Coles'
__all__ = ["BridgePlugin"]

_ = Translations().get()
__ = Translations().get_m()


class BridgePlugin(PluginObject):
    """
    Message bridging plugin object
    """

    config = None

    rules = {}

    @property
    def rules(self):
        """
        The list of bridging rules
        """

        return self.config["rules"]

    def setup(self):
        """
        Called when the plugin is loaded. Performs initial setup.
        """

        self.logger.trace(_("Entered setup method."))

        try:
            self.config = self.storage.get_file(self, "config", YAML,
                                                "plugins/bridge.yml")
        except Exception:
            self.logger.exception(_("Error loading configuration!"))
            self.logger.error(_("Disabling.."))
            self._disable_self()
            return
        if not self.config.exists:
            self.logger.error(_("Unable to find config/plugins/bridge.yml"))
            self.logger.error(_("Disabling.."))
            self._disable_self()
            return

        # General

        self.events.add_callback("PreMessageReceived", self, self.handle_msg,
                                 1000)

        self.events.add_callback("MessageSent", self, self.handle_msg_sent,
                                 0)

        # self.events.add_callback("PreCommand", self, self.handle_command,
        #                          1000)

        self.events.add_callback("ActionSent", self, self.handle_action_sent,
                                 0)

        self.events.add_callback("ActionReceived", self,
                                 self.handle_action_received, 0
                                 )

        self.events.add_callback("UserDisconnected", self,
                                 self.handle_disconnect, 1000)

        # IRC

        self.events.add_callback("IRC/UserJoined", self,
                                 self.handle_irc_join, 1000)

        self.events.add_callback("IRC/UserParted", self,
                                 self.handle_irc_part, 1000)

        self.events.add_callback("IRC/UserKicked", self,
                                 self.handle_irc_kick, 1000)

        self.events.add_callback("IRC/UserQuit", self,
                                 self.handle_irc_quit, 1000)

        # Mumble

        self.events.add_callback("Mumble/UserRemove", self,
                                 self.handle_mumble_remove, 1000)

        self.events.add_callback("Mumble/UserJoined", self,
                                 self.handle_mumble_join, 1000)

        self.events.add_callback("Mumble/UserMoved", self,
                                 self.handle_mumble_move, 1000)

    def handle_irc_join(self, event=UserJoinedEvent):
        """
        Event handler for IRC join events
        """

        self.do_rules("", event.caller, event.user, event.channel,
                      f_str=["general", "join"],
                      tokens={"CHANNEL": event.channel.name})

    def handle_irc_part(self, event=UserPartedEvent):
        """
        Event handler for IRC part events
        """

        self.do_rules("", event.caller, event.user, event.channel,
                      f_str=["general", "part"],
                      tokens={"CHANNEL": event.channel.name})

    def handle_irc_kick(self, event=UserKickedEvent):
        """
        Event handler for IRC kick events
        """

        self.do_rules(event.reason, event.caller, event.user, event.channel,
                      f_str=["general", "kick"],
                      tokens={"CHANNEL": event.channel.name,
                              "KICKER": event.kicker.nickname})

    def handle_irc_quit(self, event=UserQuitEvent):
        """
        Event handler for IRC quit events
        """

        self.do_rules(event.message, event.caller, event.user, event.user,
                      f_str=["irc", "disconnect"],
                      tokens={"USER": event.user.nickname})

    def handle_disconnect(self, event=UserDisconnected):
        """
        Event handler for general disconnect events
        """

        self.do_rules("", event.caller, event.user, event.user,
                      f_str=["general", "disconnect"],
                      tokens={"USER": event.user.nickname})

    def handle_mumble_join(self, event=UserJoined):
        """
        Event handler for Mumble join events
        """

        self.do_rules("", event.caller, event.user, event.user,
                      f_str=["mumble", "connect"])

    def handle_mumble_move(self, event=UserMoved):
        """
        Event handler for Mumble move events
        """

        # Moving /from/ the configured channel to another one
        self.do_rules("", event.caller, event.user, event.old_channel,
                      f_str=["mumble", "moved-from"],
                      tokens={"CHANNEL": event.channel.name})
        # Moving /to/ the configured channel
        self.do_rules("", event.caller, event.user, event.channel,
                      f_str=["mumble", "moved-to"],
                      tokens={"CHANNEL": event.channel.name})

    def handle_mumble_remove(self, event=UserRemove):
        """
        Event handler for Mumble remove events
        """

        self.do_rules(event.reason, event.caller, event.user, event.user,
                      f_str=["mumble", "remove"],
                      tokens={"KICKER": event.kicker,
                              "BANNED?": "banned" if event.ban else "kicked"})

    def handle_msg(self, event=MessageReceived):
        """
        Event handler for general message events
        """

        self.do_rules(event.message, event.caller, event.source, event.target)

    def handle_msg_sent(self, event=MessageSent):
        """
        Event handler for general message sent events
        """

        self.do_rules(event.message, event.caller, event.caller.ourselves,
                      event.target)

    def handle_action_received(self, event=ActionReceived):
        self.do_rules(event.message, event.caller, event.source, event.target,
                      f_str=["general", "action"])

    def handle_action_sent(self, event=ActionSent):
        """
        Event handler for general action sent events
        """

        self.do_rules(event.message, event.caller, event.caller.ourselves,
                      event.target, f_str=["general", "action"])

    def handle_command(self, event=PreCommand):
        """
        Event handler for general pre-command events
        """

        if event.printable:
            self.do_rules(event.message, event.caller, event.source,
                          event.target)

    def do_rules(self, msg, caller, source, target, from_user=True,
                 to_user=True, f_str=None, tokens=None, use_event=False):
        """
        Action the bridge ruleset based on input.

        :param msg: Message to relay
        :param caller: User that sent the message
        :param source: Protocol the message relates to
        :param target: User or Channel the message was sent to
        :param from_user: Whether to relay from a PM
        :param to_user: Whether to relay to a PM
        :param f_str: Definition of the formatting string to use. For example,
            ["general", "action"] or ["irc", "quit"]
        :param tokens: Dict of extra tokens to replace
        :param use_event: Whether to throw a MessageSent event

        :type msg: str
        :type caller: User
        :type source: Protocol
        :type target: User, Channel
        :type from_user: bool
        :type to_user: bool
        :type f_str: list
        :type tokens: dict
        :type use_event: bool
        """

        if not caller:
            return
        if not source:
            return
        if not target:
            return
        if not tokens:
            tokens = {}
        if not f_str:
            f_str = ["general", "message"]

        c_name = caller.name.lower()  # Protocol
        s_name = source.nickname  # User
        if isinstance(target, Channel):
            t_name = target.name  # Channel
        else:
            t_name = target.nickname

        for rule, data in self.rules.items():
            self.logger.debug(_("Checking rule: %s - %s") % (rule, data))
            from_ = data["from"]
            to_ = data["to"]

            if c_name != from_["protocol"].lower():
                self.logger.trace(_("Protocol doesn't match."))
                continue

            if not self.factory_manager.get_protocol(to_["protocol"]):
                self.logger.trace(_("Target protocol doesn't exist."))
                continue

            if isinstance(target, User):
                # We ignore the source name since there can only ever be one
                #     user: us.
                if not from_user:
                    self.logger.trace(_("Function was called with relaying "
                                        "from users disabled."))
                    continue
                if from_["source-type"].lower() != "user":
                    self.logger.trace(_("Target type isn't a user."))
                    continue
            elif isinstance(target, Channel):
                if from_["source-type"].lower() != "channel":
                    self.logger.trace(_("Target type isn't a Channel."))
                    continue
                if from_["source"].lower() != "*" \
                   and from_["source"].lower() != t_name.lower():
                    self.logger.trace(_("Target name doesn't match the "
                                        "source."))
                    continue
            else:
                self.logger.trace(_("Target isn't a known type."))
                continue

            if to_["target"] == "user" and not to_user:
                self.logger.trace(_("Function was called with relaying to "
                                    "users disabled."))
                continue

            # If we get this far, we've matched the incoming rule.

            format_string = None

            formatting = data["formatting"]
            if f_str[0] in formatting:
                if f_str[1] in formatting[f_str[0]]:
                    format_string = formatting[f_str[0]][f_str[1]]

            if not format_string:
                self.logger.trace(_("Not relaying message as the format "
                                    "string was empty or missing."))
                continue

            else:
                sf_name = s_name
                tf_name = t_name
                if from_.get("obfuscate-names", False):
                    sf_name = s_name[:-1] + "_" + s_name[-1]
                    if "USER" in tokens:
                        _u = tokens["USER"]
                        tokens["USER"] = _u[:-1] + "_" + _u[-1]

                if to_.get("obfuscate-names", False):
                    tf_name = t_name[:-1] + "_" + t_name[-1]
                    if "TARGET" in tokens:
                        _u = tokens["TARGET"]
                        tokens["TARGET"] = _u[:-1] + "_" + _u[-1]

                if "disconnected" in format_string:
                    pass

                for line in msg.strip("\r").split("\n"):
                    format_string = formatting[f_str[0]][f_str[1]]

                    for k, v in tokens.items():
                        format_string = format_string.replace("{%s}" % k, v)

                    format_string = format_string.replace("{MESSAGE}", line)
                    format_string = format_string.replace("{USER}", sf_name)
                    format_string = format_string.replace("{TARGET}", tf_name)
                    format_string = format_string.replace("{PROTOCOL}",
                                                          caller.name)

                    prot = self.factory_manager.get_protocol(to_["protocol"])
                    prot.send_msg(to_["target"], format_string,
                                  target_type=to_["target-type"],
                                  use_event=use_event)
