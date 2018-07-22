# coding=utf-8
import json

__author__ = 'Gareth Coles'


class _Encoder(json.JSONEncoder):
    def default(self, o):
        if hasattr(o, "__json__"):
            return o.__json__()
        return json.JSONEncoder.default(self, o)


_our_encoder = _Encoder()


def dump(obj, fp, skipkeys=False, ensure_ascii=True, check_circular=True,
         allow_nan=True, cls=None, indent=None, separators=None,
         encoding='utf-8', default=None, sort_keys=False, **kw):
    return json.dump(obj, fp, skipkeys, ensure_ascii, check_circular,
                     allow_nan, _Encoder, indent, separators, encoding,
                     default, sort_keys, **kw)


def dumps(obj, skipkeys=False, ensure_ascii=True, check_circular=True,
          allow_nan=True, cls=None, indent=None, separators=None,
          encoding="utf-8", default=None, sort_keys=False, **kw):
    return json.dumps(obj, skipkeys, ensure_ascii, check_circular,
                      allow_nan, _Encoder, indent, separators, encoding,
                      default, sort_keys, **kw)


load = json.load
loads = json.loads
