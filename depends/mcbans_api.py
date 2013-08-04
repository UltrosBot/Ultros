# coding=utf-8
# Arc is copyright 2009-2011 the Arc team and other contributors.
# Arc is licensed under the BSD 2-Clause modified License.
# To view more details, please see the "LICENSING" file in the "docs" folder of the Arc Package.

# The Arc package can be found at http://archivesmc.com

import urllib, urllib2
try:
    import json
except ImportError:
    import simplejson as json

class McBans():
    def __init__(self, apikey):
        self.url = "http://72.10.39.172/v2" # No trailing "/"!
        self.key = apikey

    def _request(self, data):
        """Convenience function to send data to MCBans"""
        data = urllib.urlencode(data)
        request = urllib2.Request("%s/%s" % (self.url, self.key), data)
        response = urllib2.urlopen(request)
        readable = json.loads(response.read())
        return readable

    # Connection activity

    def connect(self, player, ip):
        data = {"player": player, "ip": ip, "exec": "playerConnect"}
        values = self._request(data)
        return values # {'banStatus': 'n', 'playerRep': 10, 'altList': 'username: REP 0, username: REP 10'(, 'banReason': 'banned')}

    def disconnect(self, player):
        data = {"player": player, "exec": "playerDisconnect"}
        values = self._request(data)
        return values # {'result': 'y'}
        
    def callBack(self, maxPlayers, playerList, version):
        done = ""
        if isinstance(playerList, list):
            done = ",".join(playerList)
        else:
            done = playerList
        data = {"maxPlayers": maxPlayers, "playerList": done, "version": version, "exec": "callBack"}
        values = self._request(data)
        return values # {'result': 'y'}

    # Banning activity

    def unban(self, player, admin):
        data = {"player": player, "admin": admin, "exec": "unBan"}
        values = self._request(data)
        return values # {"result": "y"}

    def localBan(self, player, ip, reason, admin):
        data = {"player": player, "ip": ip, "reason": reason, "admin": admin, "exec": "localBan"}
        values = self._request(data)
        return values # {"result": "y"}

    def globalBan(self, player, ip, reason, admin):
        data = {"player": player, "ip": ip, "reason": reason, "admin": admin, "exec": "globalBan"}
        values = self._request(data)
        return values # {"result": "y"}

    def tempBan(self, player, ip, reason, admin, duration, measure):
        if measure == "m" or measure == "h" or measure == "d":
            data = {"player": player, "ip": ip, "reason": reason, "admin": admin, "duration": duration, "measure": measure, "exec": "tempBan"}
            values = self._request(data)
        else:
            raise ValueError("'measure' must be m, h or d!")
        return values # {"result": "y"}

    # Lookups

    def lookup(self, player, admin="None"):
        data = {"player": player, "admin": admin, "exec": "playerLookup"}
        values = self._request(data)
        return values # {'global': ['servername .:. reason', 'servername .:. reason'], u'total': 4, u'local': ['servername .:. reason'], 'reputation': 5}

    def lookupAlts(self, player):
        #Premium-only
        #Non-premium usage returns {'result': 'n'}
        data = {"player": player, "exec": "altList"}
        values = self._request(data)
        return values # {'altListCount': 2, 'altList': 'altname: REP 10, anotheraltname: REP 10'}

    # Account confirmation

    def confirm(self, player, key):
        data = {"player": player, "string": key, "exec": "playerSet"}
        values = self._request(data)
        return values # {"result": "n"}

    # Messaging API

    def inbox(self, player):
        data = {"player": player, "exec": "getInbox"}
        values = self._request(data)
        return values # {"result": "n", "messages": ???}

    def getNewMessage(self, player):
        data = {"player": player, "exec": "getNewMessage"}
        values = self._request(data)
        return values # {"result": "n", "message": message}

    def getMessage(self, player, messageID):
        data = {"player": player, "message": messageID, "exec": "getMessage"}
        values = self._request(data)
        return values # {"result": "n", "message": message}

    def sendMessage(self, player, target, message):
        data = {"player": player, "target": target, "message": message, "exec": "sendMessage"}
        values = self._request(data)
        return values # {"result": "n"}

    def block(self, player, target):
        data = {"player": player, "target": target, "exec": "playerBlock"}
        values = self._request(data)
        return values # {"result": "a"}

    def unblock(self, player, target):
        data = {"player": player, "target": target, "exec": "playerUnBlock"}
        values = self._request(data)
        return values # {"result": "n"}