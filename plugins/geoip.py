import socket
import urllib
from xml.dom import minidom

from system.decorators import *

class plugin(object):
    """
    GeoIP plugin -
    """

    commands = {
        "geoip"      : "geo_ip_lookup"
    }

    hooks = {
        }

    name = "GeoIP"

    def __init__(self, irc):
        self.irc = irc

        self.help = {
            "geoip": "Attempt to look up the location of an address or user.\n"
                     "Usage: %sgeoip <address|nick>" % self.irc.control_char
            }

    #@config("rank", "authorized")
    def geo_ip_lookup(self, user, channel, arguments):
        if arguments[1:]:
            GEO_IP_LOOKUP_URL = 'http://api.hostip.info/?ip=%s'
            GML_NS = 'http://www.opengis.net/gml'

            try:

                if "." in arguments[1]:
                    ip_address = arguments[1]
                    ip_address = socket.gethostbyaddr(ip_address)[2][0]
                else:
                    username = arguments[1]
                    ip_address = self.irc.chanlist[channel][username]['host']
                    ip_address = socket.gethostbyaddr(ip_address)[2][0]

            except:
                self.irc.sendmsg(channel, "[%s] No location found" % (arguments[1]))
                return

            try:
                data = urllib.urlopen(GEO_IP_LOOKUP_URL % ip_address)
                xml = data.read()

                dom = minidom.parseString(xml)
                elem = dom.getElementsByTagName('Hostip')[0]
                location = elem.getElementsByTagNameNS(GML_NS, 'name')[0].firstChild.data.partition(',')

                country = elem.getElementsByTagName('countryName')[0].firstChild.data
                loc = location[0].strip() + ", " + location[2].strip()

                if country == "(Unknown Country?)":
                    self.irc.sendmsg(channel, "[%s] No location found" % ip_address)
                    return

                self.irc.sendmsg(channel, "[%s] Country: %s, Location: %s" % (ip_address, country, loc))

            except KeyError:
                self.irc.sendmsg(channel, "[%s] No location found" % (ip_address))
        else:
            self.irc.sendnotice(user, "Usage: %sgeoip <address|nick>" % self.irc.control_char)