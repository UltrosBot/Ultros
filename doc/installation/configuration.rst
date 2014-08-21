.. _configuration:

Configuration
=============

Ultros uses YAML for all its configuration files by default. While at least one of us feels that YAML is the
best format for the job, it's worth noting that the exceptions produced by the YAML parser can be cryptic
at best, so you should take note of the following guidelines.

* **You cannot use tabs in YAML files** - only spaces. It doesn't matter how many spaces you use, as long as you use
  the same number of spaces for all indentation in the same file.
* Take note of the layout of the example configuration files. For example, if you're adding elements to a list, you'll notice the
  example probably has "- " before the list entry, so you should probably do the same thing with your list entries.
* Everyone makes mistakes, and we're happy to help anyone having issues, but please take the time to check over your
  YAML files before asking us about bugs in the configuration handling. You can always use a linter_ to check your file over.

Main configuration
------------------

The main configuration deals with the plugins and protocols you want to use with your bot, as well as reconnection settings.
As mentioned, Ultros supports connecting to multiple protocols, multiple instances of the same protocol, and even multiple
connections to the same server.

The exerpts below are taken from the **config/settings.yml.example** file. If you need to redownload that file,
you can find it here: :download:`settings.yml.example <../../config/settings.yml.example>`

.. Protocols
.. literalinclude:: ../../config/settings.yml.example
    :language: yaml
    :linenos:
    :lines: 7-9

In this section, you simply list off the names of your protocols. These names are what you will refer to when you
modify other configuration files. We recommend a descriptive naming system, such as **<protocol>**-**<network>**.
The names you specify here must also exist in **config/protocols/<name>.yml**, which is where you configure the
protocol itself. See the sections below for more information on that.

.. Plugins
.. literalinclude:: ../../config/settings.yml.example
    :language: yaml
    :linenos:
    :lines: 17-21

In this section, you can list off the names of all of the plugins you want Ultros to load. The names here are specified
per-plugin, and you can usually find the names of the plugin in their documentation. If you can't, then you can also
edit the **plugins/<plugin>.plug** files; the name is also stored there.

The plugins that ship with Ultros are as follows:

* Auth
* Bridge
* Dialectizer
* Factoids
* URLs

.. Reconnections
.. literalinclude:: ../../config/settings.yml.example
    :language: yaml
    :linenos:
    :lines: 23-29

In this section, you specify how Ultros should behave when it loses connection or flat-out fails to connect. The options
are explained in the snippet above. You should note that the reconnection counters are not shared between protocols,
which means that they will reconnect independently of each other.

.. Metrics
.. literalinclude:: ../../config/settings.yml.example
    :language: yaml
    :linenos:
    :lines: 31-48

This final option is for configuring Ultros' basic metrics. If you don't like metrics and you haven't yet started your bot,
then set this to **off** and it will never contact the server.

* **on** - The bot will connect to the server, be assigned a UUID (if it doesn't have one already) and submit metrics every
  ten minutes. The only metrics we send to the server is a list of the types of protocols that are loaded, the currently enabled
  plugins, and which packages are installed.
* **off** - If the bot has already been assigned a UUID, it will contact the server once to clear its protocols, plugins and packages
  lists and to let it know that metrics will be disabled. After this is done, the bot won't contact the server again.
    * If the bot doesn't have a UUID, it won't contact the server.
* **destroy** - If you want your UUID to be unassigned and all of the bot's information to be removed from the server, you can set
  your metrics setting to **destroy**. This will tell the server to delete all its stored data on the current UUID, and will also
  delete the UUID that's stored locally.
    * If the bot doesn't have a UUID, it won't contact the server. Therefore, you don't need to change this to **off** when you've
      had the data removed.

If you want to look at the metrics, you can find them here: http://ultros.io/metrics

Protocols » All
---------------

As mentioned earlier, each protocol gets its own configuration file in **config/protocols/<name>.yml**. Each type of
protocol has its own configuration, and they can be fairly different, but there is one section that is common across
all protocols.

.. Common protocol configs

Example from an IRC protocol:

.. literalinclude:: ../../config/protocols/irc-esper.yml.example
    :language: yaml
    :linenos:
    :lines: 1-3

Example from a Mumble protocol:

.. literalinclude:: ../../config/protocols/mumble.yml.example
    :language: yaml
    :linenos:
    :lines: 1-3

This section must be present in all protocol configs.

* **protocol-type** is the type of protocol you're defining here. As of this document, the types are **irc** and **mumble**.
* **can-flood** lets you turn off flood-limiting for your protocol. Some plugins may also use this to limit their output.

    * On IRC, you will almost always want this set to **no**, unless your bot has operator status on the network.

Protocols » IRC
---------------

The IRC protocol configuration is split up into several sections. You'll need the main section above, with the type set to
**irc**.

.. Network section
.. literalinclude:: ../../config/protocols/irc-esper.yml.example
    :language: yaml
    :linenos:
    :lines: 5-9

.. Bind address
.. literalinclude:: ../../config/protocols/irc-esper.yml.example
    :language: yaml
    :linenos:
    :lines: 14

The **network** section above is where you define your connection information.

* **address** - The address of the server to connect to.
* **port** - The port to connect to. The default port for IRC is **6667** (**6697** if you're using SSL).
* **ssl** - Whether to use SSL or not. This requires that you installed OpenSSL, in the installation instructions.
* **password** - Server password. You won't need this unless you're connecting through a bouncer or a special server.
* **bindaddr** - If you have more than one networking interface, the one to use for the connection. If you don't know what this is,
  then simply leave it commented out, it's not that important.

.. Identity section
.. literalinclude:: ../../config/protocols/irc-esper.yml.example
    :language: yaml
    :linenos:
    :lines: 16-24

The **identity** section is where you set up the bot's identification and any authentication it needs.

* **nick** - The nickname to connect with.
* **authentication** - The type of authentication to use, if any. It can be one of the following:

    * **None** - No authentication.
    * **NickServ** - Use modern NickServ authentication, with a username and password.
    * **NS-old** - Use old-style NickServ authentication, with just a password. Your nick needs to be the username you're logging in with.
    * **Auth** - The authentication method used by QuakeNet.
    * **Password** - Standard password authentication.

* **auth_name** - The username to use for authentication, where applicable.
* **auth_pass** - The password to use for authentication, where applicable.
* **auth_target** - When you're using a form of NickServ auth above, this is the nickname NickServ is set to use. It's usually just **NickServ**.

.. Channels section
.. literalinclude:: ../../config/protocols/irc-esper.yml.example
    :language: yaml
    :linenos:
    :lines: 27-31

The **channels** section defines what channels to join when the bot has connected. It's a list of channels of the following format..

* **name** - The name of the channel to join. Be sure to wrap it in **\"**quotes**\"**, otherwise the leading **\#** will comment it out.
* **key** - The channel key, if there is one. You can leave this blank if there isn't one.
* **kick_rejoin** - Whether to rejoin when kicked. This is ignored if you set **kick_rejoin** to **yes** below.

.. Control chars
.. literalinclude:: ../../config/protocols/irc-esper.yml.example
    :language: yaml
    :linenos:
    :lines: 33

The **control_chars** option defines what needs to be at the start of a message for it to be used as a command.

* It defaults to **\".\"**.
* This doesn't have to just be one character - Additionally, you can use **{NICK}** if you want the bot's nick to be there.

.. Rate limiting
.. literalinclude:: ../../config/protocols/irc-esper.yml.example
    :language: yaml
    :linenos:
    :lines: 37-39

The **rate_limiting** section is for limiting the speed messages are sent at. This is important as most IRC networks will kill
the bot if it sends messages too fast.

* **enabled** - Unless your bot has operator status on the network, you'll want this set to **yes**.
* **line_delay** - How long (in seconds) to wait between messages. Defaults to **0.1** seconds.

.. Kick rejoin
.. literalinclude:: ../../config/protocols/irc-esper.yml.example
    :language: yaml
    :linenos:
    :lines: 48

The **kick_rejoin** option here overrides the channel-specific ones if you set it to **yes**. Set it to **no** if you want to
configure this for individual channels.

.. Rejoin delay
.. literalinclude:: ../../config/protocols/irc-esper.yml.example
    :language: yaml
    :linenos:
    :lines: 51

The **rejoin_delay** option simply specifies how long to wait before rejoining a channel the bot was kicked from, in seconds.

.. Perform
.. literalinclude:: ../../config/protocols/irc-esper.yml.example
    :language: yaml
    :linenos:
    :lines: 53-54

For **advanced users**, the **perform** section is a list of raw IRC messages to send to the server - after identifying, but
before joining channels. For example, to have the bot be invited to an invite-only channel, you could do something like::

    perform:
    - "PRIVMSG ChanServ :INVITE #staff"
    - "PRIVMSG ChanServ :INVITE #HERPDERP"

.. Join-on-invite
.. literalinclude:: ../../config/protocols/irc-esper.yml.example
    :language: yaml
    :linenos:
    :lines: 55

This section allows the bot to join channels automatically when someone on the network invites it. Note that turning this on
will mean that anyone can have your bot join any channels they can use /invite in, so be aware of that.

Protocols » Mumble
------------------

Undocumented right now, please read the config file.

.. Join-on-invite
.. literalinclude:: ../../config/protocols/mumble.yml.example
    :language: yaml
    :linenos:
    :lines: 1:21

.. Footnote links, etc

.. _linter: http://yamllint.com/