__author__ = 'Gareth Coles'

# Required: authorized(caller, source, protocol)


class authHandler(object):

    def __init__(self, config, plugin):
        self.config = config
        self.plugin = plugin

    def create_user(self, user, password):
        pass
