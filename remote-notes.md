Notes for remote protocols
--------------------------

This has been something I've wanted to do for some time now. To briefly explain,
Ultros only supports Python and things that run on top of it - While we love
Python here, other people do not, and there are tools that are simply not
available or just not viable in Python that would add desirable things to
Ultros.

With that in mind, I decided that the best way around the problem was a protocol
system build around JSON sockets. I can't think of a language that doesn't
support this, so it seems to be a good fit.

The plan
--------

- [ ] Create a basic JSON LineReader
- [ ] Implement some kind of security
    - I'm thinking a key exchange might be the best way, using at least one 
      pre-shared key
- [ ] Produce a full set of objects and utils that allow existing plugins to 
      easily work with this system
    - Wrapper classes will obviously be a requirement here
    - Also worth remembering that Twisted is async, so we shouldn't have to wait 
      for data to be sent out
- [ ] Produce a set of tools or libraries for the following initial languages
    - Python
    - Node.JS

Spec
----

The spec is as of yet undecided, so here's some provisional information

* Key exchange
    * Ultros will generate a public and private key for each configured
      remote protocol
    * The user will copy this public key to the remote protocol via some 
      trusted method, which will then generate its own private and public key
        * There's no reason the remote protocol can't generate a new key each
          time, but this would be quite nonsensical in most cases
    * On first connect, the remote protocol will encrypt and send its public
      key to Ultros, which will be kept in memory for the duration of the
      connection
    * Now that the exchange is complete, communication can take place securely
* JSON protocol
    * The structure of this hasn't been decided, but all messages will be JSON
      objects, followed by a newline or `\n`, used as a separator between 
      messages
* Capabilities
    * It is intended that remote protocols should have access to as many Ultros
      services and capabilities as possible. To that end, the first set of
      capabilities I'll be targeting are as follows:
        * Commands
            * Registration, handling and management
        * Events
            * Both firing and listening
            * Event cancellation is not planned for the initial release
        * Plugins
            * Both management and registration
        * Protocols
            * Both management and registration
            * Including users, channels and the protocol objects themselves
    * Inter-plugin communication is not planned for the initial release
    * All of the above will require a lot of abstraction, and we will therefore
      need the following:
        * A way to convert Ultros types to JSON, including function lists for
          remote calling
        * A way to convert JSON back to Ultros types, which may or may not need
          to refer to existing objects instead of simply creating a new object

---

There's a lot of work involved with this. While I'm okay with working on this in
my spare time, any help from interested users would be appreciated.
