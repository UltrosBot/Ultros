# coding=utf-8
import system.plugins.plugin
from system.decorators.log import deprecated_class

__author__ = "Gareth Coles"


PluginObject = deprecated_class(
    hint_message="Use system.plugins.plugin.PluginObject instead"
)(system.plugins.plugin.PluginObject)

__all__ = ["PluginObject"]
