# coding=utf-8
import system.plugins.plugin
from system.decorators.log import deprecated_class

__author__ = "Gareth Coles"


@deprecated_class(
        hint_message="Use system.plugins.plugin.PluginObject instead"
)
class PluginObject(system.plugins.plugin.PluginObject):
    pass

__all__ = ["PluginObject"]
