# coding=utf-8
import pprint
import json

from system.yaml_loader import *
from system.decorators import *

from twisted.internet import reactor
from twisted.web.server import Site
from twisted.web.resource import Resource, NoResource, ForbiddenResource

def authorized(keys, request):
    if "api_key" in request.args:
        key = request.args["api_key"][0]
        return key in keys
    return False

class plugin(object):

    """
    This is a webserver. It provides access to the bot using
    a variety of JSON APIs, as well as supporting various
    external services via webhooks.

    Oh boy, are we excited about /this/ plugin!
    """

    hooks = {}

    name = "Webserver"

    commands = {
    }

    # You don't need to do this, most likely. I did because of the initializer stuff, though.

    def intercom_send(self, target, data):
        pass

    def _intercom_send(self, target, data):
        print self.intercom_send(self, target, data)

    # OK, that's all the crazy stuff done!

    def __init__(self, irc):
        self.irc = irc
        self.help = {
        }

        self.settings_handler = yaml_loader(True, "web")
        self.settings = self.settings_handler.load("settings", {"api_keys": [], "port": 8080})

        resource = BaseResource(irc, self.settings, self._intercom_send)
        factory = Site(resource)
        reactor.listenTCP(self.settings["port"], factory)

    def intercom(self, origin, data):
        pass


class BaseResource(Resource):

    isLeaf = False
    children = {}

    def __init__(self, irc, settings, send):
        Resource.__init__(self)
        self.api_keys = settings["api_keys"]
        self.irc = irc
        self.children = {"api": ApiResource(irc, self.api_keys), "test": TestResource(irc, self.api_keys, send), "": self}

    def render_GET(self, request):
        print "[WEB] %s %s: %s" % (request.getClientIP(), request.method, request.uri)
        return "This is the base resource. Check out <a href=\"test\">/test</a> and <a href=\"api\">/api</a> for more."

    def getChild(self, path, request):
        if path not in self.children.keys():
            return NoResource()


class ApiResource(Resource):

    isLeaf = False
    children = {}

    def __init__(self, irc, api_keys):
        Resource.__init__(self)
        self.api_keys = api_keys
        self.irc = irc
        self.children = {"github": GithubResource(irc, self.api_keys),
                         "privmsg": PrivmsgResource(irc, self.api_keys),
                         "": self}

    def render_GET(self, request):
        print "[WEB] %s %s: %s" % (request.getClientIP(), request.method, request.uri)
#        if "messages" in request.args.keys():
#            for msg in request.args["messages"]:
#                self.irc.sendmsg("#mcblockit-test", msg)
        if authorized(self.api_keys, request):
            return "Grats, you found the API resource! Nothing here yet, though.."
        else:
            print "[WEB] -> 401 Not Authorized"
            request.setResponseCode(401)
            request.setHeader("content-type", "text/html; charset=utf-8")
            return "<html><head><title>401 - Not Authorized</title></head><body><h1>Not Authorized</h1><p>You are not " \
                   "authorized to access this resource. Perhaps you're missing an API key?</p></body></html>"

    def getChild(self, path, request):
        if path not in self.children.keys():
            return NoResource()


class GithubResource(Resource):

    isLeaf = True
    def __init__(self, irc, api_keys):
        Resource.__init__(self)
        self.api_keys = api_keys
        self.irc = irc
        settings_handler = yaml_loader(True, "web")
        settings = settings_handler.load("github", {"projects": {"McBlockit---Helpbot": ["#archives"]}})
        self.repos = settings["projects"]

    def render_POST(self, request):
        print "[WEB] %s %s: %s" % (request.getClientIP(), request.method, request.uri)
        if not authorized(self.api_keys, request):
            print "[WEB] -> 401 Not Authorized"
            request.setResponseCode(401)
            request.setHeader("content-type", "text/html; charset=utf-8")
            return "<html><head><title>401 - Not Authorized</title></head><body><h1>Not Authorized</h1><p>You are not "\
                   "authorized to access this resource. Perhaps you're missing an API key?</p></body></html>"
        settings_handler = yaml_loader(True, "web")
        settings = settings_handler.load("github")
        self.repos = settings["projects"]
        try:
            for payload in request.args["payload"]:
                payload = json.loads(payload)
                repo = payload["repository"]
                head = payload["head_commit"]

                author = head["author"]["name"]
                repo_name = repo["name"]
                added = len(head["added"])
                modified = len(head["modified"])
                removed = len(head["removed"])
                message = head["message"]
                if "\n" in message:
                    message = message.split("\n")[0]
                commits = len(payload["commits"])

                if repo_name in self.repos:
                    for channel in self.repos[repo_name]:
                        self.irc.sendmsg(channel, "%s pushed a commit to %s (%sa/%sm/%sd) - \"%s\" [Total: %s commits]" %
                                                  (author, repo_name, added, modified, removed, message, commits))
                else:
                    print "[WEB] Alert - Recieved data for a repo we don't follow: \"%s\"" % repo_name
                    return json.dumps({"result": "error", "error": "Not following that repo!"})
        except Exception as e:
            print "[WEB] Error: %s" % e
            return json.dumps({"result": "error", "error": str(e)})
        else:
            return json.dumps({"result": "success"})

class PrivmsgResource(Resource):

    isLeaf = True
    def __init__(self, irc, api_keys):
        Resource.__init__(self)
        self.api_keys = api_keys
        self.irc = irc

    def render_POST(self, request):
        print "[WEB] %s %s: %s" % (request.getClientIP(), request.method, request.uri)
        if not authorized(self.api_keys, request):
            print "[WEB] -> 401 Not Authorized"
            request.setResponseCode(401)
            request.setHeader("content-type", "text/html; charset=utf-8")
            return "<html><head><title>401 - Not Authorized</title></head><body><h1>Not Authorized</h1><p>You are not "\
                   "authorized to access this resource. Perhaps you're missing an API key?</p></body></html>"
        try:
            for payload in request.args["payload"]:
                payload = json.loads(payload)
                target  = payload["target"]
                message = payload["message"]
                if "source" in payload:
                    if payload["source"] == "mybb":
                        message = message.decode("string-escape").replace("\n", "\\n").replace("\t", "\\t").replace("\r", "\\r")
                message = message.replace("%COL%", self.irc.col)
                self.irc.sendmsg(target, message)
        except Exception as e:
            print "[WEB] Error: %s" % e
            return json.dumps({"result": "error", "error": str(e)})
        else:
            return json.dumps({"result": "success"})

class TestResource(Resource):

    isLeaf = True
    def __init__(self, irc, api_keys, send):
        self.send = send
        self.api_keys = api_keys
        Resource.__init__(self)
        self.irc = irc

    def render_GET(self, request):
        print "[WEB] %s %s: %s" % (request.getClientIP(), request.method, request.uri)
        self.send("Test", "TESTING!")
        return "Request: %s<br/><br/>"\
               "Path: %s<br/><br/>"\
               "Args: %s<br/><br/>"\
               "Headers: %s<br /><br />"\
               "IRC: %s" % (str(request).replace("<", "&lt;").replace(">", "&gt;"),
                            request.path, request.args, request.requestHeaders, pprint.pformat(self.irc.chanlist, 2).replace(" ", "&nbsp;").replace("\n", "<br />"))

    def render_POST(self, request):
        print "[WEB] %s %s: %s" % (request.getClientIP(), request.method, request.uri)
        return "Request: %s<br/><br/>"\
               "Path: %s<br/><br/>"\
               "Args: %s<br/><br/>"\
               "Headers: %s<br /><br />"\
               "IRC: %s" % (str(request).replace("<", "&lt;").replace(">", "&gt;"),
                            request.path, request.args, request.requestHeaders, pprint.pformat(self.irc.chanlist, 2).replace(" ", "&nbsp;").replace("\n", "<br />"))
