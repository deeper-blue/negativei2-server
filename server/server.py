import os
import json
import time
import logging
from flask import Flask, request, abort, jsonify
from flask_cors import CORS
from flask_socketio import SocketIO, join_room
from schemas.game import MakeMoveInput, CreateGameInput, JoinGameInput, DrawOfferInput, RespondOfferInput, ResignInput
from schemas.controller import ControllerRegisterInput, ControllerPollInput
from .game import Game
import google.cloud
from google.cloud import firestore
import firebase_admin
from firebase_admin import credentials

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
    # can't do this in a CI environment
    cred = credentials.Certificate(ACCOUNT_JSON_FILENAME)
    default_app = firebase_admin.initialize_app(cred)
else:
    # reassigned by a mock object
    db = None

GAMES_COLLECTION = "games"
CONTROLLER_COLLECTION = "controllers"
COUNTS_COLLECTION = "counts"

BAD_REQUEST = 400
REQUEST_OK = 'OK'

app = Flask(__name__)
CORS(app)
socketio = SocketIO(app)

@app.route('/')
def main():
    return 'hello world'

@app.route('/makemove', methods=["POST"])
def make_move():
    errors = MakeMoveInput(db).validate(request.form)
    if errors:
        abort(BAD_REQUEST, str(errors))

    # Get the game reference and construct a Game object
    game_ref = db.collection(GAMES_COLLECTION).document(request.form['game_id'])
    game = Game.from_dict(game_ref.get().to_dict())

    # Make the requested move on the game object
    game.move(request.form['move'])

    # Export the updated Game object to a dict
    game_dict = game.to_dict()

    # Write the updated Game dict to Firebase
    game_ref.set(game_dict)

    # update all clients
    socketio.emit("move", game_dict, room=game.id)

    return jsonify(game_dict)

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

    # Retrieve game ID count, increment it and cast it to a string.
    count_ref = db.collection(COUNTS_COLLECTION).document(GAMES_COLLECTION)
    count = str(int(count_ref.get().to_dict()['count']) + 1)

    # Create a new document reference with the incremented ID.
    doc_ref = db.collection(GAMES_COLLECTION).document(count)

    # Create a game from the validated schema and the incremented ID.
    game = Game.from_create_game_schema(request.form, doc_ref.id)

    # Write the game's dict to the document reference.
    # NOTE: `set` is used here rather than `create` in the event that
    #   the counts are somehow modified on Firebase. For example, if
    #   the count is somehow reset to 0, this will overwrite whatever
    #   game is stored with ID 0, instead of raising an error.
    doc_ref.set(game.to_dict())

    # Update the incremented ID count on the `/counts/games` document.
    # HACK: Firebase's `update` does not seem to work for this purpose,
    #   otherwise we could do `count_ref.update({'count': int(count)})`.
    game_count_document = count_ref.get().to_dict()
    game_count_document['count'] = int(count)
    count_ref.set(game_count_document)

    return get_game(doc_ref.id)

@app.route('/gamelist')
def game_list():
    query = db.collection(
        GAMES_COLLECTION).where('game_over.game_over', '==', False).where('free_slots', '>', 0)
    return jsonify([ref.to_dict() for ref in query.get()])

@app.route('/joingame', methods=["POST"])
def join_game():
    errors = JoinGameInput(db).validate(request.form)
    if errors:
        abort(BAD_REQUEST, str(errors))
    game_id     = request.form['game_id']
    player_id   = request.form['player_id']
    side        = request.form.get('side', None)

    game_ref    = db.collection(GAMES_COLLECTION).document(game_id)
    game_dict   = game_ref.get().to_dict()
    g           = Game.from_dict(game_dict)
    if side is None:
        if g.players['w'] is None:
            side = 'w'
        elif g.players['b'] is None:
            side = 'b'
        else:
            abort(BAD_REQUEST, 'No free side to join')
    try:
        g.add_player(player_id, side)
    except Exception as e:
        abort(BAD_REQUEST, str(e))
    game_ref.set(g.to_dict())
    return get_game(game_id)

@app.route('/controllerregister', methods=['POST'])
def register_controller():
    errors = ControllerRegisterInput(db).validate(request.form)
    if errors:
        abort(BAD_REQUEST, str(errors))
    controller_id = request.form['board_id']
    controller_ref = db.collection(CONTROLLER_COLLECTION).document(controller_id)

    controller_dict = {'game_id': None, 'last_ply_count': 0, **request.form}
    # avoid overwriting game_id
    if controller_ref.get().exists:
        controller_dict = controller_ref.get().to_dict()
    controller_dict['last_seen'] = time.time()

    controller_ref.set(controller_dict)
    return 'registered'

@app.route('/controllerpoll', methods=['POST'])
def controller_poll():
    errors = ControllerPollInput(db).validate(request.form)
    if errors:
        abort(BAD_REQUEST, str(errors))
    controller_id = request.form['board_id']
    controller_ref = db.collection(CONTROLLER_COLLECTION).document(controller_id)
    controller_dict = controller_ref.get().to_dict()

    game_id = controller_dict['game_id']
    error = int(request.form.get('error', -1))
    ply_count = int(request.form['ply_count'])

    # check if last_ply_count is less than current
    last_ply_count = controller_dict['last_ply_count']
    if last_ply_count < ply_count:
        # controller has finished a move
        socketio.emit('controller_finished', ply_count, room=game_id)

    # update controller document
    controller_dict['last_seen'] = time.time()
    controller_dict['last_ply_count'] = ply_count
    controller_ref.set(controller_dict)

    poll_response = {'game_over': {'game_over': False, 'reason': None}, 'history': []}

    if error != -1:
        # let web app know about error
        socketio.emit("controller_error", error, room=game_id)

    if game_id is not None and error == -1:
        game_dict = db.collection(GAMES_COLLECTION).document(game_id).get().to_dict()
        poll_response['game_over'] = game_dict['game_over']

        # game_dict['ply_count'] == len(history)
        for i in range(ply_count, game_dict['ply_count']):
            poll_response['history'].append(game_dict['history'][i])

    return jsonify(poll_response)

@socketio.on('register')
def register_for_game_updates(game_id):
    join_room(game_id)
    app.logger.info(f"Client joined {game_id}")

@app.route('/drawoffer', methods=["POST"])
def draw_offer():
    errors = DrawOfferInput(db).validate(request.form)
    if errors:
        abort(BAD_REQUEST, str(errors))

    # Get the game reference and construct a Game object
    game_ref = db.collection(GAMES_COLLECTION).document(request.form['game_id'])
    game = Game.from_dict(game_ref.get().to_dict())

    # Retrieve the player's side and make the offer
    players = {player: side for side, player in game.players.items()}
    side = players[request.form['user_id']]
    game.offer_draw(side=side)

    # Export the updated Game object to a dict
    game_dict = game.to_dict()

    # Write the updated Game dict to Firebase
    game_ref.set(game_dict)

    # Update all clients
    socketio.emit("drawOffer", request.form['user_id'], room=game.id)

    return jsonify(game_dict)

@app.route('/respondoffer', methods=["POST"])
def respond_to_draw_offer():
    errors = RespondOfferInput(db).validate(request.form)
    if errors:
        abort(BAD_REQUEST, str(errors))

    # Get the game reference and construct a Game object
    game_ref = db.collection(GAMES_COLLECTION).document(request.form['game_id'])
    game = Game.from_dict(game_ref.get().to_dict())

    # Retrieve the player's side
    players = {player: side for side, player in game.players.items()}
    side = players[request.form['user_id']]

    # Accept or decline the draw (depending on the response)
    if request.form['response'].lower() == 'true':
        game.accept_draw(side=side)
    else:
        game.decline_draw(side=side)

    # Export the updated Game object to a dict
    game_dict = game.to_dict()

    # Write the updated Game dict to Firebase
    game_ref.set(game_dict)

    # Update all clients
    id_draw_offers = {'id': request.form['user_id'], 'draws': game.draw_offers}
    socketio.emit("drawAnswer", id_draw_offers, room=game.id)

    return jsonify(game_dict)

@app.route('/resign', methods=["POST"])
def resign():
    errors = ResignInput(db).validate(request.form)
    if errors:
        abort(BAD_REQUEST, str(errors))

    # Get the game reference and construct a Game object
    game_ref = db.collection(GAMES_COLLECTION).document(request.form['game_id'])
    game = Game.from_dict(game_ref.get().to_dict())

    # Retrieve the player's side and make the resignation
    players = {player: side for side, player in game.players.items()}
    side = players[request.form['user_id']]
    game.resign(side=side)

    # Export the updated Game object to a dict
    game_dict = game.to_dict()

    # Write the updated Game dict to Firebase
    game_ref.set(game_dict)

    # Update all clients
    socketio.emit("forfeit", request.form['user_id'], room=game.id)

    return jsonify(game_dict)

if __name__ == "__main__":
    app.run(host='0.0.0.0')
else:
    gunicorn_logger = logging.getLogger('gunicorn.error')
    app.logger.handlers = gunicorn_logger.handlers
    app.logger.setLevel(gunicorn_logger.level)
