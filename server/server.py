import json
from flask import Flask, request, abort
from schemas.game import MakeMoveInput

BAD_REQUEST = 400
REQUEST_OK = 'OK'

app = Flask(__name__)

@app.route('/')
def main():
    return 'hello world'

@app.route('/makemove', methods=["POST"])
def make_move():
    errors = MakeMoveInput().validate(request.form)
    if errors:
        abort(BAD_REQUEST, str(errors))
    return REQUEST_OK

if __name__ == "__main__":
    app.run(host='0.0.0.0')
