import json
import logging
from flask import Flask, request, abort, jsonify
from schemas.game import MakeMoveInput, CreateGameInput
from schemas.controller import ControllerRegisterInput

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
    # example of return type. Possible that there is established standard
    # we will find out when incorporating an actual chess library
    return jsonify({"board": "kjdiIjfjekKojfjLKJfkj",
            "players": {
                "white": {
                    "id": "playerID1",
                    "time-remaining": "3496",
                    "moves": ["E3->D4", "D4->D5"]
                },
                "black": {
                    "id": "playerID2",
                    "time-remaining": "3496",
                    "moves": ["B3->C4", "C4->B5"]
                }
            }
           })

@app.route('/creategame', methods=["POST"])
def create_game():
    errors = CreateGameInput().validate(request.form)
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
