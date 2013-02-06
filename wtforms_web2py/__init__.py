# HACK! Monkeypatching to ensure web2py that WTForms' widgets are safe.
from wtforms.fields.core import Field
from wtforms.widgets.core import HTMLString
Field.xml = lambda self: Field.__html__(self).encode('utf-8')
HTMLString.xml = lambda self: HTMLString.__html__(self).encode('utf-8')
