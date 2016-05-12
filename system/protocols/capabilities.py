# coding=utf-8
from enum import Enum, unique

__author__ = 'Sean'
__all__ = ["Capabilities"]


@unique
class Capabilities(Enum):

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
