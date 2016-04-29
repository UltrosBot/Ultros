# coding=utf-8
import ctypes

from utils.opus.lib import opus, APPLICATION_AUDIO, CTL_SET_BITRATE, \
    CTL_SET_BANDWIDTH, c_int16_p

__author__ = 'Gareth Coles'


band_ctl = {
    'narrow': 1101,
    'medium': 1102,
    'wide': 1103,
    'superwide': 1104,
    'full': 1105,
}


class Encoder(object):
    encoder = None

    def __init__(self, sampling, channels, application=APPLICATION_AUDIO):
        self.sampling_rate = sampling
        self.channels = channels
        self.application = application

        self.frame_length = 20
        self.sample_size = 2 * self.channels
        self.samples_per_frame = int(
            self.sampling_rate / 100 * self.frame_length
        )

        self.encoder = self._get_encoder()
        self.set_bitrate(128)
        self.set_bandwidth("full")

    def __del__(self):
        if self.encoder is not None:
            opus.opus_encoder_destroy(self.encoder)
            self.encoder = None

    def _get_encoder(self):
        return opus.opus_encoder_create(
            self.sampling_rate, self.channels, self.application
        )

    def set_bitrate(self, kbps):
        kbps = min(128, max(16, int(kbps)))

        opus.opus_encoder_ctl(
            self.encoder, CTL_SET_BITRATE, kbps*1024
        )

        return kbps

    def set_bandwidth(self, band):
        if band not in band_ctl:
            raise KeyError("{} must be one of: {}".format(
                band, ", ".join(band_ctl.keys())
            ))

        k = band_ctl[band]
        opus.opus_encoder_ctl(self.encoder, CTL_SET_BANDWIDTH, k)

    def encode(self, pcm, frame_size):
        max_data_bytes = len(pcm)
        pcm = ctypes.cast(pcm, c_int16_p)
        data = (ctypes.c_char * max_data_bytes)()

        return opus.opus_encode(
            self.encoder, pcm, frame_size, data, max_data_bytes
        )
