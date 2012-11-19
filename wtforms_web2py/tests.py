import sys

import unittest
from mock import Mock

from wtforms import (Form, SelectField, IntegerField, TextField, validators)
from wtforms.validators import Optional
from wtforms.widgets import Select
from wtforms.fields import SelectFieldBase
from wtforms.compat import text_type

from fields import MySelectField, QuerySelectField
from dal import model_form


class DummyPostData(dict):
    def getlist(self, key):
        return self[key]


class LazySelect(object):
    def __call__(self, field, **kwargs):
        return list((val, text_type(label), selected) for val, label, selected in field.iter_choices())


def contains_validator(field, v_type):
    for v in field.validators:
        if isinstance(v, v_type):
            return True
    return False


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
        self._saved_gluon = sys.modules.get('gluon')
        sys.modules['gluon'] = gluon

    def tearDown(self):
        if self._saved_gluon:
            sys.modules['gluon'] = self._saved_gluon
        else:
            del sys.modules['gluon']

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


class TestModelForm(unittest.TestCase):

    def setUp(self):
        from gluon import DAL, Field, IS_IN_SET
        self.dal = DAL(None)
        self.table = self.dal.define_table(
            "user",
            Field("name", label="The Name", required=True, length=20),
            Field("age", "integer", required=True, comment="User's age"),
            Field("eye_color"),
            Field("sex", requires=IS_IN_SET(("male", "female"), zero=None)),
            Field("get_spam_from_us", "boolean", default=True),
        )
        self.F = model_form(self.table, field_args={
            "sex": {"widget": LazySelect()}
        })
        self.form = self.F()

    def test_form_sanity(self):
        self.assertEqual(self.F.__name__, 'UserForm')
        # DAL().define_table() adds id field automagically, so there we have one
        # more field than in out delcaration.
        self.assertEqual(len([x for x in self.form]), 6)

    def test_label(self):
        self.assertEqual(self.form.name.label.text, "The Name")

    def test_description(self):
        self.assertEqual(self.form.age.description, "User's age")

    def test_max_length(self):
        self.assertTrue(contains_validator(self.form.name, validators.Length))
        self.assertFalse(contains_validator(self.form.age, validators.Length))

    def test_optional(self):
        self.assertTrue(contains_validator(self.form.eye_color, validators.Optional))
        self.assertFalse(contains_validator(self.form.name, validators.Optional))

    def test_required(self):
        self.assertFalse(contains_validator(self.form.eye_color, validators.Required))
        self.assertTrue(contains_validator(self.form.name, validators.Required))

    @unittest.skip("TODO")
    def test_foreign_keys(self):
        from gluon import Field
        another_table = self.dal.define_table(
            "profile",
            Field("user", "reference user"),
        )
        F = model_form(another_table)
        form = F()
        for x in form: print x

    def test_some_validators(self):
        pass

    def test_fields_with_options(self):
        self.assertEqual([('male', 'male', False), ('female', 'female', False)],
                         self.form.sex())

    def test_default(self):
        self.assertEqual(self.form.get_spam_from_us.data, True)


if __name__ == "__main__":
    unittest.main()
