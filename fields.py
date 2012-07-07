from wtforms import (Form, SelectField, IntegerField, TextField, validators)
from wtforms.validators import Optional
from wtforms.widgets import Select
from wtforms.fields import SelectFieldBase


class MySelectField(SelectField):

    def __init__(self, label=None, validators=None, empty_label="----------",
                 **kwargs):
        if empty_label:
            kwargs["choices"] = (("__None", empty_label),) + tuple([ (unicode(c[0]), c[1]) for c in kwargs["choices"] ])
        super(MySelectField, self).__init__(label, validators, **kwargs)

    def process_data(self, value):
        import ipdb; ipdb.set_trace()
        if value is None:
            self.data = None
        else:
            try:
                self.data = self.coerce(value)
            except (ValueError, TypeError):
                self.data = None

    def process_formdata(self, valuelist):
        import ipdb; ipdb.set_trace()
        if valuelist and valuelist[0] == "__None":
            self.data = None
        else:
            super(MySelectField, self).process_formdata(valuelist)
