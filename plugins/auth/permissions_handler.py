"""Permissions handler. In charge of deciding who can do what.

If this is the permissions handler in use, you can get an instance of it from
the CommandManager - otherwise you'll have to get it from the plugin instance.

The permissions handler supports inheritance, patterns and other useful stuff.
If you want to write your own, be sure to implement all the documented methods.
"""

__author__ = 'Gareth Coles'

# Required: check(permission, caller, source, protocol)

import fnmatch
import re

from system.protocols.generic.user import User
from system.translations import Translations

from utils.misc import str_to_regex_flags as s2rf

_ = Translations().get()
__ = Translations().get_m()


class permissionsHandler(object):
    """Permissions handler class"""

    pattern = re.compile(r"/(.*)/(.*)")

    def __init__(self, plugin, data):
        """Initialize the permissions handler.

        This will also create a default group with some default permissions.
        """

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
        """Find permissions data for a given username.

        :param username: Username to check for
        :type username: str

        :return: The user's data, or None if it's not found
        :rtype: dict, None
        """

        username = username.lower()

        if username in self.data["users"]:
            return self.data["users"][username]
        return None

    def find_group(self, group):
        """Find permissions data for a given group.

        :param group: Group to check for
        :type group: str

        :return: The group's data, or None if it's not found
        :rtype: dict, None
        """

        group = group.lower()

        if group in self.data["groups"]:
            return self.data["groups"][group]
        return None

    def reload(self):
        """Performs a dumb reload of the data file."""

        return self.data.reload()

    def check(self, permission, caller, source, protocol):
        """Check whether someone has a specified permission.

        You can supply `source` and `protocol` as their relevant objects
        or simple strings - however, `caller` must be a User object, and
        `protocol` cannot be None.

        :param permission: The permission to check against
        :param caller: The User to check against
        :param source: The source to check against
        :param protocol: The protocol to check against

        :type permission: str
        :type caller: User
        :type source: User, Channel, str, None
        :type protocol: Protocol, str

        :return: Whether the user has the given permission in this context
        :rtype: bool
        """

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

        self.plugin.logger.debug(_("CHECK | Permis: %s") % permission)
        self.plugin.logger.debug(_("CHECK | Caller: %s") % caller)
        self.plugin.logger.debug(_("CHECK | Source: %s") % source)
        self.plugin.logger.debug(_("CHECK | Protoc: %s") % protocol)

        if caller.authorized:
            self.plugin.logger.debug(_("CHECK | Authorized: %s") %
                                     caller.authorized)
            username = caller.auth_name
            superuser = self.plugin.config["use-superuser"]
            return self.user_has_permission(username, permission,
                                            protocol, source,
                                            check_superadmin=superuser)
        else:
            self.plugin.logger.debug(_("CHECK | Not authorized."))
            return self.group_has_permission("default", permission, protocol,
                                             source)

    # User operations
    #  Modification

    def create_user(self, user):
        """Create an entry for a username in the permissions file.

        This will fail if the entry already exists. Entries will, by default,
        have users set to the `default` group, with no extra permissions and
        `superadmin` disabled.

        :param user: The username to create the entry for
        :type user: str

        :return: Whether the entry was created
        :rtype: bool
        """

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

                self.plugin.logger.debug(_("User created: %s") % user)

                return True
        return False

    def remove_user(self, user):
        """Remove the entry for a username in the permissions file.

        This will fail if the entry doesn't exist.

        :param user: The username to remove the entry for
        :type user: str

        :return: Whether the entry was removed
        :rtype: bool
        """

        user = user.lower()

        with self.data:
            if user not in self.data["users"]:
                return False
            del self.data["users"][user]
        return True

    def set_user_option(self, user, option, value):
        """Set an option for a user in the permissions file.

        Don't use this for plugin-specific data! This is for
        permissions-related stuff only. If you have plugins that need to share
        data, create an API in the plugins.

        This will fail if the user doesn't have an entry in the permissions
        file.

        Note, if the user already has the option set, it will be overwritten.

        :param user: The username to set the option for
        :param option: The option to set
        :param value: The value to set for the option

        :type user: str
        :type option: str
        :type value: object

        :return: Whether the option was set
        :rtype: bool
        """

        user = user.lower()
        option = option.lower()

        with self.data:
            if user in self.data["users"]:
                self.data["users"][user]["options"][option] = value
                self.plugin.logger.debug(_("Option %s set to %s for user %s.")
                                         % (option, value, user))

                return True
        return False

    def add_user_permission(self, user, permission, protocol=None,
                            source=None):
        """Add a permission to a user in the permissions file.

        This will fail if the user doesn't exist, or the permission
        is already set.

        You may optionally specify a protocol and source to match against. If
        you want to match a source, you must also specify a protocol.

        :param user: The username to set the permission for
        :param permission: The permission to set
        :param protocol: The protocol to set the permission for
        :param source: The source to set the permission for

        :type user: str
        :type permission: str
        :type protocol: str, None
        :type source: str, None

        :return: Whether the permission was set
        :rtype: bool
        """

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
        """Remove a permission from a user in the permissions file.

        This will fail if the user doesn't exist, or the permission
        isn't already set.

        You may optionally specify a protocol and source to match against. If
        you want to match a source, you must also specify a protocol.

        :param user: The username to remove the permission from
        :param permission: The permission to remove
        :param protocol: The protocol to remove the permission from
        :param source: The source to remove the permission from

        :type user: str
        :type permission: str
        :type protocol: str, None
        :type source: str, None

        :return: Whether the permission was removed
        :rtype: bool
        """

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
        """Set the group for a user.

        The user will inherit all the permissions from the group.

        This will fail if the user entry doesn't exist.

        :param user: The username to set the group for
        :param group: The group to set

        :type user: str
        :type group: str

        :return: Whether the group was set
        :rtype: bool
        """

        group = group.lower()
        user = user.lower()

        with self.data:
            if user in self.data["users"]:
                self.data["users"][user]["group"] = group
                return True
        return False

    #  Read-only

    def get_user_option(self, user, option):
        """Get the value of an option for a user.

        This will return None if the option isn't found, or False if the
        user doesn't have an entry.

        :param user: Username to check the option on
        :param option: Option to check for

        :type user: str
        :type option: str

        :return: The value, or False or None
        :rtype: object, None
        """
        #TODO: Saner returns

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
        """Check whether a user has a permission. Don't use this if you're
        doing real permissions work - use check() instead.

        :param user: Username to check against
        :param permission: Permissions to check for
        :param protocol: Protocol to check against
        :param source: Source to check against
        :param check_group: Whether to check group permissions
        :param check_superadmin: Whether to honor superadmin

        :type user: str
        :type permission: str
        :type protocol: str
        :type source: str
        :type check_group: bool
        :type check_superadmin: bool

        :return: Whether the user has the given permission
        :rtype: bool
        """

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
        """As with `create_user`, but for groups."""

        group = group.lower()

        with self.data:
            if group not in self.data["groups"]:
                new_group = {
                    "permissions": [],
                    "options": {}
                }
                self.data["groups"][group] = new_group
                return True
        return False

    def remove_group(self, group):
        """As with `remove_user`, but for groups."""

        group = group.lower()

        with self.data:
            if group in self.data["groups"]:
                del self.data["groups"][group]
                return True
        return False

    def set_group_option(self, group, option, value):
        """As with `set_user_option`, but for groups."""

        group = group.lower()
        option = option.lower()

        with self.data:
            if group in self.data["groups"]:
                self.data["groups"][group]["options"][option] = value
                return True
        return False

    def set_group_inheritance(self, group, inherit):
        """Set group inheritance for a certain group.

        Groups may inherit permissions from one other group - useful for
        granting different groups of permissions.

        This will fail if the group you're setting inheritance for doesn't
        exist.

        :param group: The group you're setting inheritance for
        :param inherit: The group to inherit from, or None to remove it

        :type group: str
        :type inherit: str, None

        :return: Whether tyhe inheritance was set
        :rtype: bool
        """

        group = group.lower()

        if isinstance(inherit, str):
            inherit = inherit.lower()
        elif inherit is not None:
            raise TypeError(_("Inheritance must either be a string or None"))

        with self.data:
            if group in self.data["groups"]:
                self.data["groups"][group]["inherit"] = inherit
                return True
        return False

    def add_group_permission(self, group, permission, protocol=None,
                             source=None):
        """As with `add_user_permission`, but for groups."""

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
        """Add a list of multiple permissions to a certain group.

        This simply maps the list over `add_group_permission` as a convenience.

        :param group: The group to add permissions to
        :param permissions: The permissions to add

        :type group: str
        :type permissions: list
        """

        for permission in permissions:
            self.add_group_permission(group, permission)

    def remove_group_permission(self, group, permission):
        """As with `remove_user_permission`, but for groups."""

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
        """As with `get_user_option`, but for groups."""

        group = group.lower()
        option = option.lower()

        if group in self.data["groups"]:
            if option in self.data["groups"][group]["options"]:
                return self.data["groups"][group]["options"][option]
            return None
        return False

    def get_group_inheritance(self, group):
        """Get the inheritance setting for a group.

        This will return False if the group doesn't exist, or None if
        inheritance isn't set.

        :param group: The group to get inheritance for
        :type group: str

        :return: The inheritance set for the group
        :rtype: str, bool, None
        """
        group = group.lower()

        if group in self.data["groups"]:
            if "inherit" in self.data["groups"][group]:
                return self.data["groups"][group]["inherit"]
            return None
        return False

    def group_has_permission(self, group, permission,
                             protocol=None, source=None):
        """As with `user_has_permission`, but for groups."""

        group = group.lower()
        permission = permission.lower()

        groups = []
        all_perms = set()

        self.plugin.logger.debug(_("Checking group perms..."))
        self.plugin.logger.debug(_("GROUP | %s") % group)
        self.plugin.logger.debug(_("PERMI | %s") % permission)
        self.plugin.logger.debug(_("SOURC | %s") % source)
        self.plugin.logger.debug(_("PROTO | %s") % protocol)

        def _recur(_group):
            if _group is None:
                self.plugin.logger.debug(_("Group is None."))
                return
            if _group in self.data["groups"]:
                if _group not in groups:
                    groups.append(_group)
                    perms_list = self.data["groups"][_group]["permissions"]
                    all_perms.update(set(perms_list))

                    _protos = self.data["groups"][_group].get("protocols", {})

                    if _protos is None:
                        self.plugin.logger.debug(_("Protocols are None."))
                        return

                    if protocol:
                        _proto = _protos.get(protocol, {})

                        all_perms.update(set(_proto.get("permissions", [])))

                        _sources = _proto.get("sources", {})

                        if _sources is None:
                            self.plugin.logger.debug(_("Sources are None."))
                            return

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
    def compare_permissions(self, perm, permissions, wildcard=True,
                            deny_nodes=True, regex=True):
        """Compare a set of permissions to see if they match a specific
        permission.

        This is used a lot internally, but you may find it useful as well.

        :param perm: The permissions to attempt to match
        :param permissions: A list of permission to match,
            including regex/wildcard permissions
        :param wildcard: Whether to handle wildcard permissions
        :param deny_nodes: Whether to handle denial/negative nodes
        :param regex: Whether to handle regex permissions

        :type perm: str
        :type permissions: list
        :type wildcard: bool
        :type deny_nodes: bool
        :type regex: bool

        :return: Whether the permission has been matched or not
        :rtype: bool
        """
        perm = perm.lower()

        grant = []
        deny = []
        for element in permissions:
            if element.startswith("^"):
                deny.append(element[1:])
            else:
                grant.append(element)

        if deny_nodes:
            for element in deny:
                result = False

                if regex:
                    result = self.pattern.match(element)

                    if result:
                        pattern, flags = result.groups()
                        if re.match(pattern, perm, s2rf(flags)):
                            return False
                if not result:
                    if wildcard and fnmatch.fnmatch(perm, element.lower()):
                        return False
                    elif (not wildcard) and perm == element.lower():
                        return False

        for element in grant:
            result = False

            if regex:
                result = self.pattern.match(element)

                if result:
                    pattern, flags = result.groups()
                    if re.match(pattern, perm, s2rf(flags)):
                        return True
            if not result:
                if wildcard and fnmatch.fnmatch(perm, element.lower()):
                    return True
                elif (not wildcard) and perm == element.lower():
                    return True

        return False
