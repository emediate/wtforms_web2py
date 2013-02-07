# HACK! In local copy of wtforms.compat text_type redefined to be a subclass of
# unicode which tries hard not to raise Unicode(En|De)code errors.
import sys
from wtforms_web2py import compat
sys.modules['wtforms.compat'] = compat

# HACK! Monkeypatching to ensure web2py that WTForms' widgets are safe.
from wtforms.fields.core import Field
from wtforms.widgets.core import HTMLString
Field.xml = lambda self: Field.__html__(self).encode('utf-8')
HTMLString.xml = lambda self: HTMLString.__html__(self).encode('utf-8')
