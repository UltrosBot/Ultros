__author__ = 'Gareth Coles'

# Required: authorized(caller, source, protocol)

from utils.password import mkpasswd
import hashlib


class authHandler(object):

    def __init__(self, plugin, data):
        self.data = data
        self.plugin = plugin

        self.create_superadmin_account()

    def create_superadmin_account(self):
        if len(self.data):
            if "superadmin" in self.data:
                self.plugin.logger.warn("Superadmin account exists!")
                self.plugin.logger.warn("You should remove this account "
                                        "as soon as possible!")
            return
        self.plugin.logger.info("Generating a default auth account and "
                                "password.")
        self.plugin.logger.info("You will need to either use this to add "
                                "permissions to your user account, or just "
                                "create an account and edit the permissions "
                                "file.")
        self.plugin.logger.info("Remember to delete this account when you've "
                                "created your own admin account!")

        password = mkpasswd(32, 11, 11, 10)

        self.create_user("superadmin", password)

        self.plugin.logger.info("============================================")
        self.plugin.logger.info("Super admin username: superadmin")
        self.plugin.logger.info("Super admin password: %s" % password)
        self.plugin.logger.info("============================================")

        p_handler = self.plugin.get_permissions_handler()

        if p_handler:
            if not p_handler.create_user("superadmin"):
                self.plugin.logger.warn("Unable to create permissions section "
                                        "for the superadmin account!")
            if not p_handler.set_user_option("superadmin", "superadmin", True):
                self.plugin.logger.warn("Unable to set 'superadmin' flag on "
                                        "the superadmin account!")
        else:
            self.plugin.logger.warn("Unable to set permissions for the "
                                    "superadmin account as the default "
                                    "permissions system isn't being used.")
            self.plugin.logger.warn("Please do this manually!")

    def hash(self, salt, password):
        return hashlib.sha512(salt + password).hexdigest()

    def reload(self):
        self.data.reload()

    def create_user(self, username, password):
        username = username.lower()

        with self.data:
            if username in self.data:
                return False

            salt = mkpasswd(64, 21, 22, 21)
            hashed = self.hash(salt, password)

            self.data[username] = {
                "password": hashed,
                "salt": salt
            }

        return True

    def delete_user(self, username):
        username = username.lower()
        with self.data:
            if username in self.data:
                del self.data[username]
                return True
        return False

    def login(self, user, protocol, username, password):
        username = username.lower()
        with self.data:
            if username not in self.data:
                return False
            user_data = self.data[username]
        calculated = self.hash(username, user_data["salt"])
        real_hash = user_data["password"]

        if calculated == real_hash:
            user.authorized = True
            user.auth_name = username
            return True
        return False

    def logout(self, user, protocol):
        if user.authorized:
            user.authorized = False
            del user.auth_name
            return True
        return False

    def authorized(self, caller, source, protocol):
        return caller.authorized

    def user_exists(self, username):
        username = username.lower()
        return username in self.data
