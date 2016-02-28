# coding=utf-8
import nose.tools as nosetools

from json import loads
from system.json_encoder import dumps

__author__ = 'Gareth Coles'

"""
Tests for the custom JSON encoder with the __json__ magic method
"""


class JsonTestObject(object):
    x = 1
    y = 2
    z = 3

    def __json__(self):
        return {"x": self.x, "y": self.y, "z": self.z}


class test_json:
    """
    JSON  | Tests for the custom JSON encoder
    """

    def test_json_test_object(self):
        """
        JSON  | Test encoding a custom object
        """

        o = JsonTestObject()

        json_data = dumps(o)
        restructured = loads(json_data)

        nosetools.eq_(o.x, restructured["x"])
        nosetools.eq_(o.y, restructured["y"])
        nosetools.eq_(o.z, restructured["z"])
