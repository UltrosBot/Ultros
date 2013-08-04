# coding=utf-8
import os, string
import fnmatch

from evalfunctions import evalFunctions
from system.constants import *
from system.yaml_loader import *


class FAQ(object):
    config = {}

    def __init__(self, path, bot):
        self.path = path
        if not os.path.exists(path):
            os.mkdir(path)
        self.bot = bot
        self.evalObj = evalFunctions(bot)

        settings = yaml_loader()
        settings = settings.load("config/settings.yml")["faq"]

        self.config["type"] = settings["type"]
        location = settings["location"]
        if location[-1] == "/" or location[-1] == "\\":
            self.config["location"] = location
        else:
            self.config["location"] = location + "/"
        self.config["name"] = settings["name"]
        self.config["num_colours"] = int(settings["colours"])
        self.config["css"] = settings["css"]

        self.config["colours"] = settings["generated_colours"]

    def get(self, entry, cinfo):
        entry += ".txt"
        path = self.path
        epath = path + "/" + entry
        while ".." in epath:
            epath = epath.replace("..", ".")
        if os.path.exists(epath):
            fh = open(epath, "r")
            data = fh.read()
            fh.close()
            del fh
            rdata = data.split("\n")
            try:
                rdata.remove("")
            except:
                pass
            done = []
            for element in rdata:
                if "$(" in element and ")" in element:
                    stuff = element.split("$(", 1)
                    stuff = stuff[1].split(")")
                    del stuff[-1]
                    stuff = ")".join(stuff)
                    try:
                        result = self.evalObj.seval(stuff, cinfo)
                    except Exception as e:
                        result = str(e)
                    element = element.replace("$(%s)" % stuff, result)
                    if "\n" in element:
                        for part in element.split("\n"):
                            if part.strip() != "":
                                done.append(part)
                    else:
                        done.append(element)
                else:
                    done.append(element)

            return[True, done]
        else:
            return [False, ERR_NO_SUCH_ENTRY]

    def get_noeval(self, entry, cinfo):
        entry += ".txt"
        path = self.path
        epath = path + "/" + entry
        while ".." in epath:
            epath = epath.replace("..", ".")
        if os.path.exists(epath):
            fh = open(epath, "r")
            data = fh.read()
            fh.close()
            del fh
            rdata = data.split("\n")
            try:
                rdata.remove("")
            except:
                pass
            return[True, rdata]
        else:
            return [False, ERR_NO_SUCH_ENTRY]

    def set(self, entry, data, mode):
        entry += ".txt"
        path = self.path
        epath = path + "/" + entry
        while ".." in epath:
            epath = epath.replace("..", ".")
        if os.path.exists(epath):
            if mode == MODE_APPEND:
                fh = open(epath, "a")
                fh.write(data)
                fh.write("\n")
                fh.flush()
                fh.close()
                del fh
                return [True, RESULT_SUCCESS]
            elif mode == MODE_REMOVE:
                os.remove(epath)
                self.cleandirs(self.path)
                return [True, RESULT_SUCCESS]
            elif mode == MODE_REPLACE:
                fh = open(epath, "w")
                fh.write(data)
                fh.write("\n")
                fh.close()
                del fh
                return [True, RESULT_SUCCESS]
        else:
            if mode == MODE_APPEND:
                makepath = epath.split("/")
                makepath.remove(makepath[-1])
                try:
                    os.makedirs("/".join(makepath))
                except Exception:
                    pass
                fh = open(epath, "a")
                fh.write(data)
                fh.write("\n")
                fh.flush()
                fh.close()
                del fh
                return [True, RESULT_SUCCESS]
            elif mode == MODE_REMOVE:
                return [False, ERR_NO_SUCH_ENTRY]
            elif mode == MODE_REPLACE:
                makepath = epath.split("/")
                makepath.remove(makepath[-1])
                try:
                    os.makedirs("/".join(makepath))
                except Exception:
                    pass
                fh = open(epath, "w")
                fh.write(data)
                fh.write("\n")
                fh.close()
                del fh
                return [True, RESULT_SUCCESS]

    def cleandirs(self, path):
        files = os.listdir(path)
        dirs = []
        for element in files:
            if os.path.isdir(path + "/" + element):
                dirs.append(element)

        for element in dirs:
            if len(os.listdir(path + "/" + element)) is 0:
                os.rmdir(path + "/" + element)
            elif os.path.isdir(path + "/" + element):
                self.cleandirs(path + "/" + element)
                if len(os.listdir(path + "/" + element)) is 0:
                    os.rmdir(path + "/" + element)

    def listentries(self, depreciated=None):
        if self.config["type"] in ["html", "txt", "both"]:
            if self.config["type"] == "html" or self.config["type"] == "both":
                if self.config["css"] == "generated":
                    self.listentries_html(self.config["location"], self.config["name"], self.config["colours"], cols=0)
                else:
                    self.listentries_html(self.config["location"], self.config["name"], [], False,
                        self.config["num_colours"])
                if self.config["type"] == "both":
                    self.listentries_text(self.config["location"] + self.config["name"] + ".txt")
            else:
                self.listentries_text(self.config["location"] + self.config["name"] + ".txt")

    def listentries_text(self, filehname="topics.txt"):
        buffer = []
        for root, dirs, files in os.walk(self.path):
            for filename in fnmatch.filter(files, "*.txt"):
                if root is self.path:
                    buffer.append("%s" % filename.split(".txt")[0])
                else:
                    data = string.replace(root, "\\", "/")
                    data = "".join(data.split("/")[1:])
                    buffer.append("%s/%s" % (data, filename.split(".txt")[0]))
        buffer.sort(key=str.lower)
        buffer = "\n".join(buffer)
        fh = open(filehname, "w")
        fh.write(buffer)
        fh.flush()
        fh.close()

    def listentries_html(self, f_path="./", f_name="topics", colours=None, css_switch=True, cols=3):
        if not colours: colours = ["#99CCFF", "#99FF99", "#FF9999"]
        buffer = []
        for root, dirs, files in os.walk(self.path):
            for filename in fnmatch.filter(files, "*.txt"):
                if root is self.path:
                    buffer.append("%s" % filename.split(".txt")[0])
                else:
                    data = string.replace(root, "\\", "/")
                    data = "".join(data.split("/")[1:])
                    buffer.append("%s/%s" % (data, filename.split(".txt")[0]))
        buffer.sort(key=str.lower)
        f_html = f_name + ".html"
        if css_switch:
            f_css = f_name + ".css"
        else:
            f_css = self.config["css"]

        html = """
<!DOCTYPE html>
<html>
    <head>
        <meta lang=\"en/us\" />
        <title>FAQ Topics</title>
        <link rel=\"stylesheet\" href=\"{CSSFILE}\" />
    </head>
    <body>
        <table>
            <tr>
                <th> Entry </th>
                <th> Content </th>
            </tr>"""

        html = html.replace("{CSSFILE}", f_css)

        template = """
            <tr class=\"{LINESTYLE}\">
                <th> {ENTRY} </th>
                <td> {CONTENT} </th>
            </tr>"""

        css = """
table
{
    border-collapse: collapse;
}

td, th
{
    vertical-align: top;
    border: 1px double black;
    padding-left: 1em;
    padding-right:1em;
}
"""

        if css_switch:
            i = 0

            for element in colours:
                css_class = "COLOUR-" + str(i)
                css += "." + css_class + "\n{\n    background-color: " + element +\
                       ";\n    text-align: left;\n}\n"
                i += 1

        i = 0

        for element in buffer:
            entries = self.get_noeval(element, None)
            if not entries[0]:
                continue # Simple fix for a missing entry fail
            if css_switch:
                css_class = "COLOUR-" + str(i)
                if i == len(colours) - 1:
                    i = 0
                else:
                    i += 1

            else:
                css_class = "COLOUR-" + str(i)
                if i == cols - 1:
                    i = 0
                else:
                    i += 1
            entries = "<br />".join(entries[1])

            done = template.replace("{LINESTYLE}", css_class)
            done = done.replace("{ENTRY}", element)
            done = done.replace("{CONTENT}", entries)

            html += done

        html += """        </table>
    </body>
</html>"""

        html = html.replace(self.bot.col, "[COLOUR]")
        html = html.replace(self.bot.bold, "[BOLD]")
        html = html.replace(self.bot.under, "[UNDERLINE]")
        html = html.replace(self.bot.ital, "[ITALIC]")
        html = html.replace(self.bot.reverse, "[REVERSE]")
        html = html.replace(self.bot.ctcp, "[CTCP]")

        fh = open(f_path + f_html, "w")
        fh.write(html)
        fh.flush()
        fh.close()

        del fh

        if css_switch:
            fh = open(f_path + f_css, "w")
            fh.write(css)
            fh.flush()
            fh.close()

            del fh