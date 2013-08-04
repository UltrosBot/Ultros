# coding=utf-8
import json
try:
    from bs4 import BeautifulSoup
except ImportError:
    from BeautifulSoup import BeautifulSoup
import urllib
import urllib2
import urlparse
from system.decorators import *
from system.yaml_loader import *

class plugin(object):
    """
    URL parser; used to fetch titles for URLs pasted in IRC.
    """

    name = "URL Title Fetcher"

    commands = {
        "urltitle": "url_options",
        "title": "fetch_title",
        "shorturl": "fetch_short_url"
    }

    hooks = {
        "connectionLost": "save",
        "signedOn": "load",
        "privmsg": "privmsg"
    }

    # Extensions the page title parser shouldn't parse
    notParse = ["png", "jpg", "jpeg", "tiff", "bmp", "ico", "gif", "iso", "bin", "pub", "ppk", "doc", "docx", "xls",
                "xlsx", "ppt", "pptx", "svg"]

    channels = {}

    def __init__(self, irc):
        self.irc = irc
        self.settings = yaml_loader(True, "urltitlefetcher")

        self.channels = {}

        self.help = {
            "urltitle": "Toggle url title fetching for the current channel.\n" +
                        ("Usage: %surltitle [all|on|off]\n" % self.irc.control_char) +
                        "all = all users, on = voiced and up, off = no-one",
            "title":    "Fetch the title of a given URL, or the last URL sent to the channel if no URL is given.\n" +
                        ("Usage: %stitle [url]\n" % self.irc.control_char) +
                        "NOTE: If title fetching is off in the current channel, this will notice the user rather than message the channel if they are not voiced or above.",
            "shorturl": "Get a short URL for a given URL, or the last URL sent to the channel if no URL is given.\n" +
                        ("Usage: %sshorturl [url]\n" % self.irc.control_char) +
                        "NOTE: If title fetching is off in the current channel, this will notice the user rather than message the channel if they are not voiced or above."
            }

        self.YOUTUBE_LOGO = irc.col + "01,00YOU" + irc.col + "00,04TUBE" + irc.col
        self.OUTPUT_YOUTUBE_VIDEO = "[" + self.YOUTUBE_LOGO + " Video] %s (%s) by %s, %s likes, %s dislikes, %s views"
        self.OUTPUT_YOUTUBE_PLAYLIST = "[" + self.YOUTUBE_LOGO + " Playlist] %s (%s videos, total %s) by %s - \"%s\""
        self.OUTPUT_YOUTUBE_CHANNEL = "[" + self.YOUTUBE_LOGO + " Channel] %s (%s subscribers, %s videos with %s total views) - \"%s\""

        self.YOUTUBE_DESCRIPTION_LENGTH = 75

        self.OSU_LOGO = irc.col + "13osu!" + irc.col
        self.OSU_MAP_FORMAT = "[" + self.OSU_LOGO + " map] %s [%s]"

    def load(self):
        self.channels = self.settings.load("channels")
        if not self.channels:
            self.channels = {}

    def save(self, data=None):
        self.settings.save_data("channels", self.channels)

    def setup_channel(self, channel):
        """
        Initialises the channel settings if they have not yet been done
        """
        if not self.channels.has_key(channel):
            self.channels[channel] = {"status": "all", "last": None}
        elif not isinstance(self.channels[channel], dict):
            #I assume this is in case an old config is loaded where there is only one option per channel, rather than a dict of options
            self.channels[channel] = {"status": self.channels[channel], "last": None}

    def privmsg(self, data):
        user = data['user']
        channel = data['channel']
        message = data['message']

        if message.startswith(self.irc.control_char):
            return

        self.setup_channel(channel)
        if self.channels[channel]["status"] == "off":
            return

        messagelower = message.lower()
        pos = messagelower.find("http://")
        if pos == -1:
            pos = messagelower.find("https://")
        if pos > -1:
            end = messagelower.find(" ", pos)
            if end > -1:
                url = message[pos:end]
            else:
                url = message[pos:]
            self.channels[channel]["last"] = url
            msg = self.get_url_message(url)
            if msg is not None:
                self.send_to_right_place(msg, channel, user)

    def fetch_title(self, user, channel, arguments):
        self.setup_channel(channel)
        url = None
        if len(arguments) == 2:
            url = arguments[1]
        elif self.channels[channel]["last"] is not None:
            url = self.channels[channel]["last"]
        else:
            return
        msg = self.get_url_message(url)
        if msg is None:
            msg = "No title or not a URL"
        self.send_to_right_place(msg, channel, user)

    @config("rank", "op")
    def url_options(self, user, channel, arguments):
        self.setup_channel(channel)
        if len(arguments) == 1:
            self.irc.sendnotice(user, "URL title fetching for this channel is %s" % (self.channels[channel]["status"]))
        elif len(arguments) == 2:
            arguments[1] = arguments[1].lower()
            if arguments[1] == "on" or arguments[1] == "true":
                self.channels[channel]["status"] = "on"
            elif arguments[1] == "off" or arguments[1] == "false":
                self.channels[channel]["status"] = "off"
            elif arguments[1] == "all":
                self.channels[channel]["status"] = "all"
            else:
                self.irc.sendnotice(user, "Invalid option given for title matching")
                return
            self.irc.sendnotice(user, "URL title fetching for this channel has been set to %s" % (self.channels[channel]["status"]))

    def fetch_short_url(self, user, channel, arguments):
        self.setup_channel(channel)
        url = None
        if len(arguments) == 2:
            url = arguments[1]
        elif self.channels[channel]["last"] is not None:
            url = self.channels[channel]["last"]
        else:
            return
        tiny = self.short_url(url)
        if tiny is None:
            tiny = "Could not get short url"
        self.send_to_right_place("Short URL %s for %s" % (tiny, url), channel, user)

    def send_to_right_place(self, message, channel, user):
        """
        Send the given message to the right place, depending on channel settings.
        If channel status is all:
            send to channel
        If channel status is on:
            If user is voice+;
                send to channel
            Else:
                notice to user
        Else:
            notice to user
        """
        if self.channels[channel]["status"] == "all" or (self.channels[channel]["status"] == "on" and (self.irc.is_voice(channel, user) or self.irc.is_op(channel, user))):
            self.irc.sendmsg(channel, message)
        else:
            self.irc.sendnotice(user, message)

    def short_url(self, url):
        """
        Returns a tinyurl.com short url
        """
        return urllib2.urlopen("http://tinyurl.com/api-create.php?url=" + urllib.quote_plus(url)).read()

    def get_url_message(self, url):
        message = self.special_domain(url)
        if message is None:
            title, domain = self.page_title(url)
            if title is None:
                return None
            message = "\"%s\" at %s" % (title, domain)
        return message

    def page_title(self, url):
        """
        Get the page title and domain
        """
        if url.split(".")[-1] in self.notParse:
            return None, None
        else:
            domain = ""
            try:
                parsed = urlparse.urlparse(url)
                domain = parsed.hostname
                request = urllib2.Request(url)
                request.add_header('User-agent', 'Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.0.1) Gecko/2008071615 Fedora/3.0.1-1.fc9-1.fc9 Firefox/3.0.1')
                page = urllib2.urlopen(request).read()
                soup = BeautifulSoup(page)
                title = unicode(soup.title.string).encode("UTF-8")
                return title, domain
            except Exception as e:
                if not str(e).lower() == "not viewing html":
                    return str(e), domain
                return None, None

    def special_domain(self, url):
        """
        Returns the message to be displayed if it is a special domain, or None if it should be treated regularly
        """
        parsed = urlparse.urlparse(url)
        hostname = parsed.hostname.lower()
        if hostname[:4] == "www.":
            hostname = hostname[4:]
        if hostname == "youtube.com":
            if parsed.path.lower() == "/watch":
                params = urlparse.parse_qs(parsed.query)
                if "v" in params and len(params["v"]) > 0:
                    try:
                        video_data = json.loads(urllib2.urlopen("http://gdata.youtube.com/feeds/api/videos/" + params["v"][0] + "?v=2&alt=json").read())
                        title = video_data["entry"]["media$group"]["media$title"]["$t"]
                        uploader = video_data["entry"]["media$group"]["media$credit"][0]["yt$display"]
                        time = self.seconds_to_time(int(video_data["entry"]["media$group"]["yt$duration"]["seconds"]))
                        views = video_data["entry"]["yt$statistics"]["viewCount"]
                        likes = video_data["entry"]["yt$rating"]["numLikes"]
                        dislikes = video_data["entry"]["yt$rating"]["numDislikes"]
                        return self.OUTPUT_YOUTUBE_VIDEO % (title, time, uploader, likes, dislikes, views)
                    except:
                        pass
            elif parsed.path.lower() == "/playlist":
                params = urlparse.parse_qs(parsed.query)
                if "list" in params and len(params["list"]) > 0:
                    try:
                        playlist_data = json.loads(urllib2.urlopen("http://gdata.youtube.com/feeds/api/playlists/" + params["list"][0] + "?v=2&alt=json").read())
                        title = playlist_data["feed"]["title"]["$t"]
                        author = playlist_data["feed"]["author"][0]["name"]["$t"]
                        description = playlist_data["feed"]["subtitle"]["$t"]
                        description = self.make_description_nice(description, self.YOUTUBE_DESCRIPTION_LENGTH)
                        count = len(playlist_data["feed"]["entry"])
                        seconds = 0
                        for entry in playlist_data["feed"]["entry"]:
                            seconds += int(entry["media$group"]["yt$duration"]["seconds"])
                        time = self.seconds_to_time(seconds)
                        return self.OUTPUT_YOUTUBE_PLAYLIST % (title, count, time, author, description)
                    except:
                        pass
            elif parsed.path.lower().startswith("/user/"):
                parts = parsed.path.split("/")
                if len(parts) >= 3:
                    try:
                        user_data = json.loads(urllib2.urlopen("http://gdata.youtube.com/feeds/api/users/" + parts[2] + "?v=2&alt=json").read())
                        name = user_data["entry"]["title"]["$t"]
                        description = user_data["entry"]["summary"]["$t"]
                        description = self.make_description_nice(description, self.YOUTUBE_DESCRIPTION_LENGTH)
                        subscribers = user_data["entry"]["yt$statistics"]["subscriberCount"]
                        views = user_data["entry"]["yt$statistics"]["totalUploadViews"]
                        videos = None
                        for entry in user_data["entry"]["gd$feedLink"]:
                            if entry["rel"].endswith("#user.uploads"):
                                videos = entry["countHint"]
                                break
                        return self.OUTPUT_YOUTUBE_CHANNEL % (name, subscribers, videos, views, description)
                    except:
                        pass
        elif hostname == "osu.ppy.sh":
            parts = parsed.path.split("/")
            if len(parts) >= 3:
                try:
                    if parts[1] == "b" or parts[1] == "s":
                        osu_map = parts[1] + "/" + parts[2]
                        json_data = urllib.urlopen("http://ash.gserv.me:8000/json/%s" % osu_map).read()
                        map_data = json.loads(json_data)
                        return self.OSU_MAP_FORMAT % (map_data["title"], map_data["difficulty"])
                    elif parts[1] == "u":
                        osu_user = parts[2]
                        #TODO: Get the user data and return a nice message
                except Exception as e:
                    print (e)
                    pass
            #Not a special URL or error while processing it - the calling code can get the html title tag instead
        return None

    def seconds_to_time(self, secs):
        #There's probably a more "pythonic" way to do this, but I didn't know of one
        m, s = divmod(secs, 60)
        if m >= 60:
            h, m = divmod(m, 60)
            return "%d:%02d:%02d" % (h, m, s)
        else:
            return "%d:%02d" % (m, s)

    def make_description_nice(self, description, max_length = -1):
        """
        Replace newlines with spaces and limit length
        """
        description = description.strip()
        description = description.replace("\r\n", " ").replace("\r", " ").replace("\n", " ")
        if max_length > 0 and len(description) > max_length:
            description = description[:max_length - 3] + "..."
        return description
