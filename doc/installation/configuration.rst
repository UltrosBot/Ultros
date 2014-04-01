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
Don't forget that you should only use characters here that can be used in filenames!

.. Plugins
.. literalinclude:: ../../config/settings.yml.example
    :language: yaml
    :linenos:
    :lines: 22-26

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
    :lines: 28-

In this section, you specify how Ultros should behave when it loses connection or flat-out fails to connect. The options
are explained in the snippet above. You should note that the reconnection counters are not shared between protocols,
which means that they will reconnect independantly of each other.

.. Footnote links, etc

.. _linter: http://yamllint.com/