__author__ = 'Gareth Coles'


class Info(object):

    data = None

    core = None
    info = None

    def __init__(self, yaml_data):
        """

        :param yaml_data:
        :type yaml_data: dict
        :return:
        """

        self.data = yaml_data

        for key in yaml_data.keys():
            obj = yaml_data[key]

            if isinstance(obj, dict):
                setattr(self, key, Info(obj))
            else:
                setattr(self, key, obj)

        if self.core is not None:
            self.name = self.core.name
            self.module = self.core.module

        if hasattr(self.core, "dependencies"):
            self.dependencies = self.core.dependencies
        else:
            self.dependencies = []
