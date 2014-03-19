.. _configuration:

Configuration
=============

Ultros uses YAML for all its configuration files by default. While at least one of us feels that YAML is the
best format for the job, it's worth noting that the exceptions produced by the YAML parser can be cryptic
at best, so you should take note of the following guidelines.

* **You cannot use tabs in YAML files** - only spaces. It doesn't matter how many spaces you use, as long as you use
  the same number of tabs for all indentation in the same file.
* Take note of the layout of the example configuration files. For example, if you're adding elements to a list, you'll notice the
  example probably has "- " before the list entry, so you should probably do the same thing with your list entries.
* Everyone makes mistakes, and we're happy to help anyone having issues, but please take the time to check over your
  YAML files before asking us about bugs in the configuration handling. You can always use a linter_ to check your file over.

Main configuration
------------------

The main configuration deals with the plugins and protocols you want to use with your bot, as well as reconnection settings.
As mentioned, Ultros supports connecting to multiple protocols, multiple instances of the same protocol, and even multiple
connections to the same server.

You define the names of your protocols here.

.. literalinclude:: ../../config/settings.yml.example
    :language: yaml
    :linenos:

.. Footnote links, etc

.. _linter: http://yamllint.com/