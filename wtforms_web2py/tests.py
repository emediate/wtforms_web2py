import sys
import unittest
from mock import Mock

from wtforms import Form, validators as v
from wtforms.compat import text_type

import gluon
from gluon import (DAL, Field, IS_EMPTY_OR, IS_IN_SET, IS_INT_IN_RANGE,
                   IS_IN_DB, IS_LIST_OF)

from fields import QuerySelectField
from dal import model_form, ModelConverter


class DummyPostData(dict):
    def getlist(self, key):
        return self[key]


class LazySelect(object):
    def __call__(self, field, **kwargs):
        return list((val, text_type(label), selected)
                    for val, label, selected in field.iter_choices())


def contains_validator(field, v_type):
    for v in field.validators:
        if isinstance(v, v_type):
            return True
    return False


def _make_row(id, name):
    # Mocks has special handling for name attribute: Mock.name returns
    # something like:
    # `<Mock name='name with pass as a argument' id=[id of this mock]>`
    # id(mock) is different each time, so we have to reassign it there.
    row = Mock(id=id)
    del row.name
    row.name = name
    return row


class BaseDALTest(unittest.TestCase):

    """
    Records what DAL should return for specific queries, and then in
    `.trearDown()` checks that it was really called with these queries::

        self.mock_db_query(query=query, response=whatever)

    It's also possible to additionally check other arguments of a call to DAL::

        self._db_call(query).select.assert_called_with(orderby=orderby)
    """

    def setUp(self):
        db = self.db = DAL(None)
        self._saved_current = gluon.current
        gluon.current = Mock(globalenv={"db": db})

    def mock_db_query(self, query, response):
        db_set = Mock(**{"select.return_value": response})
        self._check_query = query
        self._old_dal_call = self.db.__class__.__call__
        self._db_call = self.db.__class__.__call__ = \
                Mock(return_value=db_set)

    def tearDown(self):
        if getattr(self, "_check_query", False):
            self._db_call.assert_called_with(self._check_query)
        gluon.current = self._saved_current
        if getattr(self, "_old_dal_call", False):
            self.db.__class__.__call__ = self._old_dal_call


class QuerySelectFieldTest(BaseDALTest):

    def test_field_outputs_whatever_it_should(self):
        query = object()
        objects = (_make_row(id=1, name="First"),
                   _make_row(id=2, name="Second"))
        self.mock_db_query(query=query, response=objects)

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
        self.mock_db_query(query=query, response=[])
        form = F()
        form.qsf()
        self._db_call(query).select.assert_called_with(orderby=orderby)


class TestAllFieldTypes(BaseDALTest):

    def setUp(self):
        super(TestAllFieldTypes, self).setUp()
        self.table = self.db.define_table(
            "all_field_table",
            Field("string", "string"),
            Field("text", "text"),
            Field("boolean", "boolean"),
            Field("integer", "integer"),
            Field("double", "double"),
            Field("decimal", "decimal(3,4)"),
            Field("date", "date"),
            Field("time", "time"),
            Field("datetime", "datetime"),
        )
        F = model_form(self.table)
        self.form = F()

    def test_form_sanity(self):
        self.assertEqual(len([x for x in self.form]), 10)


class TestModelForm(BaseDALTest):

    def setUp(self):
        super(TestModelForm, self).setUp()
        self.table = self.db.define_table(
            "user",
            Field("name", label="The Name", required=True, length=20),
            Field("age", "integer", required=True, comment="User's age",
                  requires=IS_INT_IN_RANGE(0, 100)),
            Field("eye_color"),
            Field("sex", requires=IS_EMPTY_OR(
                                  IS_IN_SET(("male", "female")))),
            Field("get_spam_from_us", "boolean", default=True),
        )
        self.F = model_form(self.table, field_args={
            "sex": {"widget": LazySelect()}
        })
        self.form = self.F()

    def test_form_sanity(self):
        self.assertEqual(self.F.__name__, 'UserForm')
        # DAL().define_table() adds id field automagically, so there we
        # have one more field than in out delcaration.
        self.assertEqual(len([x for x in self.form]), 6)

    def test_label(self):
        self.assertEqual(self.form.name.label.text, "The Name")

    def test_description(self):
        self.assertEqual(self.form.age.description, "User's age")

    def test_max_length(self):
        self.assertTrue(
            contains_validator(self.form.name, v.Length))
        self.assertFalse(
            contains_validator(self.form.age, v.Length))

    def test_optional(self):
        self.assertTrue(
            contains_validator(self.form.eye_color, v.Optional))
        self.assertFalse(
            contains_validator(self.form.name, v.Optional))

    def test_required(self):
        self.assertFalse(
            contains_validator(self.form.eye_color, v.Required))
        self.assertTrue(
            contains_validator(self.form.name, v.Required))

    def test_fields_with_options(self):
        self.assertEqual(
            [('', '', False), ('male', 'male', False), ('female', 'female', False)],
            self.form.sex())

    def test_default(self):
        self.assertEqual(self.form.get_spam_from_us.data, True)


class TestModelFormWithDb(BaseDALTest):

    def setUp(self):
        super(TestModelFormWithDb, self).setUp()
        self.user_table = self.db.define_table(
            "user", Field("name"),
        )
        self.profile_table = self.db.define_table(
            "profile", Field("user", "reference user"),
        )

        self.F = model_form(self.profile_table, field_args={
            "user": {"widget": LazySelect()}
        })
        self.form = self.F()

    def test_foreign_keys(self):
        objects = (_make_row(id=1, name="Vasya"),
                   _make_row(id=2, name="Petya"))
        self.mock_db_query(query=self.user_table,
                           response=objects)
        self.assertEqual(self.form.user(),
                         [(1, u'Vasya', False), (2, u'Petya', False)])


class TestValidators(unittest.TestCase):

    def setUp(self):
        self.converter = ModelConverter()

    def test_unwinding(self):
        validators = self.converter.unwind_requires([
            IS_LIST_OF(IS_EMPTY_OR(IS_INT_IN_RANGE(0, 100))),
            IS_IN_SET((1,2,3)),
        ])
        names = [v.__class__.__name__ for v in validators]
        self.assertEquals(names, ['IS_LIST_OF', 'IS_IN_SET', 'IS_EMPTY_OR', 'IS_INT_IN_RANGE'])

    def test_some_more_validators(self):
        validators, _ = self.converter.convert_requires(IS_INT_IN_RANGE(1, 100))
        self.assertIsInstance(validators[0], v.NumberRange)


if __name__ == "__main__":
    unittest.main()
