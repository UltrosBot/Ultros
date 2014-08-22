# coding=utf-8

"""
Module containing classes for all the default and base events.

Evemts are Ultros' way of connecting different parts of the code. Something
happens, so some code is called, and something else happens, and so on. Events
can be called from anywhere - a plugin, a protocol, or even some internal
class.

* Plugins should subclass `PluginEvent` in their event classes.
* Protocols get to use `BaseEvent` but should use it to create their own base
    events. For example, `IRCEvent` and `MumbleEvent`.
"""
