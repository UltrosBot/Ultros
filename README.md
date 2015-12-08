![Ultros hugging Ultros, as interpreted by rakiru](https://dl.dropboxusercontent.com/u/7298729/drawings/ultros-christmas.png)

### The only squid that connects communities

[![Code Health](https://landscape.io/github/UltrosBot/Ultros/master/landscape.png)](https://landscape.io/github/UltrosBot/Ultros/master)

Builds: [On Bamboo](http://bamboo.gserv.me/browse/ULTROS-MAIN/latest)

-------------------

<sub>(I've seen enough hentai...)</sub>

Ultros is an IRC/Mumble/etc. bot, extensible to pretty much any protocol, with a full-featured plugin system.
For more information, see the [site](http://ultros.io) and [documentation (beta)](http://docs.ultros.io).

-------------------

IRC: [irc://irc.esper.net/Ultros](irc://irc.esper.net/Ultros) ([webchat](https://webchat.esper.net/?nick=&channels=Ultros))

Site (Currently under development): [ultros.io](https://ultros.io)

Documentation: [ReadTheDocs (beta)](http://docs.ultros.io)

API docs: [here](http://apidocs.ultros.io)

-------------------

This project uses some libraries that are not available through pip. They are automatically downloaded at
runtime, and are listed below for completeness and attribution purposes.

* [SocksiPy](http://socksipy-branch.googlecode.com)
    * This is used for various proxy-related tasks
    * License: The new BSD license
    * Dan Haim and the forked branch maintainers
* [SocksiPyHandler](https://gist.github.com/e000/869791)
    * This allows us to use urllib2 via a proxy without monkey-patching everything
    * License: Gist, no license specified in the file
    * [e000](https://github.com/e000) (e **at** tr0ll **dot** in)

We attempt to download the libraries instead of distributing them directly as it allows us to use them
without violating their license terms, as our project is licensed using a different open-source license.
