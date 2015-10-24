.. Ultros documentation on the URLs plugin.

Ultros - URLs plugin
====================

One of Ultros' most-used plugins is the URLs plugin. This plugin is in charge
of handling URLs (aka links) that are shared within any channels Ultros is a
part of. By default, all this plugin will do is attempt to find the page title
of a standard http or https URL, but other plugins (such as `URL-tools`_) may
add special handling for specific sites.

This plugin requires that the **Auth** plugin be loaded and available, and that
a permissions manager be set up.

Getting started
---------------

The first thing you'll want to do is head into **config/plugins** and copy
**urls.yml.example** to **urls.yml**. Open the file, and configure it to your
liking, following the guidelines below.


.. literalinclude:: ../../config/plugins/urls.yml.example
    :language: yaml
    :linenos:
    :lines: 1-2

This section is all about user-agent spoofing. Spoofing is necessary so that websites
respond to us as if we're a real web browser - Firefox by default. In this section, you
can set a different user-agent string for specific domains, or use the default one by
setting this to **False** - This is necessary for sites like Soundcloud, which use Javascript
to set the page title when a real browser is detected, but simply places it in the HTML otherwise.

----

.. literalinclude:: ../../config/plugins/urls.yml.example
    :language: yaml
    :linenos:
    :lines: 4-5

Further to this, you may set the default user-agent string to use for all websites that
haven't been placed in the spoofing setting above. The default is Firefox's user-agent string.

----

.. literalinclude:: ../../config/plugins/urls.yml.example
    :language: yaml
    :linenos:
    :lines: 15-41

This section is all about pre-handler redirects. To understand what this means, you should
understand that the URLs plugin works by registering handlers for different sites based on
various different criteria. Before those handlers are run, however, we can attempt to resolve
any redirects presented by URL shortening services and other sites.

* **max**: The maximum number of redirects to follow before giving up. Set this to a reasonably low amount.
* **domains**: A whitelist of domains to follow redirects for before handlers are run. Regular expressions are not used.

----

.. literalinclude:: ../../config/plugins/urls.yml.example
    :language: yaml
    :linenos:
    :lines: 43-44

For the default website handler only: The maximum length of a title to be sent to a chat network.
As the configuration states, note that this is the length of the title as shown on the page - the
actual message sent to the chat network will be slightly larger to accommodate the domain info.

----

.. literalinclude:: ../../config/plugins/urls.yml.example
    :language: yaml
    :linenos:
    :lines: 46

The blacklist is used to ignore different URls based on regular expressions. The full
URL will be tested against each regular expression in this list, and if one of them matches, will
be completely ignored by the plugin. For example, you may want to ignore **git.io** URLs if the
bot is in channels where those URLs are pasted a lot - such as by another bot.

If you don't understand regular expressions, we recommend the excellent
`Learn Regex the Hard Way`_ by Zed. A. Shaw - Although it only goes up to exercise 16,
it's a great place to start.

Please also note that when you're writing regular expressions in YAML, you should surround
them with 'single quotes', so that YAML will not try to directly handle any regex escapes
you use.

----

.. literalinclude:: ../../config/plugins/urls.yml.example
    :language: yaml
    :linenos:
    :lines: 55-56

For the URL shortening part of the plugin, this is the default handler to use. This plugin
only provides a TinyURL shortener by default, which is used whenever the shortener you set
here can't be found, but plugins such as `URL-tools`_ may add other shorteners, which
you may use here instead.

Note that this doesn't override the per-channel shorteners (which will be covered
later) unless they're missing.

----

.. literalinclude:: ../../config/plugins/urls.yml.example
    :language: yaml
    :linenos:
    :lines: 58-62

This section is all about languages. Some websites will look out for a header named
**Accept-Language** and try to serve their website using the specified language. You
may set the default language requested here, as well as specifying specific languages
for separate domains, if you so wish. This may be of particular interest to users that
aren't native English speakers.

----

.. literalinclude:: ../../config/plugins/urls.yml.example
    :language: yaml
    :linenos:
    :lines: 64-88

This rather large section is all about how we handle cookies. It's a little complicated,
but provides quite a lot of flexibility. This part of the plugin uses regular expressions.

* **enable**: Set this to False to completely disable cookie support for this plugin. Note that plugins that add handlers are free to ignore this setting.
* **cookies**: What to do with cookies, depending on how they're categorised.
    * **Categories**:
        * **group**: Domains that you've grouped together, as shown below.
        * **global**: Any domains that you haven't included in a group.
    * **Settings**:
        * **session**: Accept all cookies and hold onto them until the plugin is reloaded. Never save them to file.
        * **save**: Save all cookies to file.
        * **update**: Discard any new cookies, but update any others that already exist.
        * **discard**: Discard all cookies, don't save anything.
* **never**: Regular expressions for domains that should never have cookies stored for them
* **group**: Groups of domains that should share their cookies, but keep them separate from all other domains.
    * **example_group**: Set this to a name that you'll remember, as it's used as the name of the cookie jar.
        * All domains in this list should be proper regular expressions to match.

If you don't understand regular expressions, we recommend the excellent
`Learn Regex the Hard Way`_ by Zed. A. Shaw - Although it only goes up to exercise 16,
it's a great place to start.

Please also note that when you're writing regular expressions in YAML, you should surround
them with 'single quotes', so that YAML will not try to directly handle any regex escapes
you use.

----

.. literalinclude:: ../../config/plugins/urls.yml.example
    :language: yaml
    :linenos:
    :lines: 90-91

This section is about advanced connection settings. Right now it only contains one setting -
**max_read_size**. This setting is used when finding titles on pages - It will only read the
specified number of bytes before attempting to find the title. This prevents excessively large
pages or maliciously-crafted URLs from taking too long to parse or using up all of Ultros' memory.

We recommend you keep the default of **16384** bytes - or 16 KiB. Feel free to change this if
you know what you're doing.

----

.. literalinclude:: ../../config/plugins/urls.yml.example
    :language: yaml
    :linenos:
    :lines: 93

The last line in the file is the version of your configuration. Do not change this or you
will likely break your configuration as we start adding versions.

----

Once you're all set up and ready to go, don't forget to open **config/settings.yml** and add
**URLs** to your list of plugins!

Permissions and commands
------------------------

**Command: urls**

* **Permission**: *urls.manage*
* **Usage**: *urls <setting> <value>*
    * **Setting**: *set <on/off>* - Enable or disable handling URLs for the current channel
    * **Setting**: *shortener <name>* - Set which URL shortener to use for the current channel
    * Run this command without arguments for help text and a list of shorteners

----

**Command: shorten**

* **Permission**: *urls.shorten*
* **Usage**: *shorten [url]*
    * You may specify a URL to shorten, or omit it to use the last URL that was sent to the channel
    * This will use the channel's configured shortener, or the default shortener when that isn't configured, the shortener is missing, or the command is used in a private message

----

**Permission**: *urls.trigger*

* This is used to determine whether a user is allowed to trigger the URLs plugin with a URL
    * This is a default permission, but you may use it to deny access to specific users, channels or protocols if needed

Known extension plugins
-----------------------

* `URL-tools`_

.. Footnote links, etc

.. _URL-tools: https://github.com/UltrosBot/Ultros-contrib/tree/master/URL-tools
.. _Learn Regex the Hard Way: http://regex.learncodethehardway.org/book/

.. |br| raw:: html

   <br />
