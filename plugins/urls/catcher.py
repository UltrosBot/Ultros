"""Class designed for logging caught URLs. It doesn't work very well right now.

This uses a configured dbapi source along with some SQL defined in the sql/
folder. You can always add SQL there if you need another dialect.
"""

__author__ = 'Gareth Coles'

import datetime
import os

from socket import error as SocketError
from system.protocols.generic.channel import Channel
from system.storage.formats import DBAPI

from system.translations import Translations
_ = Translations().get()


class Catcher(object):
    """URL catcher object"""

    _config = {}
    where = ""

    plugin = None
    storage = None
    logger = None

    sql = None
    db = None

    pipe_breakages = 0

    @property
    def enabled(self):
        """Whether the catcher is enabled."""

        if "catcher" not in self._config:
            return False

        return self._config["catcher"].get("use", False)

    @property
    def config(self):
        """The catcher's configuration."""

        return self._config["catcher"]

    @property
    def ignored(self):
        """The catcher's configured ignored sources."""

        return self.config.get("ignored", [])

    def __init__(self, plugin, config, storage, logger):
        self._config = config

        if "catcher" not in config:
            logger.debug(_("No catcher section in config."))
            return

        if not self.enabled:
            logger.debug(_("Catcher disabled via config."))
            return

        self.plugin = plugin
        self.storage = storage
        self.logger = logger

        self.where = os.path.dirname(os.path.abspath(__file__))
        self.sql = dict(create="", find="", insert="")

        self.reload()

    def _log_callback_success(self, result, message, use_result=False):
        """Log that a callback succeeded."""

        if use_result:
            self.logger.info(message % result)
        else:
            self.logger.info(message)

    def _log_callback_failure(self, failure, message, use_failure=False):
        """Log that a callback failed."""

        if isinstance(failure, SocketError):
            if failure.errno == 32:
                if self.pipe_breakages < 3:
                    self.pipe_breakages += 1
                    self.db.reconnect()
                    return
                else:
                    self.logger.error(_("Broken pipe has occurred more than "
                                        "three times in a row!"))

        if use_failure:
            self.logger.error(message % failure)
        else:
            self.logger.error(message)

    def reload(self):
        """Reload the catcher entirely."""

        self.load_sql(self.config["dialect"])

        params = self.config["params"]

        if isinstance(params, dict):  # Standard dictionary access
            self.db = self.storage.get_file(
                self.plugin, "data", DBAPI,
                "%s:%s" % (self.config["adapter"], self.config["descriptor"]),
                **params
            )
        else:  # Shitty adapter that requires non-kwargs
            self.db = self.storage.get_file(
                self.plugin, "data", DBAPI,
                "%s:%s" % (self.config["adapter"], self.config["descriptor"]),
                *params
            )

        d = self.db.runInteraction(self.create_interaction)

        d.addCallbacks(self._log_callback_success,
                       self._log_callback_failure,
                       callbackArgs=(_("Created table."), False),
                       errbackArgs=(_("Failed to create table: %s"), True))

    def load_sql(self, dialect):
        """Load the SQL for a certain dialect."""

        base_path = "%s/sql/%s/" % (self.where, dialect)
        self.logger.debug(_("Looking for SQL in %s") % base_path)
        if os.path.exists(base_path):
            self.sql["create"] = open(base_path + "create.sql").read()
            self.sql["find"] = open(base_path + "find.sql").read()
            self.sql["insert"] = open(base_path + "insert.sql").read()
        else:
            raise ValueError(_("No SQL found for dialect '%s'.") % dialect)

    def create_interaction(self, txn):
        """DBAPI interaction for creating the table."""

        sql = self.sql["create"].replace(
            "{TABLE}", self.config["table_prefix"] + "_urls"
        )

        txn.execute(sql)

    def find_interaction(self, txn, url):
        """DBAPI interaction for finding a URL."""

        sql = self.sql["find"].replace(
            "{TABLE}", self.config["table_prefix"] + "_urls"
        )

        txn.execute(sql, (url,))
        r = txn.fetchone()

        return r is not None

    def insert_interaction(self, txn, url, user, target, protocol):
        """DBAPI interaction for inserting a URL."""

        found = self.find_interaction(txn, url)
        self.pipe_breakages = 0

        if not found:
            sql = self.sql["insert"].replace(
                "{TABLE}", self.config["table_prefix"] + "_urls"
            )
            now = datetime.datetime.utcnow()

            txn.execute(sql, (url, now, user, target, protocol))

    def insert_url(self, url, user, target, protocol):
        """Insert a URL into the database."""

        if self.enabled:
            if isinstance(target, Channel):
                if "%s:%s" % (protocol.name, target.name) in self.ignored:
                    return
            d = self.db.runInteraction(self.insert_interaction,
                                       url, user, target, protocol)

            d.addErrback(
                self._log_callback_failure,
                _("Failed to insert URL: %s"),
                True
            )
