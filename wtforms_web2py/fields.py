from wtforms import (Form, SelectField, IntegerField, TextField, validators)
from wtforms.validators import Optional, ValidationError
from wtforms.widgets import Select
from wtforms.fields import SelectFieldBase


class QuerySelectField(SelectFieldBase):
    widget = Select()

    def __init__(self, label=None, validators=None, query=None, orderby=None,
                 get_pk=None, get_label=None, allow_blank=False, blank_text='',
                 **kwargs):
        super(QuerySelectField, self).__init__(label, validators, **kwargs)
        self.query = query
        self.orderby = orderby
        self.allow_blank = allow_blank
        self.blank_text = blank_text
        if get_pk is None:
            self.get_pk = lambda obj: obj.id
        else:
            self.get_pk = get_pk
        if get_label is None:
            self.get_label = lambda obj: obj.name
        else:
            self.get_label = get_label

    def _get_data(self):
        if self._formdata is not None:
            for pk, row in self._get_object_list():
                if pk == self._formdata:
                    self._set_data(pk)
                    break
        return self._data

    def _set_data(self, data):
        self._data = data
        self._formdata = None

    data = property(_get_data, _set_data)

    def _get_object_list(self):
        get_pk = self.get_pk
        from gluon import current
        db = current.globalenv["db"]
        return [(get_pk(row), row) for row in db(self.query).select(orderby=self.orderby)]

    def iter_choices(self):
        if self.allow_blank:
            yield ("__None", self.blank_text, self.data is None)
        for pk, row in self._get_object_list():
            yield (pk, self.get_label(row), pk == self.data)

    def process_formdata(self, valuelist):
        if valuelist:
            if valuelist[0] == "__None":
                self.data = None
            else:
                self._data = None
                self._formdata = int(valuelist[0])

    def pre_validate(self, form):
        if not self.allow_blank or self.data is not None:
            for pk, obj in self._get_object_list():
                if self.data == pk:
                    break
            else:
                raise ValidationError(self.gettext('Not a valid choice'))
