from wtforms_web2py.utils import force_unicode

class ForgivingUnicode(unicode):
    def __new__(cls, val):
        unicoded_val = force_unicode(val, 'utf-8')
        return super(ForgivingUnicode, cls).__new__(cls, unicoded_val)
    def __str__(self):
        return self.encode('utf-8')

text_type = ForgivingUnicode
string_types = basestring,
iteritems = lambda o: o.iteritems()
itervalues = lambda o: o.itervalues()
from itertools import izip

def with_metaclass(meta, base=object):
    return meta("NewBase", (base,), {})
