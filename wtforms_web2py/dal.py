import re
from wtforms import validators as v, widgets, fields as wtforms_fields
from gluon import (IS_IN_SET, IS_INT_IN_RANGE, IS_FLOAT_IN_RANGE, IS_LENGTH,
                   IS_IN_DB, IS_NOT_EMPTY, IS_EMAIL)
from . import fields as web2py_wtforms_fields
from form import Form


class _FieldsProxy(object):

    def __init__(self, *objects):
        self.objects = objects

    def __getattr__(self, name):
        for obj in self.objects:
            try:
                return getattr(obj, name)
            except AttributeError:
                continue
        raise AttributeError("Can't find field %r." % name)


class FieldConverter(object):

    """
    Base class for field converters.

    Instance of field converter is capable of converting an instance of DAL
    field to an instance of WTForms field.
    """

    def __init__(self, model_converter):
        self.model_converter = model_converter

    def can_convert(self, field):
        raise NotImplementedError

    def convert(self, field, kwargs):
        '''
        Converts dal field to wtforms field.

        Args:
            * `field`: dal field;
            * kwargs: arguments for wtforms field constructor.
        '''
        raise NotImplementedError


class SimpleFieldConverter(FieldConverter):

    def __init__(self, model_converter, dal_field_name, wtforms_field_name):
        self.model_converter = model_converter
        self.dal_field_name = dal_field_name
        self.wtforms_field_name = wtforms_field_name

    def can_convert(self, field):
        return self.dal_field_name == field.type

    def convert(self, field, kwargs):
        return getattr(self.model_converter.fields, self.wtforms_field_name)(**kwargs)


class RegexFieldConverter(FieldConverter):

    def can_convert(self, field):
        return self.regex.match(field.type)


class ReferenceConverter(RegexFieldConverter):
    regex = re.compile(r"reference (?P<other_table_name>\w+)")

    def convert(self, field, kwargs):
        from gluon import current
        db = current.globalenv["db"]
        m = self.regex.match(field.type)
        other_table_name = m.groupdict()['other_table_name']
        other_table = getattr(db, other_table_name)
        return self.model_converter.fields.QuerySelectField(query=other_table, **kwargs)


class DecimalConverter(RegexFieldConverter):
    regex = re.compile(r"decimal\((?P<places>\d+),\s*(?P<rounding>\d+)\)")

    def convert(self, field, kwargs):
        m = self.regex.match(field.type)
        kwargs.update(m.groupdict())
        return self.model_converter.fields.DecimalField(**kwargs)


class IdConverter(FieldConverter):

    def can_convert(self, field):
        return field.type == 'id'

    def convert(self, field, kwargs):
        defaults = {
            "widget": widgets.HiddenInput()
        }
        defaults.update(kwargs)
        defaults["validators"].append(v.NumberRange(min=1))
        return self.model_converter.fields.IntegerField(**defaults)


class ModelConverter(object):

    DEFAULT_SIMPLE_CONVERSIONS = {
        "IntegerField": ["integer"],
        "BooleanField": ["boolean"],
        "DateField": ["date"],
        "DateTimeField": ["time", "datetime"],
        "FloatField": ["double"],
        "TextField": ["string"],
        "TextAreaField": ["text"],
    }
    DEFAULT_CONVERTERS = [DecimalConverter, IdConverter, ReferenceConverter]

    #: ``getattr(fields, field_name)`` should return field class.
    fields = _FieldsProxy(web2py_wtforms_fields, wtforms_fields)

    def __init__(self, converters=()):
        self.converters = list(converters)
        for field_type, dal_fields in self.DEFAULT_SIMPLE_CONVERSIONS.iteritems():
            for name in dal_fields:
                converter = SimpleFieldConverter(self, name, field_type)
                self.converters.append(converter)

        for cls in self.DEFAULT_CONVERTERS:
            self.converters.append(cls(self))

    def convert(self, model, field, field_args=None):
        kwargs = {
            "label": field.label,
            "description": field.comment,
            "validators": [],
            "filters": [],
            "default": field.default,
        }
        if field_args:
            kwargs.update(field_args)

        validators, choices, required = self.convert_requires(field.requires)
        kwargs["validators"].extend(validators)
        if choices:
            return self.fields.SelectField(choices=choices, **kwargs)

        if field.required or required:
            kwargs["validators"].append(v.Required())
        else:
            kwargs["validators"].append(v.Optional())
            # TODO: field.unique vs IS_EMPTY_OR vs IS_NOT_EMPTY ?

        for converter in self.converters:
            if converter.can_convert(field):
                return converter.convert(field, kwargs)

    def convert_requires(self, requires):
        validators = []
        choices = []
        required = False
        for w2p_validator in self.unwind_requires(requires):
            if isinstance(w2p_validator, IS_INT_IN_RANGE):
                validators.append(v.NumberRange(
                    min=w2p_validator.minimum, max=w2p_validator.maximum - 1))
            elif isinstance(w2p_validator, IS_FLOAT_IN_RANGE):
                validators.append(v.NumberRange(
                    min=w2p_validator.minimum, max=w2p_validator.maximum,))
            elif isinstance(w2p_validator, (IS_IN_SET, IS_IN_DB)):
                choices = w2p_validator.options()
            elif isinstance(w2p_validator, IS_LENGTH):
                validators.append(v.Length(
                    min=w2p_validator.minsize, max=w2p_validator.maxsize,
                    message=w2p_validator.error_message))
            elif isinstance(w2p_validator, IS_NOT_EMPTY):
                required = True
                validators.append(v.DataRequired(
                    message=w2p_validator.error_message))
            elif isinstance(w2p_validator, IS_EMAIL):
                validators.append(v.Email(message=w2p_validator.error_message))
        return validators, choices, required

    def unwind_requires(self, requires):
        """
        Unwinds `webpy_field.requires` into a flat list of validators.

        `requires` can be somewhat complex structure of validators:
        * it can be either a validator instance or a list of them;
        * IS_EMPTY_OR and IS_LIST_OF validators contain another validator inside
          them.
        """
        if not isinstance(requires, (list, tuple)):
            requires = [requires]
        for w2p_validator in requires[:]:
            if hasattr(w2p_validator, "other"):
                requires.extend(self.unwind_requires(w2p_validator.other))
        return requires


def model_fields(model, only=None, exclude=None, field_args=None, converter=None):

    converter = converter or ModelConverter()
    field_args = field_args or {}
    model_fields = [ (name, getattr(model, name)) for name in model.fields ]

    if only:
        model_fields = (x for x in model_fields if x[0] in only)
    elif exclude:
        model_fields = (x for x in model_fields if x[0] not in exclude)

    field_dict = {}
    for name, model_field in model_fields:
        field = converter.convert(model, model_field, field_args.get(name))
        if field is not None:
            field_dict[name] = field

    return field_dict


def model_form(table, base_class=Form, only=None, exclude=None, field_args=None,
               converter=None):
    """
    Make a WTForms form from DAL `table`.

    Args:
        * base_class: base class for the new form, ``wtforms.Form`` by default.
        * only: list of fields to include into the new form.
        * exclude: list of fields to exclude from the new form.
        * field_args: field_name -> kwargs dict mapping.
        * converter: instance of model converter.  Converter must have method
                     `convert(table, field, field_kwargs)`.
    """
    field_dict = model_fields(table, only, exclude, field_args, converter)
    return type(table._tablename.title() + "Form", (base_class,), field_dict)
