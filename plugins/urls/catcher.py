__author__ = 'Gareth Coles'

import os

#from system.storage.formats import DBAPI
from utils.misc import AttrDict


class Catcher(object):
    where = ""

    config = {}
    plugin = None
    storage = None
    logger = None

    sql = None

    def __init__(self, plugin, config, storage, logger):
        self.config = config
        self.plugin = plugin
        self.storage = storage
        self.logger = logger

        self.where = os.path.dirname(os.path.abspath(__file__))
        self.sql = AttrDict(create="", find="", insert="")

    def reload(self):
        pass

    def load_sql(self, dialect):
        base_path = "%s/%s/" % (self.where, dialect)
        if os.path.exists(base_path):
            self.sql.create = open(base_path + "create.sql").read()
            self.sql.find = open(base_path + "find.sql").read()
            self.sql.insert = open(base_path + "insert.sql").read()
        else:
            raise ValueError("No SQL found for dialect %s." % dialect)

    def create_interaction(self, txn):
        sql = self.sql.create

    def find_interaction(self, txn):
        swql = self.sql.find

    def insert_interaction(self, txn):
        sql = self.sql.insert

    def insert_url(self, url, user, target, protocol):
        pass
