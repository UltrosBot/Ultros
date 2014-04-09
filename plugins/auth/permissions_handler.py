__author__ = 'Gareth Coles'

# Required: check(permission, caller, source, protocol)

import fnmatch
from system.protocols.generic.user import User


class permissionsHandler(object):

    def __init__(self, plugin, data):
        self.data = data
        self.plugin = plugin

        with self.data:
            if "users" not in self.data:
                self.data["users"] = {}
            if "groups" not in self.data:
                self.data["groups"] = {}

        if not len(self.data["groups"]):
            self.create_group("default")
            self.add_group_permissions("default",
                                       ["auth.login",
                                        "auth.logout",
                                        "auth.register",
                                        "auth.passwd",
                                        "bridge.relay",
                                        "factoids.get.*",
                                        "urls.shorten",
                                        "urls.title"])

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

        if isinstance(source, User):
            source = None
        elif isinstance(source, str):
            source = source.lower()
        else:
            source = source.name.lower()

        if isinstance(protocol, str):
            protocol = protocol.lower()
        else:
            protocol = protocol.name.lower()

        self.plugin.logger.info("CHECK | Permis: %s" % permission)
        self.plugin.logger.info("CHECK | Caller: %s" % caller)
        self.plugin.logger.info("CHECK | Source: %s" % source)
        self.plugin.logger.info("CHECK | Protoc: %s" % protocol)

        # TODO: Remove this hack now that we have inheritance
        if caller is None:
            self.plugin.logger.info("CHECK | Caller is None.")
            return self.group_has_permission("default", permission, protocol,
                                             source)

        if caller.authorized:
            self.plugin.logger.info("CHECK | Authorized: %s" %
                                     caller.authorized)
            username = caller.auth_name
            superuser = self.plugin.config["use-superuser"]
            return self.user_has_permission(username, permission,
                                            protocol, source,
                                            check_superadmin=superuser)
        else:
            self.plugin.logger.info("CHECK | Not authorized.")
            self.group_has_permission("default", permission, protocol,
                                      source)
        return False

    # User operations
    #  Modification

    def create_user(self, user):
        user = user.lower()

        with self.data:
            if user not in self.data["users"]:
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
            if user not in self.data["users"]:
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

    def add_user_permission(self, user, permission, protocol=None,
                            source=None):
        user = user.lower()
        permission = permission.lower()

        with self.data:
            if user in self.data["users"]:
                sauce = None
                if protocol:
                    result = False

                    protos = self.data["users"][user].get("protocol", {})

                    proto = protos.get(protocol, {})
                    pperms = proto.get("permissions", [])
                    sources = proto.get("sources", {})

                    if source:
                        sauce = sources.get(source, [])
                        if permission not in source:
                            sauce.append(permission)
                            result = True
                    elif permission not in pperms:
                        pperms.append(permission)
                        result = True

                    if sauce:
                        sources[source] = sauce

                    proto["sources"] = sources
                    proto["permissions"] = pperms
                    protos[protocol] = proto
                    self.data["users"][user]["protocols"] = protos

                    return result

                elif permission not in self.data["users"]["permissions"]:
                    self.data["users"]["permissions"].append(permission)
                    return True
        return False

    def remove_user_permission(self, user, permission, protocol=None,
                               source=None):
        user = user.lower()
        permission = permission.lower()

        with self.data:
            if user in self.data["users"]:
                sauce = None
                if protocol:
                    result = False

                    protos = self.data["users"][user].get("protocol", {})

                    proto = protos.get(protocol, {})
                    pperms = proto.get("permissions", [])
                    sources = proto.get("sources", {})

                    if source:
                        sauce = sources.get(source, [])
                        if permission in source:
                            sauce.remove(permission)
                            result = True
                    elif permission in pperms:
                        pperms.remove(permission)
                        result = True

                    if sauce:
                        sources[source] = sauce

                    proto["sources"] = sources
                    proto["permissions"] = pperms
                    protos[protocol] = proto
                    self.data["users"][user]["protocols"] = protos

                    return result

                elif permission not in self.data["users"]["permissions"]:
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
                            protocol=None, source=None,
                            check_group=True, check_superadmin=True):
        user = user.lower()
        permission = permission.lower()

        if user in self.data["users"]:
            if check_superadmin:
                superadmin = self.get_user_option(user, "superadmin")
                if superadmin:
                    return True

            user_perms = self.data["users"][user]["permissions"]

            _protos = self.data["users"][user].get("protocols", {})

            if protocol:
                _proto = _protos.get(protocol, {})
                user_perms = user_perms + _proto.get("permissions", [])

                _sources = _protos.get("sources", {})

                if source:
                    user_perms = user_perms + _sources.get(source, [])

            if self.compare_permissions(permission, user_perms):
                return True

            if check_group:
                user_group = self.data["users"][user]["group"]
                has_perm = self.group_has_permission(user_group, permission,
                                                     protocol, source)
                if has_perm:
                    return True
        return False

    # Group operations
    #  Modification

    def create_group(self, group):
        group = group.lower()

        with self.data:
            if group not in self.data["groups"]:
                new_group = {
                    "permissions": [],
                    "options": {},
                    "inherit": None
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

    def set_group_inheritance(self, group, inherit):
        group = group.lower()

        if isinstance(inherit, str):
            inherit = inherit.lower()
        elif inherit is not None:
            raise TypeError("Inheritance must either be a string or None")

        with self.data:
            if group in self.data["groups"]:
                self.data["groups"][group]["inherit"] = inherit
                return True
        return False

    def add_group_permission(self, group, permission, protocol=None,
                             source=None):
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

    def get_group_inheritance(self, group):
        group = group.lower()

        if group in self.data["groups"]:
            if "inherit" in self.data["groups"][group]:
                return self.data["groups"][group]["inherit"]
            return None
        return False

    def group_has_permission(self, group, permission,
                             protocol=None, source=None):
        group = group.lower()
        permission = permission.lower()

        groups = []
        all_perms = set()

        self.plugin.logger.debug("Checking group perms...")
        self.plugin.logger.debug("GROUP | %s" % group)
        self.plugin.logger.debug("PERMI | %s" % permission)
        self.plugin.logger.debug("SOURC | %s" % source)
        self.plugin.logger.debug("PROTO | %s" % protocol)

        def _recur(_group):
            if _group in self.data["groups"]:
                if _group not in groups:
                    groups.append(_group)
                    perms_list = self.data["groups"][_group]["permissions"]
                    all_perms.update(set(perms_list))

                    _protos = self.data["groups"][_group].get("protocols", {})

                    if protocol:
                        _proto = _protos.get(protocol, {})

                        all_perms.update(set(_proto.get("permissions", [])))

                        _sources = _proto.get("sources", {})

                        if source:
                            all_perms.update(set(_sources.get(source, [])))

                    inherit = self.get_group_inheritance(_group)
                    if inherit:
                        _recur(inherit)

        if group in self.data["groups"]:
            _recur(group)
            return self.compare_permissions(permission, list(all_perms))
        return False

    # Permissions comparisons
    def compare_permissions(self, perm, permissions, wildcard=True):
        perm = perm.lower()
        for element in permissions:
            if wildcard and fnmatch.fnmatch(perm, element.lower()):
                return True
            elif (not wildcard) and perm == element.lower():
                return True
        return False
