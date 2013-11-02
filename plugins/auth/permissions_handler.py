__author__ = 'Gareth Coles'

# Required: check(permission, caller, source, protocol)


class permissionsHandler(object):

    def __init__(self, config, plugin):
        self.config = config
        self.plugin = plugin

    def find_player(self, player):
        pass

    def find_group(self, group):
        pass

    def reload(self):
        return self.config.reload()

    def check(self, permission, caller, source, protocol):
        pass

    # User operations
    #  Modification

    def create_user(self, user):
        pass

    def remove_user(self, user):
        pass

    def set_user_option(self, user, option, value):
        pass

    def add_user_permission(self, user, permission):
        pass

    def remove_user_permission(self, user, permission):
        pass

    def add_user_group(self, user, group):
        pass

    def remove_user_group(self, user, group):
        pass

    #  Read-only

    def get_user_option(self, user, option):
        pass

    def user_has_permission(self, user, permission,
                            check_group=True, check_superadmin=True):
        pass

    # Group operations
    #  Modification

    def create_group(self, group):
        pass

    def remove_group(self, group):
        pass

    def set_group_option(self, group, option, value):
        pass

    def add_group_permission(self, group, permission):
        pass

    def remove_group_permission(self, group, permission):
        pass

    # Read-only

    def get_group_option(self, group, option):
        pass

    def group_has_permission(self, group, permission):
        pass
