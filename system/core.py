# coding=utf-8
from system.factory_manager import FactoryManager
from system.logging.logger import getLogger

__author__ = 'Gareth Coles'


class Ultros(object):
    def __init__(self, parsed_args):
        self.parsed_args = parsed_args
        self.factory_manager = FactoryManager()
        self.factory_manager.setup_logging(self.parsed_args)
        self.logger = getLogger("Core")

    def start(self):
        self.factory_manager.setup()
        self.factory_manager.run()

    def stop(self):
        self.factory_manager.unload()
