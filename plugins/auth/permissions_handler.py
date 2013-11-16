__author__ = 'Gareth Coles'

# Required: check(permission, caller, source, protocol)


class permissionsHandler(object):

    def __init__(self, plugin, data):
        self.data = data
        self.plugin = plugin

        with self.data:
            if not "users" in self.data:
                self.data["users"] = {}
            if not "groups" in self.data:
                self.data["groups"] = {}

        if not len(self.data["groups"]):
            self.create_group("default")
            self.add_group_permissions("default",
                                       ["auth.login",
                                        "auth.logout",
                                        "bridge.relay"])

    def find_username(self, username):
        username = username.lower()

        if username in self.data["users"]:
            return self.data["users"][username]
        return None

    def find_group(self, group):
        group = group.lower()

        if group in self.data["groups"]:
            return self.data["groups"][group]
        return None

    def reload(self):
        return self.data.reload()

    def check(self, permission, caller, source, protocol):
        permission = permission.lower()

        if caller is None:
            return self.group_has_permission("default", permission)

        if caller.authorized:
            username = caller.auth_name
            superuser = self.plugin.config["use-superuser"]
            return self.user_has_permission(username, permission,
                                            check_superadmin=superuser)
        return False

    # User operations
    #  Modification

    def create_user(self, user):
        user = user.lower()

        with self.data:
            if not user in self.data["users"]:
                newuser = {
                    "group": "default",
                    "permissions": [],
                    "options": {
                        "superadmin": False
                    }
                }

                self.data["users"][user] = newuser

                self.plugin.logger.debug("User created: %s" % user)

                return True
        return False

    def remove_user(self, user):
        user = user.lower()

        with self.data:
            if not user in self.data["users"]:
                return False
            del self.data["users"][user]
        return True

    def set_user_option(self, user, option, value):
        user = user.lower()
        option = option.lower()

        with self.data:
            if user in self.data["users"]:
                self.plugin.logger.debug("User exists!")
                self.data["users"][user]["options"][option] = value
                self.plugin.logger.debug("Option %s set to %s for user %s."
                                         % (option, value, user))

                return True
        return False

    def add_user_permission(self, user, permission):
        user = user.lower()
        permission = permission.lower()

        with self.data:
            if user in self.data["users"]:
                if permission not in self.data["users"]["permissions"]:
                    self.data["users"]["permissions"].append(permission)
                    return True
        return False

    def remove_user_permission(self, user, permission):
        user = user.lower()
        permission = permission.lower()

        with self.data:
            if user in self.data["users"]:
                if permission not in self.data["users"]["permissions"]:
                    self.data["users"]["permissions"].remove(permission)
                    return True
        return False

    def set_user_group(self, user, group):
        group = group.lower()
        user = user.lower()

        with self.data:
            if user in self.data["users"]:
                self.data["users"][user]["group"] = group
                return True
        return False

    #  Read-only

    def get_user_option(self, user, option):
        user = user.lower()
        option = option.lower()

        if user in self.data["users"]:
            if option in self.data["users"][user]["options"]:
                return self.data["users"][user]["options"][option]
            return None
        return False

    def user_has_permission(self, user, permission,
                            check_group=True, check_superadmin=True):
        user = user.lower()
        permission = permission.lower()

        if user in self.data["users"]:
            if check_superadmin:
                superadmin = self.get_user_option(user, "superadmin")
                if superadmin:
                    return True

            user_perms = self.data["users"][user]["permissions"]
            if permission in user_perms:
                return True

            if check_group:
                user_group = self.data["users"][user]["group"]
                has_perm = self.group_has_permission(user_group, permission)
                if has_perm:
                    return True
        return False

    # Group operations
    #  Modification

    def create_group(self, group):
        group = group.lower()

        with self.data:
            if not group in self.data["groups"]:
                new_group = {
                    "permissions": [],
                    "options": {}
                }
                self.data["groups"][group] = new_group
                return True
        return False

    def remove_group(self, group):
        group = group.lower()

        with self.data:
            if group in self.data["groups"]:
                del self.data["groups"][group]
                return True
        return False

    def set_group_option(self, group, option, value):
        group = group.lower()
        option = option.lower()

        with self.data:
            if group in self.data["groups"]:
                self.data["groups"][group]["options"][option] = value
                return True
        return False

    def add_group_permission(self, group, permission):
        group = group.lower()
        permission = permission.lower()

        with self.data:
            if group in self.data["groups"]:
                if permission not in self.data["groups"][group]["permissions"]:
                    self.data["groups"][group]["permissions"]\
                        .append(permission)
                    return True
        return False

    def add_group_permissions(self, group, permissions):
        for permission in permissions:
            self.add_group_permission(group, permission)

    def remove_group_permission(self, group, permission):
        group = group.lower()
        permission = permission.lower()

        with self.data:
            if group in self.data["groups"]:
                if permission in self.data["groups"][group]["permissions"]:
                    self.data["groups"][group]["permissions"]\
                        .remove(permission)
                    return True
        return False

    # Read-only

    def get_group_option(self, group, option):
        group = group.lower()
        option = option.lower()

        if group in self.data["groups"]:
            if option in self.data["groups"][group]["options"]:
                return self.data["groups"][group]["options"][option]
            return None
        return False

    def group_has_permission(self, group, permission):
        group = group.lower()
        permission = permission.lower()

        if group in self.data["groups"]:
            if permission in self.data["groups"][group]["permissions"]:
                return True
        return False
