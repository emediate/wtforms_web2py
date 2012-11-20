from wtforms import Form, validators, fields as f
from gluon import IS_IN_SET, IS_INT_IN_RANGE, IS_FLOAT_IN_RANGE
from fields import QuerySelectField


class ModelConverterBase(object):

    def __init__(self, converters):
        self.converters = converters

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

        if field.required:
            kwargs["validators"].append(validators.Required())
        else:
            kwargs["validators"].append(validators.Optional())
        # TODO: field.unique?

        if isinstance(field.requires, IS_IN_SET):
            return f.SelectField(choices=field.requires.options(), **kwargs)
        elif isinstance(field.requires, IS_INT_IN_RANGE):
            kwargs["validators"].append(validators.NumberRange(
                min=field.requires.minimum, max=field.requires.maximum - 1))
        elif isinstance(field.requires, IS_FLOAT_IN_RANGE):
            kwargs["validators"].append(validators.NumberRange(
                min=field.requires.minimum, max=field.requires.maximum))

        ftype = field.type
        if ftype in self.converters:
            return self.converters[ftype](model, field, kwargs)
        elif ftype.startswith("reference "):
            _, other_table_name = ftype.split()
            return self.conv_reference(model, field, kwargs, other_table_name)
        else:
            converter = getattr(self, "conv_%s" % ftype, None)
            if converter is not None:
                return converter(model, field, kwargs)


class ModelConverter(ModelConverterBase):

    def __init__(self):
        super(ModelConverter, self).__init__(converters={})

    def conv_id(self, model, field, kwargs):
        return f.IntegerField(**kwargs)

    def conv_integer(self, model, field, kwargs):
        return f.IntegerField(**kwargs)

    def conv_string(self, model, field, kwargs):
        kwargs["validators"].append(validators.Length(max=field.length))
        return f.TextField(**kwargs)

    def conv_boolean(self, model, field, kwargs):
        return f.BooleanField(**kwargs)

    def conv_reference(self, model, field, kwargs, other_table_name):
        from gluon import current
        db = current.globalenv["db"]
        other_table = getattr(db, other_table_name)
        return QuerySelectField(query=other_table, **kwargs)

# types:
# * id
# * date
# * datetime
# * text
# * ... and enough for now

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
    field_dict = model_fields(table, only, exclude, field_args, converter)
    return type(table._tablename.title() + "Form", (base_class,), field_dict)
