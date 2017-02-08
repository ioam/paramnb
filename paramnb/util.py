import sys
from collections import OrderedDict

if sys.version_info.major == 3:
    unicode = str
    basestring = str

def named_objs(objlist):
    """
    Given a list of objects, returns a dictionary mapping from
    string name for the object to the object itself.
    """
    objs = OrderedDict()
    for k, obj in objlist:
        if hasattr(k, '__name__'):
            k = k.__name__
        elif sys.version_info < (3,0) and isinstance(k, basestring) and not isinstance(k, unicode):
            k = unicode(k.decode('utf-8'))
        else:
            k = unicode(k)
        objs[k] = obj
    return objs

