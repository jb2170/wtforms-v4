from .legacyform import BaseForm, FormMeta, Form

# I'll be honest I don't know what is going on with the form metaclass FormMeta. Perhaps it's for some weird mro ordering amongst classes and superclasses, when the user inherits Form and defines their own. As I hubristic-ly rewrite my own Form class here from scratch, it should become clear whether the metaclass is necessary, or a Python 2 relic.

# XXX 2025/01/01
# I've just discovered in real time why the metaclass and base classes exist. (I'm editing SAOColors rn). If the methods of BaseForm existed in Form, then the FormMeta __init__ would mess with them thinking that they're fields.
