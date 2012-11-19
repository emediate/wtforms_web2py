import sys

import unittest
from mock import Mock

from wtforms import (Form, SelectField, IntegerField, TextField, validators)
from wtforms.validators import Optional
from wtforms.widgets import Select
from wtforms.fields import SelectFieldBase
from wtforms.compat import text_type

from fields import MySelectField, QuerySelectField


class DummyPostData(dict):
    def getlist(self, key):
        return self[key]


class LazySelect(object):
    def __call__(self, field, **kwargs):
        return list((val, text_type(label), selected) for val, label, selected in field.iter_choices())


CHOICES = (
    (1, "one"),
    (2, "two"),
    (3, "three"),
)


class MyForm(Form):
    select = MySelectField("label", [Optional()], choices=CHOICES)

class TestMySelectField(unittest.TestCase):

    def ttest_with_empty_formdata(self):
        form = MyForm()
        assert form.validate
        assert form.data["select"] == None

    def ttest_empty_choice(self):
        data = DummyPostData({
            "select": "__None",
        })
        form = MyForm(data)
        if form.validate():
            print "valid", form.data
        else:
            print "invaid", form.errors


class QuerySelectFieldTest(unittest.TestCase):

    def setUp(self):
        def make_row(id, name):
            # Mocks has special handling for name attribute: Mock.name returns
            # something like `<Mock name='name with pass as a argument' id=[id of this mock]>`
            # id(mock) is different each time, so we have to reassign it there.
            row = Mock(id=id)
            del row.name
            row.name = name
            return row
        objects = (make_row(id=1, name="First"), make_row(id=2, name="Second"))
        # mocking all the web2py stuff
        self.db_set = Mock(**{"select.return_value": objects})
        self.db = Mock(return_value=self.db_set)
        gluon = Mock(current=Mock(globalenv={"db": self.db}))
        sys.modules['gluon'] = gluon

    def test_field_outputs_whatever_it_should(self):
        query = object()
        class F(Form):
            qsf = QuerySelectField(query=query, widget=LazySelect())
        form = F()
        self.assertEqual([(1, u'First', False), (2, u'Second', False)],
                         form.qsf())

    def test_field_calls_dal_with_right_stuff(self):
        query = object()
        orderby = object()
        class F(Form):
            qsf = QuerySelectField(query=query, orderby=orderby,
                                   widget=LazySelect())
        form = F()
        form.qsf()
        self.db.assert_called_with(query)
        self.db_set.select.assert_called_with(orderby=orderby)



if __name__ == "__main__":
    unittest.main()
