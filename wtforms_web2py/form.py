from wtforms import Form as WTForm


class Form(WTForm):

    @property
    def fields(self):
        for field in self:
            if field.widget.input_type != "hidden":
                yield field

    @property
    def hidden_fields(self):
        for field in self:
            if field.widget.input_type == "hidden":
                yield field
