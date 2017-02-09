import sys
from collections import OrderedDict

if sys.version_info.major == 3:
    unicode = str
    basestring = str


def as_unicode(obj):
    """
    Safely casts any object to unicode including regular string
    (i.e. bytes) types in python 2.
    """
    if sys.version_info.major < 3 and isinstance(obj, str):
        obj = unicode(obj.decode('utf-8'))
    else:
        obj = unicode(obj)
    return obj


def named_objs(objlist):
    """
    Given a list of objects, returns a dictionary mapping from
    string name for the object to the object itself.
    """
    objs = OrderedDict()
    for k, obj in objlist:
        if hasattr(k, '__name__'):
            k = k.__name__
        else:
            k = as_unicode(k)
        objs[k] = obj
    return objs
