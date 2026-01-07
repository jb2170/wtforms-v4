from flask import Flask, request
import wtforms

class RootForm(wtforms.Form):
    name = wtforms.StringField("name", [
        wtforms.validators.Optional(strip_whitespace=True),
        wtforms.validators.Length(max=8)
    ])

app = Flask(__name__)

@app.route("/", methods=["POST"])
def index():
    form = RootForm(request.form)
    if form.validate():
        return f"Done, name={repr(form.name.data)}\n"
    else:
        return f"Failed {form.errors}\n"

# fail
# $ curl -sSL -d "name=$(head -c 16 /dev/zero | tr '\0' 'y')" localhost:8000

# success
# $ curl -sSL -d "name=$(head -c 16 /dev/zero | tr '\0' ' ')" localhost:8000
