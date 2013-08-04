# coding=utf-8
import urllib, urllib2

from system.yaml_loader import *

from twisted.internet import reactor
from xml.etree import ElementTree

from system.decorators import *

class plugin(object):
    """
    ICECast integration plugin
    """

    name = "ICECast integration"

    commands = {

    }

    hooks = {
        "connectionLost": "save",
        "signedOn": "load",
        }

    def __init__(self, irc):
        self.irc = irc
        self.has_config = False
        self.settings_handler = yaml_loader(True, "icecast")
        self.settings = self.settings_handler.load("settings")
        self.help = {

            }

        self.data = {}

    def finishedLoading(self):
        if not self.settings:
            self.irc.prnt("|! Please edit plugins/data/icecast/settings.yml and fill in the details!")
            self.irc.unloadPlugin("icecast")
        elif self.settings["xml_url"] == '':
            self.irc.prnt("|! Please edit plugins/data/icecast/settings.yml and fill in the details!")
            self.irc.unloadPlugin("icecast")
        else:
            self.has_config = True
            self.url = self.settings["xml_url"]
            self.user = self.settings["admin_user"]
            self.password = self.settings["admin_password"]

            self.nowPlaying = self.settings["now_playing"]
            self.npMessage = self.settings["npmessage"]

            self.statusMessages = self.settings["status_messages"]

            self.periodicMessages = self.settings["periodic_messages"]
            self.periodicInterval = self.settings["periodic_interval"]
            self.periodicString = self.settings["periodic_string"]

            self.messageChannels = self.settings["channels"]

    def load(self, data=None):
        self.settings = self.settings_handler.load("settings")

        if not self.settings:
            self.settings = {

            }

    def save(self, data=None):
        if self.has_config:
            self.settings_handler.save_data("settings", self.settings)

    def inventory(self, user, channel, arguments):
        pass

    def getData(self, url, user, password):
        return_data = {}
        try:
            request = urllib2.Request(url)
            base64string = base64.encodestring('%s:%s' % (user, password)).replace('\n', '')
            request.add_header("Authorization", "Basic %s" % base64string)
            data = urllib2.urlopen(request).read()
            xml = ElementTree.XML(data)
        except:
            self.sendmsg("#arford", "There appears to be nobody streaming right now.")
        else:
            streams = xml.findall("source")
            mounts = []

            serverwide_tags = ["admin", "client_connections", "clients", "connections", "file_connections", "host",
                               "listener_connections", "listeners", "location", "server_id", "server_start",
                               "source_client_connections", "source_relay_connections", "source_total_connections",
                               "sources", "stats", "stats_connections"]
            serverwide_data = {}

            for element in serverwide_tags:
                node = xml.find(element)
                if node:
                    serverwide_data[element] = node.text
                else:
                    serverwide_data[element] = ""

            stream_tags = ["artist", "audio_bitrate", "audio_channels", "audio_info", "audio_samplerate", "bitrate",
                           "genre", "ice-bitrate", "ice-channels", "ice-samplerate", "listener_peak", "listeners",
                           "listenurl", "max_listeners", "public", "server_description", "server_name",
                           "server_type", "server_url", "slow_listeners", "source_ip", "source_ip", "stream_start",
                           "subtype", "title", "total_bytes_read", "total_bytes_sent"]

            stream_data = {}

            for element in streams:
                mount = element.attrib["mount"]
                source_data = {}

                for tag in stream_tags:
                    node = element.find(element)
                    if node:
                        source_data[element] = node.text
                    else:
                        source_data[element] = ""

                source_data["mount"] = mount
                stream_data[mount] = source_data

            return_data["server"] = serverwide_data
            return_data["mounts"] = stream_data

        return return_data
