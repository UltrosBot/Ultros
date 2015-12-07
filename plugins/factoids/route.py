# coding=utf-8

from cyclone.web import asynchronous
from xml.sax.saxutils import escape

from plugins.web.request_handler import RequestHandler


__author__ = 'Gareth Coles'


class Route(RequestHandler):

    factoids = None
    name = "factoids"

    def initialize(self):
        #: :type: FactoidsPlugin
        self.factoids = self.plugin.plugins.get_plugin("factoids")

    @asynchronous
    def get(self, *args, **kwargs):
        s = self.get_session_object()

        if not self.plugin.check_permission(self.factoids.PERM_GET % "web", s):
            if s is None:
                # They need to login
                self.redirect(
                    "/login",
                    message="You need to login to access this.",
                    message_colour="red",
                    redirect="/factoids"
                )
            else:
                # They don't have permission
                content = """
<div class="ui red fluid message">
    <p>You do not have permission to list the factoids.</p>
    <p> If you feel this was in error, tell a bot admin to give you the
        <code>factoids.get.web</code> permission.
    </p>
</div>
                """

                self.render(
                    "generic.html",
                    _title="Factoids | No permission",
                    content=content
                )
        else:
            d = self.factoids.get_all_factoids()

            d.addCallbacks(self.success_callback, self.fail_callback)

    def success_callback(self, result):
        if len(result) < 1:
            content = """
<div class="ui yellow fluid segment">
    <p>No factoids found.</p>
</div>
            """
        else:
            content = "<table class=\"ui celled table segment " \
                "table-sortable\">"
            content += "<thead>" \
                       "<tr>" + \
                       "<th>Location</th>" + \
                       "<th>Protocol</th>" + \
                       "<th>Channel</th>" + \
                       "<th>Name</th>" + \
                       "<th>Content</th>" + \
                       "</tr></thead>" \
                       "<tbody>"
            for row in result:
                content += "<tr>"

                for column in row:
                    content += "<td>%s</td>" % escape(column).replace(
                        "\n", "<br /><br />"
                    )
                content += "</tr>"

            content += "</tbody>" \
                       "</table>"

        self.render(
            "generic.html",
            _title="Factoids",
            content=content
        )

    def fail_callback(self, failure):
        self.set_status(500)

        self.write_error(500, exception=failure)
