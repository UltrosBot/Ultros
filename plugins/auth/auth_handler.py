__author__ = 'Gareth Coles'

# Required: authorized(caller, source, protocol)

from utils.password import mkpasswd
import hashlib


class authHandler(object):

    def __init__(self, plugin, data, blacklist):
        self.data = data
        self.blacklist = blacklist
        self.plugin = plugin

        self.create_superadmin_account()
        self.create_blacklisted_passwords()

    def create_blacklisted_passwords(self):
        if not len(self.blacklist):
            # Top 20 passwords of 2013
            passwords = ["password", "123456", "12345678", "1234", "qwerty",
                         "12345", "dragon", "pussy", "baseball", "football",
                         "letmein", "monkey", "696969", "abc123", "mustang",
                         "michael", "shadow", "master", "jennifer", "111111"]

            with self.blacklist:
                self.blacklist["all"] = passwords
                self.blacklist["users"] = {}
                self.plugin.logger.info("Created password blacklist with the "
                                        "20 most popular passwords of 2013.")

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
                                    "superadmin account as the bundled "
                                    "permissions system isn't being used.")
            self.plugin.logger.warn("Please do this manually!")

    def hash(self, salt, password):
        return hashlib.sha512(salt + password).hexdigest()

    def reload(self):
        self.data.reload()

    def check_login(self, username, password):
        username = username.lower()
        with self.data:
            if username not in self.data:
                return False
            user_data = self.data[username]
        calculated = self.hash(user_data["salt"], password)
        real_hash = user_data["password"]

        if calculated == real_hash:
            return True
        return False

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

    def change_password(self, username, old, new):
        username = username.lower()
        with self.data:
            if username not in self.data:
                return False
            user_data = self.data[username]
            calculated = self.hash(user_data["salt"], old)
            real_hash = user_data["password"]
            if calculated != real_hash:
                return False

            salt = mkpasswd(64, 21, 22, 21)
            hashed = self.hash(salt, new)

            self.data[username]["password"] = hashed
            self.data[username]["salt"] = salt
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
        calculated = self.hash(user_data["salt"], password)
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

    def blacklist_password(self, password, username=None):
        with self.blacklist:
            password = password.lower()
            if username is None:
                if password not in self.blacklist["all"]:
                    self.blacklist["all"].append(password)
                    return True
                return False
            username = username.lower()
            if username not in self.blacklist["users"]:
                self.blacklist["users"][username] = [password]
                return True
            else:
                if password in self.blacklist["users"][username]:
                    return False
            self.blacklist["users"][username].append(password)
            return True

    def password_backlisted(self, password, username=None):
        password = password.lower()
        if password in self.blacklist["all"]:
            return True
        if username is None:
            return False
        username = username.lower()
        if username in self.blacklist["users"]:
            return password in self.blacklist["users"][username]
        return False
