import unittest

from wtforms import (Form, SelectField, IntegerField, TextField, validators)
from wtforms.validators import Optional
from wtforms.widgets import Select
from wtforms.fields import SelectFieldBase

from fields import MySelectField


class DummyPostData(dict):
    def getlist(self, key):
        return self[key]


CHOICES = (
    (1, "one"),
    (2, "two"),
    (3, "three"),
)


class MyForm(Form):
    select = MySelectField("label", [Optional()], choices=CHOICES)

class TestMySelectField(unittest.TestCase):

    def test_with_empty_formdata(self):
        form = MyForm()
        assert form.validate
        assert form.data["select"] == None

    def test_empty_choice(self):
        data = DummyPostData({
            "select": "__None",
        })
        form = MyForm(data)
        if form.validate():
            print "valid", form.data
        else:
            print "invaid", form.errors


if __name__ == "__main__":
    unittest.main()
