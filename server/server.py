import os
import json
import logging
from flask import Flask, request, abort, jsonify
from schemas.game import MakeMoveInput, CreateGameInput
from schemas.controller import ControllerRegisterInput
import google.cloud
from google.cloud import firestore

# because Heroku uses an ephemeral file system (https://devcenter.heroku.com/articles/active-storage-on-heroku)
# we need to write the key that is stored in FIREBASE_SERVICE_ACCOUNT_JSON to a file
# before we can pass it to firebase admin

# the below will error if you haven't set FIREBASE_SERVICE_ACCOUNT_JSON
raw_account = os.environ["FIREBASE_SERVICE_ACCOUNT_JSON"]

ACCOUNT_JSON_FILENAME = "firebase_account_cred.json"

with open(ACCOUNT_JSON_FILENAME, 'w') as account_file:
    account_file.write(raw_account)

# Initialising this on Travis breaks the test suite
if os.environ.get("CI", None) != "true":
    db = firestore.Client("assistive-chess-robot")
else:
    # reassigned by a mock object
    db = None

GAMES_COLLECTION = "games"

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

@app.route('/getgame/<game_id>')
def get_game(game_id):
    doc_ref = db.collection(GAMES_COLLECTION).document(game_id).get()
    if doc_ref.exists:
        return jsonify(doc_ref.to_dict())
    abort(BAD_REQUEST, "Document doesn't exist!")

@app.route('/creategame', methods=["POST"])
def create_game():
    errors = CreateGameInput(db).validate(request.form)
    if errors:
        abort(BAD_REQUEST, str(errors))
    return get_game(0)

@app.route('/controllerregister', methods=["POST"])
def register_controller():
    errors = ControllerRegisterInput().validate(request.form)
    if errors:
        abort(BAD_REQUEST, str(errors))
    return '0'

@app.route('/controllerpoll/<board_id>')
def controller_poll(board_id):
    return get_game(board_id)

if __name__ == "__main__":
    app.run(host='0.0.0.0')
else:
    gunicorn_logger = logging.getLogger('gunicorn.error')
    app.logger.handlers = gunicorn_logger.handlers
    app.logger.setLevel(gunicorn_logger.level)
