from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from wtforms.form import Form
    from wtforms.fields import Field

from .Validator import Validator

class InputRequired(Validator):
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

    def __call__(self, form: "Form", field: "Field"):
        super().__call__(form, field)
        if not field.raw_data[0]:
            field.errors.clear() # XXX is this because other errors don't matter compared to this?
            self._stop_validation(field.gettext("This field is required."))

class DataRequired(Validator):
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

    field_flags = {"required": True}

    def __call__(self, form: "Form", field: "Field"):
        super().__call__(form, field)
        if not isinstance(field.data, str):
            raise NotImplementedError
            # if not field.data:
            #     self._stop_validation("Bruh moment")
        if not field.raw_data[0].strip():
            field.errors.clear() # XXX see InputRequired
            self._stop_validation(field.gettext("This field is required to be more than just whitespace."))

class InputOptional(Validator):
    """
    Extends `FieldOptional`'s behavior; also stops further validation if
    the field's form data is the empty string.
    """

    def __call__(self, form: "Form", field: "Field"):
        super().__call__(form, field)
        if not field.raw_data[0]:
            field.errors.clear()
            self._stop_validation()

class DataOptional(Validator):
    # inherit FieldOptional to skip checking raw_data[0] twice
    # XXX only implemented for string data so far

    """
    Extends `InputOptional`'s behavior; also stops further validation if
    the field's form data is just whitespace.
    """

    def __call__(self, form: "Form", field: "Field"):
        super().__call__(form, field)
        if not isinstance(field.data, str):
            raise NotImplementedError
        if not field.raw_data[0].strip():
            field.errors.clear()
            self._stop_validation()

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

    def __init__(self, min: int = -1, max: int = -1, error_message: Optional[str] = None):
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

    def __call__(self, form: "Form", field: "Field"):
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
