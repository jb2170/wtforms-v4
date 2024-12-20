from .legacyvalidators import *

from typing import Optional as TOptional
# once `Optional` validator has been dissolved this can be renamed TOptional -> Optional

from wtforms import Form, Field

# XXX NMD: Not My Docstring: Needs reviewing
# XXX DRD: Data or Raw Data, how much non-StringField do we need to consider

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

    def __call__(self, form: Form, field: Field):
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

class Length(Validator):
    """
    Validates the length of a string.

    :param min:
        The minimum required length of the string.
        If `-1`, then null data (`None`) passes the validator.
        If `0`, then null data (`None`) does not pass the validator,
        thus the string must exist, even if it's just the empty string
        (`''` of length 0).

    :param max:
        The maximum length of the string.
        If `-1`, then the maximum length will not be checked.
        The string can be up to *and including* `max` characters long.
        The length is calculated using Python's `len`, the number of Unicode
        codepoints in the string. This is different from length in encoded bytes,
        which for example with UTF-8 encoding can be up to four bytes per codepoint.

    :param message:
        Can be interpolated using `%(min)d` and `%(max)d` if desired.
        Useful defaults are provided depending on the existence of min and max.

    When supported, sets the `minlength` and `maxlength` attributes on widgets.
    """

    def __init__(self, min: int = -1, max: int = -1, error_message: TOptional[str] = None):
        super().__init__(error_message)
        if min == -1 and max == -1:
            # is this really necessary?
            raise AssertionError("At least one of `min` or `max` must be specified.")
        if max != -1 and not min <= max:
            raise AssertionError("`min` cannot be more than `max`.")

        self.min = min
        self.max = max

        self.field_flags = {}
        if self._is_checking_min:
            self.field_flags["minlength"] = self.min
        if self._is_checking_max:
            self.field_flags["maxlength"] = self.max

    @property
    def _is_checking_min(self) -> bool:
        return self.min != -1

    @property
    def _is_checking_max(self) -> bool:
        return self.max != -1

    def _formatted_error_message(self, form, field) -> str:
        if self.error_message is not None:
            message = self.error_message
        elif not self._is_checking_max:
            message = field.ngettext(
                "Field must be at least %(min)d character long.",
                "Field must be at least %(min)d characters long.",
                self.min
            )
        elif not self._is_checking_min:
            message = field.ngettext(
                "Field cannot be longer than %(max)d character.",
                "Field cannot be longer than %(max)d characters.",
                self.max
            )
        elif self.min == self.max:
            message = field.ngettext(
                "Field must be exactly %(max)d character long.",
                "Field must be exactly %(max)d characters long.",
                self.max
            )
        else:
            message = field.gettext(
                "Field must be between %(min)d and %(max)d characters long."
            )

        return message % {"min": self.min, "max": self.max}

    def __call__(self, form, field):
        super().__call__(form, field)
        if not field.raw_data:
            length = -1
            # neat: this style makes the `self._is_checking_min` in
            # `self._is_checking_min and not length >= self.min` redundant because
            # this style causes `not self._is_checking_min and not length >= self.min` to be always False
            # and thus can be `or`-ed with `self._is_checking_min and not length >= self.min`
            # to form simply `not length >= self.min`
        else:
            # XXX DRD
            length = len(field.raw_data[0])

        if not length >= self.min or (self._is_checking_max and not length <= self.max):
            self._stop_validation(self._formatted_error_message(form, field))
