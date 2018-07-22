# coding=utf-8

# Based on: https://github.com/Rapptz/discord.py/blob/async/discord/opus.py
# Discord.py is available under the MIT license, Copyright (c) 2015-2016 Rapptz

import array
import ctypes

from utils.opus.exceptions import OpusException

__author__ = 'Gareth Coles'


class EncoderStruct(ctypes.Structure):
    pass


OK = 0
APPLICATION_AUDIO = 2049
APPLICATION_VOIP = 2048
APPLICATION_LOWDELAY = 2051
CTL_SET_BITRATE = 4002
CTL_SET_BANDWIDTH = 4008


c_int_p = ctypes.POINTER(ctypes.c_int)
c_int16_p = ctypes.POINTER(ctypes.c_int16)
c_float_p = ctypes.POINTER(ctypes.c_float)
EncoderStruct_p = ctypes.POINTER(EncoderStruct)


FUNCTIONS = {
    "opus_strerror": ((ctypes.c_int, ), ctypes.c_char_p),

    # region: Encoder stuff
    "opus_encoder_create": (
        (ctypes.c_int, ctypes.c_int, ctypes.c_int, c_int_p),
        EncoderStruct_p
    ),
    "opus_encode": (
        (
            EncoderStruct_p, c_int16_p,
            ctypes.c_int, ctypes.c_char_p, ctypes.c_int32
        ),
        ctypes.c_int32
    ),
    "opus_encoder_ctl": (None, ctypes.c_int32),
    "opus_encoder_destroy": ((EncoderStruct_p, ), None),
    # endregion
}


class OpusLibrary(object):
    lib = None

    def __init__(self):
        self.load_library(ctypes.util.find_library('opus'))
        self.setup_functions()

    def load_library(self, name):
        self.lib = ctypes.cdll.LoadLibrary(name)

    def setup_functions(self):
        for key, value in FUNCTIONS.iteritems():
            try:
                func = getattr(self.lib, key)
            except Exception:
                raise

            try:
                if value[0] is not None:
                    func.argtypes = value[0]
                func.restype = value[1]
            except KeyError:
                pass

    def opus_strerror(self, code):
        return self.lib.opus_strerror(code)

    def opus_encoder_create(self, sampling_rate, channels, applications):
        return_value = ctypes.c_int()
        result = self.lib.opus_encoder_create(
            sampling_rate, channels, applications, ctypes.byref(return_value)
        )

        if return_value.value != 0:
            raise OpusException(return_value.value)

        return result

    def opus_encode(self, encoder, pcm, frame_size, data, max_data_bytes):
        result = self.lib.opus_encode(
            encoder, pcm, frame_size, data, max_data_bytes
        )

        if result < 0:
            raise OpusException(result)

        return array.array('b', data[:result]).tobytes()

    def opus_encoder_ctl(self, encoder, *args):
        result = self.lib.opus_encoder_ctl(encoder, *args)

        if result < 0:
            raise OpusException(result)

        return result

    def opus_encoder_destroy(self, encoder):
        return self.lib.opus_encoder_destroy(encoder)


opus = OpusLibrary()
