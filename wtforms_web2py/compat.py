class ForgivingUnicode(unicode):
    def __new__(cls, val, encoding='utf-8'):
        if isinstance(val, str):
            return super(ForgivingUnicode, cls).__new__(cls, val.decode(encoding))
        elif isinstance(val, unicode):
            return super(ForgivingUnicode, cls).__new__(cls, val)
        else:
            raise TypeError('Invalid argument for ForgivingUnicode: %r' % val)
    def __str__(self):
        return self.encode('utf-8')

text_type = ForgivingUnicode
string_types = basestring,
iteritems = lambda o: o.iteritems()
itervalues = lambda o: o.itervalues()
from itertools import izip

def with_metaclass(meta, base=object):
    return meta("NewBase", (base,), {})

