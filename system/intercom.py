_intercom_plugins = {}
_intercom_funcs = {}

def _intercom_send(origin, destination, data):
    if destination in _intercom_funcs:
        return _intercom_funcs[destination](origin, data)
    return None

def _construct_func(origin):
    def send_func(self, destination, data):
        return _intercom_send(origin, destination, data)

    return send_func

def add_plugin(name, plugin):
    if hasattr(plugin, "intercom"):
        _intercom_plugins[name] = plugin
        _intercom_funcs[name] = plugin.intercom
        plugin.intercom_send = _construct_func(name)

def remove_plugin(name):
    if name in _intercom_funcs:
        del _intercom_funcs[name]
        del _intercom_plugins[name]