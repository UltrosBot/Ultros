# coding=utf-8
from enum import Enum, unique

__author__ = 'Sean'
__all__ = ["Capabilities"]


@unique
class Capabilities(Enum):
    """
    An enum containing constants to declare what a protocol is capable of

    You can use *protocol.get_capabilities()* or *protocol.has_capability(cap)*
    to get all of a protocol's capabilities or check whether it has a specific
    one respectively.

    The current capabilities we have are as follows:

    MULTILINE_MESSAGE           Messages can contain line-breaks
    MULTIPLE_CHANNELS           Protocol supports the concept of separate
                                channels
    MULTIPLE_CHANNELS_JOINED    Protocol may be in more than one channel at
                                once
    VOICE                       Protocol supports voice/audio communication
    MESSAGE_UNJOINED_CHANNELS   Protocol is able to send messages to
                                channels that it hasn't joined
    INDEPENDENT_VOICE_CHANNELS  Voice and text channels are separate; can't
                                send text to a voice channel and vice-versa
    """

    #: Messages can contain linebreaks
    MULTILINE_MESSAGE = 0

    #: Protocol uses channels
    #: (rather than a single "channel" for the whole protocol)
    MULTIPLE_CHANNELS = 1

    #: The protocol can be in more than one channel at a time
    MULTIPLE_CHANNELS_JOINED = 2

    #: Voice communication support
    VOICE = 3

    #: Able to send messages to channels the protocol isn't in
    MESSAGE_UNJOINED_CHANNELS = 4

    #: Voice and text channels are separate;
    #: can't send text to voice and vice versa
    INDEPENDENT_VOICE_CHANNELS = 5
