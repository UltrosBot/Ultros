Core » Auth
***********

.. role:: yaml(code)
   :language: yaml

+----------------------+-------------------+----------------------------------------------------------------------+
| Obtaining            | Full name         | Description                                                          |
+======================+===================+======================================================================+
| Included with Ultros | **Auth**          | Adds a full permissions and authentication system. **This is**  |br| |
|                      |                   | **required for most plugins to function.**                           |
+----------------------+-------------------+----------------------------------------------------------------------+

The Auth plugin provides two very important things.

* A user registration system with securely salted and hashed passwords
* A pretty granular permissions system for use with other plugins

The Auth plugin is **required** for most plugins to function. If you don't use it, you'll see lots of errors. The
only reason we decided to make this functionality a plugin is so that other developers can create alternative systems
for handling permissions and user authentication.

Setting up
==========

.. highlight:: yaml
   :linenothreshold: 1

The Auth plugin comes as standard with Ultros. Simply add **Auth** to your **settings.yml** file, under the **plugins**
section. ::

    plugins:
      - Auth

Once you've done that, copy **config/plugins/auth.yml.example** to **config/plugins/auth.yml** and edit to
configure the plugin.

.. Auth config
.. literalinclude:: ../../config/plugins/auth.yml.example
    :language: yaml
    :linenos:

Permissions?
============

You may be asking yourself: "What are permissions and why do I need them?", "Can't it just use IRC/Mumble ranks?",
"Where are my pants?" - While some people feel like a full permissions system is a bit overkill (and we can understand
why they might), we feel like it provides a much greater level of control over who can do what.

Still with us? Great, let's get stuck in! Your permission file is named **permissions.yml** and can be found in **data/plugins/auth/**.

Here's an example permissions file, which uses all the features of the permissions system. ::

    groups:
        default:
            permissions:
                - auth.login
                - auth.logout
                - auth.register
                - auth.passwd
                - bridge.relay
                - urls.shorten
                - urls.title
                - drunkoctopus.drink
                - drunkoctopus.drunkenness
                - lastfm.nowplaying
                - lastfm.lastfmnick
                - money.main
                - geoip.command
                - urbandictionary.definition
                - wordnik.dict
                - wordnik.wotd
                - urls.shorten
                - items.give
                - items.get
                - wolfram.wolfram
                - money.main
                - factoids.get.*
                - aoshelper.playercount
                - aoshelper.aostoip
                - aoshelper.iptoaos
                - russianroulette.rroulette
                - jargon.jargon
                - 8ball.8ball
            protocols:
                irc-fraction:
                    permissions:
                        - hb.hb
                mumble-fraction:
                    permissions:
                        - hb.hb
        untrusted:
            inherit: default
            permissions:
                - ^aoshelper.*
                - ^factoids.*
                - ^auth.register
                - ^auth.passwd
                - ^drunkoctopus.*
        trusted:
            inherit: default
            permissions:
                - brainfuck.exec
                - minecraft.query
                - drunkoctopus.drink
                - drunkoctopus.drunkenness
                - factoids.add.channel
                - factoids.set.channel
                - factoids.delete.channel
        trusted-plus:
            inherit: trusted
            permissions:
                - factoids.add.protocol
                - factoids.set.protocol
                - factoids.delete.protocol
                - dialectizer.set
                - hb.hb
        admin:
            inherit: trusted-plus
            permissions:
                - web.admin
                - urls.manage
                - control.join
                - control.leave
                - control.say
                - control.action
                - factoids.set.*
                - factoids.add.*
                - factoids.delete.*
        super-admin:
            inherit: admin
            permissions:
                - control.raw
    users:
        g:
            group: trusted-plus
            options:
                superadmin: false
            permissions:
                - control.*
        rakiru:
            group: super-admin
            options:
                superadmin: true
            permissions: []

At first glance, this seems like quite a lot, so let's break it down into two sections - **groups** and **users**.

Permissions groups
------------------

Permissions groups are a convenient way to give a set of permissions to multiple users at once. They also allow you to
define specific permissions based on which protocol or channel a user is in when their permissions are checked.

The **default** group is what unregistered and newly registered users get checked against by default. Let me repeat that:
**every new user will have the permissions in this group**. Don't add any permissions you don't want **everyone** to have,
to this group.

With that in mind, let's look at the **default group** that is generated when you first run Ultros with this plugin
enabled. ::

    groups:
        default:
            options: {}
            permissions:
                - auth.login
                - auth.logout
                - auth.register
                - auth.passwd
                - bridge.relay
                - factoids.get.*
                - urls.shorten
                - urls.title

The first thing you'll notice in this file is the start of the **groups** section. We define every permissions group
in this section. Within this section, we have a section named **default** - this is the name of our group, and can be
pretty much anything textual, but you must always have a group named **default**.

Within the **default** group, there are a couple more sections.

* An **options** section. This is currently unused, but plugins are allowed to use this for whatever they like.
* A **permissions** section. This is where we list off each permission we'd like to give to this group.

    * Permissions support **unix shell pattern matching**. The following matchers are as follows:

        * Wildcard: :yaml:`"*"` - This matches any number of characters, and can match any character.

            * For example: :yaml:`"factoids.get.*"`

        * Singular wildcard: :yaml:`"?"` - This matches any character, but only one at a time.

            * For example: :yaml:`"factoids.get.???"`

        * Character groups: :yaml:`"[abc]"` - This matches any character that is within the brackets.

            * For example: :yaml:`"factoids.get.[abcdefghijklmnopqrstuvwxyz_-]"`

        * Negative character groups: :yaml:`"[!abc]"` - This matches any character that is **not** within the brackets.

            * For example: :yaml:`"factoids.get.[!1234567890]"`

        * Character literals: :yaml:`"[*]"` - For when you need to use special characters in your permissions.

            * For example: :yaml:`"factoids.get.[*?[]]"`

    * You can also specify **negative permissions nodes**, which will **deny** specific permissions already granted. They
      are always prefixed with the circumflex character, :yaml:`^`.

        * For example, if we specify :yaml:`"factoids.get.*"` but we don't want users to see a factoid named **admin**, we
          could then give them :yaml:`"^factoids.get.admin"`.
        * Negative permissions always take priority, even when talking about group inheritance. For that reason, you should
          be careful when designing your groups.

Groups also support a few more sections. Let's take a look at a more complicated default group. ::

    groups:
        default:
            permissions: [...] # Permissions from above
            protocols:
                irc-fraction:
                    permissions:
                        - hb.hb
                    sources:
                        "#fraction":
                            - brainfuck.exec
                        "#noheartbeat":
                            - ^hb.hb
                mumble-fraction:
                    permissions:
                    - hb.hb

The **protocols** section is where we begin to define protocols and channels for specific permissions. This lets us
be a lot more granular when specifying permissions.

* Within the **protocols** section should be sections named after your protocols. In this example, we have a section for the
  **irc-fraction** and **mumble-fraction** protocols. Within this section, we can have..

    * A **permissions** section, which works the same as the one described above.
    * A **sources** section, where we describe each channel or other source. This is a list of permissions, as described above.

So, for example..

* If I'm in the default group and in **#fraction** on **irc-fraction**, then I get both the :yaml:`hb.hb`
  and :yaml:`brainfuck.exec` permissions.
* If I'm not in **#fraction** but I'm on **irc-fraction** or **mumble-fraction**,
  then I'll only be given :yaml:`hb.hb`.
* If I'm in **#noheartbeat** on **irc-fraction**, then I won't get :yaml:`hb.hb`, as it's been denied to users
  in that channel.
* If I'm not on either of those protocols, then I won't get either of the aforementioned permissions - even
  if I'm in **#fraction** on **irc-esper**.

.. note:: These permissions depend on the source they're checked against. For example, if I'm in **#noheartbeat** on
          **irc-fraction** and I attempt to use the **hb** command in **#hb**, then I'll be allowed to use it - but I won't if
          I use it in **#noheartbeat**.

This method of defining permissions gives us an awful lot of control over who gets to do what, and where. You should
always take the time to go over this properly.

.. warning:: You should **never** give the :yaml:`"*"` node to someone directly. Only use it to specify sub-permissions,
             never give users every permission available in this way. If you really need this, you should use the **superadmin**
             option detailed below.

Permissions users
-----------------

So, you've made all your groups and assigned permissions to them, and everything's looking pretty spiffy - but wait,
how do you give admin to a user? The answer is using the **users** section. Let's take a look at the default users
section generated when you first run the bot with this plugin enabled. ::

    users:
        superadmin:
            group: default
            options:
                superadmin: true
            permissions: []

In this section, we can list off our registered users, assign them groups and even individual permissions as detailed
in the groups section. But wait, what's this **superadmin** user?

When you first ran the bot with this plugin enabled, you'll have seen a message that looks like this::

    11 May 2014 - 14:12:12 |                 Auth |     INFO | Generating a default auth account and password.
    11 May 2014 - 14:12:12 |                 Auth |     INFO | You will need to either use this to add permissions to your user account, or just create an account and edit the permissions file.
    11 May 2014 - 14:12:12 |                 Auth |     INFO | Remember to delete this account when you've created your own admin account!
    11 May 2014 - 14:12:12 |                 Auth |     INFO | ============================================
    11 May 2014 - 14:12:12 |                 Auth |     INFO | Super admin username: superadmin
    11 May 2014 - 14:12:12 |                 Auth |     INFO | Super admin password: 0rE8CpW37ihTA07xH5VURn1ixl65EDf8
    11 May 2014 - 14:12:12 |                 Auth |     INFO | ============================================

The **superadmin** account, by default, has access to everything and is granted every permission available, regardless
of groups and other settings. The first thing you should do is login to this account and change the randomly-generated
password.

.. warning:: We do **not** recommend using a superadmin account, or giving any account the **superadmin** option. It
             exists for those rare cases that you may really need it, but do not use it as an excuse to not fill out
             your permissions file properly. If you do give someone else a user or group like this, you **will** mess
             up and give them a permission you **did not want them to have**.

             You have been warned.

Other files
===========

The auth plugin uses a couple other files for storage of various things.

* **blacklist.yml** contains a set of blacklisted passwords. This is updated if a user attempts to register an account
  in a public place, such as a channel.
* **passwords.yml** contains securely salted and hashed passwords, one for each user that has registered themselves.
  You cannot reset passwords by editing this file, so don't even try.

    * You should delete the entry for **superadmin** from this file when you've finished setting up your own account
      and permissions.

Commands and permissions
========================

+-------------------+-------------------+-------------------------+---------------------------------------------------+
| Commmand          | Params            | Permission              | Description                                       |
+===================+===================+=========================+===================================================+
| .login            | **Username** |br| | auth.login              | Allows you to login with your registered account. |
|                   | **Password**      |                         |                                                   |
+-------------------+-------------------+-------------------------+---------------------------------------------------+
| .logout           |                   | auth.logout             | Allows you to logout when you've logged in.       |
+-------------------+-------------------+-------------------------+---------------------------------------------------+
| .passwd           | **Old pass** |br| | auth.passwd             | Lets you change your account password.            |
|                   | **New pass**      |                         |                                                   |
+-------------------+-------------------+-------------------------+---------------------------------------------------+
| .register         | **Username** |br| | auth.register           | Lets you register an account with the bot.        |
|                   | **Password**      |                         |                                                   |
+-------------------+-------------------+-------------------------+---------------------------------------------------+

.. Footnote links, etc

.. _site: http://ultros.io

.. |br| raw:: html

   <br />
