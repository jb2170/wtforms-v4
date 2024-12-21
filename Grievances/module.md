At this point in the repo redevelopment, it seems like NumberRange should wish to inherit from FieldRequired, to check first that data is not `None`. However what if we wanted

[
    FieldOptional,
    NumberRange
]

For non-null data, NumberRange's FieldRequired unnecessarily re-checks for data existing, when FieldOptional has already ruled that out.

| URL encoded form data | `FieldOptional` | `FieldRequired` |
| -                     | -               | -               |
| 'decsc='              | TS              | FS              |
| 'description='        | T               | T               |
| 'description=%20'     | T               | T               |
| 'description=foo'     | T               | T               |

And chaining together n validators would call FieldRequired's check n times. Instead we just want to call FieldOptional once. For null data FieldOptional raises StopValidation immediately. We should want exactly one of FieldOptional or FieldRequired to be mandated by the Field itself, not by any validators.

Further, Input{Required,Optional} and Data{Required,Optional} are purely StringField validators. The reason we didn't realise this earlier, and grouped them with Field{Required,Optional} is because the form data comes in over a socket as bytes, then gets converted to string for convenience of programming in Python. Then we would think to check FieldRequired, then DataRequired, and convert the data say to an IntegerField. But really the IntegerField str->int conversion should've happened directly after the FieldRequired, with no unnecessary DataRequired.

So to recap: Field{Required,Optional} are not validators that should be inherited from by validators that go in the Field.validators list, but exactly one should be called by the Field class .validate method depending on a Field(field_required: bool = True) keyword argument. We go with True as the sane default, which WTForms doesn't use (XXX compatibility? XXX field_flags compatibility?).

Field{Required,Optional} -> DataTypeCast (which should raise FS on failure) -> Validators

I'll make validators into a submodule, with files based on type (and a common file, say for NoneOf)
