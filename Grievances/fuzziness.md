# Improved fuzziness of `Required` validators by adding `FieldRequired`

## Intro

I opened an issue #846 a few months back and solved it by reusing `NoneOf([None])`, but now I'm coming back to it and thinking I'm right, and there's an opportunity to clean up the validators in a more hierarchical way.

The `InputRequired` validator alone cannot permit enough fuzziness to distinguish between an empty string `''` being submitted, and the field not being present in the submitted form data.

For example: if a form for submitting a blogpost has a `description` field, which is permitted to be an empty string, we want to make sure that the user **did indeed send an empty string**, and that a non-empty string has not gone walkabout under the wrong field name of `desc`, or the user forgot that a `description` field existed in the first place, which they would've liked to have filled in.

The proposition is to add a validator called `FieldRequired` that checks for the presence of the field name in the form data, regardless of its value.

## Rationale

Observe that `FieldRequired` would fill in a gap in the fuzzy truth table below, with validators increasing in order of permissibility.

The following notation is used:

- `F` (False) denotes the input failing the validator
- `T` (True) denotes the input passing the validator
- `S` (StopValidation) denotes the validator raising `StopValidation`.
    - `FS` is raising `StopValidation` with an error string to abort further validation
    - `TS` is raising `StopValidation` without an error string to successfully end the validation chain early, skipping further validators

The following columns are added just for demonstrating the diagonal pattern that emerges in the tables. None of them are needed as validators.

- fail:     (why would one want validation to always fail?)
- return:   (just don't add any more validators beyond this point)
- continue: (noop)

We test four sets of data in increasing order of 'has-data-ness'

### `StringField` results

| value type   | URL encoded form data | `StringField(validators=[])` result |
| -            | -                     | -                                   |
| missing      | 'decsc='              | `None`                              |
| empty string | 'description='        | `''`                                |
| whitespace   | 'description=%20'     | `' '`                               |
| proper       | 'description=foo'     | `'foo'`                             |

### Requirement validators

| URL encoded form data | fail | `DataRequired` | `InputRequired` | `FieldRequired` | continue |
| -                     | -    | -              | -               | -               | -        |
| 'decsc='              | FS   | FS             | FS              | **FS**          | T        |
| 'description='        | FS   | FS             | FS              | **T**           | T        |
| 'description=%20'     | FS   | FS             | T               | **T**           | T        |
| 'description=foo'     | FS   | T              | T               | **T**           | T        |

Observe that for row 2 (`description=`), `InputRequired` is too strict and `continue` too permissive in distinguishing between `None` and `''`. Therefore `FieldRequired` sitting between them is necessary.

### Optional-ness validators

It also makes sense to talk about the optional family of validators at this point. They are somewhat equal-and-opposite to the required family of validators because of how they handle 'trivial data', that is data for which a validator raises StopValidation. The required family raise `FS` and the optional family raise `TS`. For non-trivial data both families return `T`, and any further validators then run.

Upon viewing the fuzzy truth table below, it becomes clear adding a `FieldOptional` validator also makes sense: for stopping validation early if a field is not present as `InputOptional` does, but not including the empty string in the set of values which escapes further validation.

| URL encoded form data | return | `DataOptional` | `InputOptional` | `FieldOptional` | continue |
| -                     | -      | -              | -               | -               | -        |
| 'decsc='              | TS     | TS             | TS              | TS              | T        |
| 'description='        | TS     | TS             | TS              | T               | T        |
| 'description=%20'     | TS     | TS             | T               | T               | T        |
| 'description=foo'     | TS     | T              | T               | T               | T        |

We already have the following in WTForms:

- `DataOptional` is `Optional(strip_whitespace = True)`
- `InputOptional` is `Optional(strip_whitespace = False)`

So again there is just one more validator `FieldOptional` to add.

## Remarks so far

`FieldRequired` vs `InputRequired` is the same distinction between `bash`'s `[ ! -v ]` and `[ ! -n ]` test operators.

So far we have talked about data validation for `StringField`, but there are other fields like `IntegerField` to consider. In particular `DataRequired` has a muddy history of how it treats false-y post-coercion data. I'll investigate these. I'm aware that `DataRequired` is discouraged overall.

## Related grievances

This section will probably be expanded into the Grievances folder until depleted.

I am a little concerned about `DataOptional`'s current implementation however, in allowing unlimited whitespace to be submitted as valid, escaping any further length checks. This is the validator one receives when calling `Optional()`, with its default kwarg of `strip_whitespace=True`. It seems DOS-worthy? I'll perhaps open a separate issue...

`Length` validator is broken when `min=0`: it permits a missing string

We want to avoid [null island](https://en.wikipedia.org/wiki/Null_Island): don't force `InputRequired` for non-string data, say for integers, lest one wrongfully stores 0 as a default.

We don't necessarily want to force users to make all data `FieldRequired`, eg a bunch of search parameters `title=&date-start=&date-end=&foo=&bar=&...`. Or perhaps we do, for watertight POSTs?

There is no base class for validators to inherit from. Some validators support a `message` parameter, but some (eg `Optional`) don't.

## Promoting usage

`FieldRequired` alone seems to be a best practice to promote to new users in quick-start documentation for `StringField`s.

Combining together `FieldRequired` and `InputOptional` is also powerful.

| URL encoded form data | `FieldRequired && InputOptional` |
| -                     | -                                |
| 'decsc='              | FS && TS = FS                    |
| 'description='        | T  && TS = TS                    |
| 'description=%20'     | T  && T  = T                     |
| 'description=foo'     | T  && T  = T                     |

The field must exist, even if empty, and empty strings escape further validation.

## Implementation

XXX this will change as I improve this repository.

We could just use `NoneOf(None)` to implement `FieldRequired`, but this is boring, and it seems clear to me there's an opportunity restructure validators into a hierarchy instead of continuing to throw more validators into that patchwork until everything is covered.

No-frills implementation:

```py
from wtforms.validators import StopValidation

class Validator:
    def __init__(self, error_message = None):
        self.error_message = error_message

    def __call__(self, form, field):
        pass

    def stop_validation(self, default_message = None):
        if default_message is None:
            message = None
        elif self.error_message is not None:
            message = self.error_message
        else:
            message = default_message

        raise StopValidation(message)

# XXX data vs raw data is a mess here for non-StringField

class FieldRequired(Validator):
    """
    Validates that the field exists, even if its data is empty

    eg in 'title=My%20Post&description=' both 'title' and 'description' exist,
    and thus pass this validator
    """
    def __call__(self, form, field):
        super().__call__(form, field)
        if not field.raw_data:
            self.stop_validation('This field must exist.')

class InputRequired(FieldRequired):
    """
    Validates that the field exists, and has data, even if only whitespace

    eg in 'title=My%20Post&description=', 'title' passes InputRequired,
    but 'description' does not
    """
    def __call__(self, form, field):
        super().__call__(form, field)
        if not field.raw_data[0]:
            self.stop_validation('This field is required.')

class DataRequired(InputRequired):
    """
    Validates that the field exists, and has data more than just whitespace
    """
    def __call__(self, form, field):
        super().__call__(form, field)
        if not isinstance(field.data, str):
            # DataRequired has a muddy history
            raise NotImplementedError
        # XXX at this point field.data is field.raw_data[0], with any filters applied
        if not field.data.strip():
            self.stop_validation('This field must be more than just whitespace.')
```
