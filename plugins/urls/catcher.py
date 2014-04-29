__author__ = 'Gareth Coles'

import datetime
import os

from system.protocols.generic.channel import Channel
from system.storage.formats import DBAPI


class Catcher(object):
    where = ""

    config = {}
    plugin = None
    storage = None
    logger = None

    sql = None
    db = None

    ignored = []

    enabled = False

    def __init__(self, plugin, config, storage, logger):
        if "catcher" not in config:
            logger.debug("No catcher section in config.")
            self.enabled = False
            return

        self.enabled = config["catcher"].get("use", False)

        if not self.enabled:
            logger.debug("Catcher disabled via config.")
            return

        self.config = config["catcher"]
        self.ignored = self.config.get("ignored", [])
        self.plugin = plugin
        self.storage = storage
        self.logger = logger

        self.where = os.path.dirname(os.path.abspath(__file__))
        self.sql = dict(create="", find="", insert="")

        self.reload()

    def _log_callback_success(self, result, message, use_result=False):
        if use_result:
            self.logger.info(message % result)
        else:
            self.logger.info(message)

    def _log_callback_failure(self, failure, message, use_failure=False):
        if use_failure:
            self.logger.error(message % failure)
        else:
            self.logger.error(message)

    def reload(self):
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
                       callbackArgs=("Created table.", False),
                       errbackArgs=("Failed to create table: %s", True))

    def load_sql(self, dialect):
        base_path = "%s/sql/%s/" % (self.where, dialect)
        self.logger.debug("Looking for SQL in %s" % base_path)
        if os.path.exists(base_path):
            self.sql["create"] = open(base_path + "create.sql").read()
            self.sql["find"] = open(base_path + "find.sql").read()
            self.sql["insert"] = open(base_path + "insert.sql").read()
        else:
            raise ValueError("No SQL found for dialect '%s'." % dialect)

    def create_interaction(self, txn):
        sql = self.sql["create"].replace(
            "{TABLE}", self.config["table_prefix"] + "_urls"
        )

        txn.execute(sql)

    def find_interaction(self, txn, url):
        sql = self.sql["find"].replace(
            "{TABLE}", self.config["table_prefix"] + "_urls"
        )

        txn.execute(sql, (url,))
        r = txn.fetchone()

        return r is not None

    def insert_interaction(self, txn, url, user, target, protocol):
        found = self.find_interaction(txn, url)

        if not found:
            sql = self.sql["insert"].replace(
                "{TABLE}", self.config["table_prefix"] + "_urls"
            )
            now = datetime.datetime.utcnow()

            txn.execute(sql, (url, now, user, target, protocol))

    def insert_url(self, url, user, target, protocol):
        if self.enabled:
            if isinstance(target, Channel):
                if "%s:%s" % (protocol.name, target.name) in self.ignored:
                    return
            d = self.db.runInteraction(self.insert_interaction,
                                       url, user, target, protocol)

            d.addErrback(self._log_callback_failure,
                         errbackArgs=("Failed to insert URL: %s", True))
