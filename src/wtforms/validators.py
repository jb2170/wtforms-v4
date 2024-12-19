from .legacyvalidators import *

from typing import Optional as TOptional
# once `Optional` validator has been dissolved this can be renamed TOptional -> Optional

# XXX NMD: Not My Docstring: Needs reviewing

class Validator:
    field_flags = {}

    def __init__(self, error_message: TOptional[str] = None):
        self.error_message = error_message

        # transform: bool = True,
        # validate: bool = True,

    # def transform(self, data):
    #     # validation and coercion in one class?
    #     return data

    # def _manipulate_field(self, field):
    #     # instead of field_flags?
    #     pass

    def __call__(self, form, field):
        """
        The heart of the validator

        Override this to perform validation here
        """
        pass

    def _stop_validation(self, default_message: TOptional[str] = None):
        if default_message is None:
            # stopping validation early eg InputOptional
            message = None
        elif self.error_message is not None:
            message = self.error_message
        else:
            message = default_message

        raise StopValidation(message)

class FieldRequired(Validator):
    # XXX should this one and its children be for StringField only?
    # It may make data vs raw_data[0] checks easier. We'll see.

    """
    Validates that the field exists, even if its data is empty

    eg in 'title=My%20Post&description=' both 'title' and 'description' exist,
    and thus pass this validator
    """

    # must not set field_flags["required"] to True, that is for InputRequired

    def __call__(self, form, field):
        super().__call__(form, field)
        if not field.raw_data:
            self._stop_validation('This field must exist.')

class InputRequired(FieldRequired):
    """
    XXX NMD: Unify with FieldRequired and DataRequired
    Validates that input was provided for this field.

    Note there is a distinction between this and DataRequired in that
    InputRequired looks that form-input data was provided, and DataRequired
    looks at the post-coercion data. This means that this validator only checks
    whether non-empty data was sent, not whether non-empty data was coerced
    from that data. Initially populated data is not considered sent.

    Sets the `required` attribute on widgets.
    """

    field_flags = {"required": True}

    def __call__(self, form, field):
        super().__call__(form, field)
        if not field.raw_data[0]:
            field.errors.clear() # XXX is this because other errors don't matter compared to this? if so also put this on FieldRequired
            self._stop_validation(field.gettext("This field is required."))

class DataRequired(InputRequired):
    """
    XXX NMD
    XXX Only StringField is implemented so far
    XXX DataRequired has a muddy history, truthy checking datatypes

    Checks the field's data is 'truthy' otherwise stops the validation chain.

    This validator checks that the ``data`` attribute on the field is a 'true'
    value (effectively, it does ``if field.data``.) Furthermore, if the data
    is a string type, a string containing only whitespace characters is
    considered false.

    If the data is empty, also removes prior errors (such as processing errors)
    from the field.

    **NOTE** this validator used to be called `Required` but the way it behaved
    (requiring coerced data, not input data) meant it functioned in a way
    which was not symmetric to the `Optional` validator and furthermore caused
    confusion with certain fields which coerced data to 'falsey' values like
    ``0``, ``Decimal(0)``, ``time(0)`` etc. Unless a very specific reason
    exists, we recommend using the :class:`InputRequired` instead.

    :param message:
        Error message to raise in case of a validation error.

    Sets the `required` attribute on widgets.
    """

    def __call__(self, form, field):
        super().__call__(form, field)
        if not isinstance(field.raw_data[0], str):
            raise NotImplementedError
            # if not field.data:
            #     self._stop_validation("Bruh moment")
        else:
            if not field.raw_data[0].strip():
                field.errors.clear() # XXX see InputRequired
                self._stop_validation(field.gettext("This field is required to be more than just whitespace."))
