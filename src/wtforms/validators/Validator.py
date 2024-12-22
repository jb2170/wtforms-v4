from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from wtforms.form import Form
    from wtforms.fields import Field

class Validator:
    field_flags = {}

    def __init__(self, error_message: Optional[str] = None):
        self.error_message = error_message

        # transform: bool = True,
        # validate: bool = True,

    # def transform(self, data):
    #     # validation and coercion in one class?
    #     return data

    # def _manipulate_field(self, field):
    #     # instead of field_flags?
    #     pass

    def __call__(self, form: "Form", field: "Field"):
        """
        The heart of the validator

        Override this to perform validation here
        """
        pass

    def _stop_validation(self, default_message: Optional[str] = None):
        if default_message is None:
            # stopping validation early eg InputOptional
            message = None
        elif self.error_message is not None:
            message = self.error_message
        else:
            message = default_message

        raise StopValidation(message)

class StopValidation(Exception):
    """
    Causes the validation chain to stop.

    If StopValidation is raised, no more validators in the validation chain are
    called. If raised with a message, the message will be added to the errors
    list.
    """

    # XXX message should be None instead of "" right?
    def __init__(self, message="", *args, **kwargs):
        Exception.__init__(self, message, *args, **kwargs)
