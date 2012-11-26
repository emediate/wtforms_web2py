# HACK! Monkeypatching to ensure web2py that WTForms' widgets are safe.
from wtforms.fields.core import Field
from wtforms.widgets.core import HTMLString
Field.xml = Field.__html__
HTMLString.xml = HTMLString.__html__
