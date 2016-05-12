# coding=utf-8
__author__ = 'Sean'

(
    #: Messages can contain linebreaks
    MULTILINE_MESSAGE,
    #: Protocol uses channels
    #: (rather than a single "channel" for the whole protocol)
    MULTIPLE_CHANNELS,
    #: The protocol can be in more than one channel at a time
    MULTIPLE_CHANNELS_JOINED,
    #: Voice communication support
    VOICE,
    #: Able to send messages to channels the protocol isn't in
    MESSAGE_UNJOINED_CHANNELS,
    #: Voice and text channels are separate;
    #: can't send text to voice and vice versa
    INDEPENDENT_VOICE_CHANNELS,
) = xrange(6)
