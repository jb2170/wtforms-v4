from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from wtforms.form import Form
    from wtforms.fields import Field

from .Validator import Validator

class FieldRequired(Validator):
    # XXX should this one and its children be for StringField only?
    # It may make data vs raw_data[0] checks easier. We'll see.

    """
    Validates that the field exists, even if its data is empty

    eg in 'title=My%20Post&description=' both 'title' and 'description' exist,
    and thus pass this validator
    """

    # must not set field_flags["required"] to True, that is for InputRequired

    def __call__(self, form: "Form", field: "Field"):
        super().__call__(form, field)
        if not field.raw_data:
            field.errors.clear()
            self._stop_validation('This field must exist.')

class FieldOptional(Validator):
    """
    Allows missing field; stops further validation if the field does not exist in the form data.

    Removes prior errors (such as processing errors) in that case.

    Sets the `optional` attribute on widgets.
    """

    field_flags = {"optional": True}

    def __init__(self):
        super().__init__(error_message = None)

    def __call__(self, form: "Form", field: "Field"):
        super().__call__(form, field)
        if not field.raw_data:
            field.errors.clear()
            self._stop_validation()
