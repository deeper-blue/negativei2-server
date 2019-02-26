from marshmallow import Schema, fields, validates, validates_schema, ValidationError
from server.game import Game

OPEN_SLOT = "OPEN"
AI = "AI"
USER_COLLECTION = "users"
GAME_COLLECTION = "games"

class MakeMoveInput(Schema):
    # This will come from Firebase
    user_id = fields.String(required=True)
    # The move to be made
    move = fields.String(required=True)
    # Identifier for the game to make the move on
    game_id = fields.String(required=True)

    def __init__(self, db):
        super().__init__()
        self.db = db

    @validates_schema
    def validate_move(self, data):
        # Validate 'game_id'
        game_ref = self.db.collection(GAME_COLLECTION).document(data['game_id']).get()
        if not game_ref.exists:
            raise ValidationError(f"Game {data['game_id']} doesn\'t exist!")

        # Create a game object for validation
        game = Game.from_dict(game_ref.to_dict())

        # Validate 'user_id'
        if data['user_id'] == OPEN_SLOT or data['user_id'] == AI:
            pass
        else:
            user_ref = self.db.collection(USER_COLLECTION).document(data['user_id']).get()
            if not user_ref.exists:
                raise ValidationError(f"User {data['user_id']} doesn\'t exist!")

        # Check if user is one of the players of the game
        if data['user_id'] not in game.players.values():
            raise ValidationError(f"User {data['user_id']} is not a player in this game.")

        # Check that it's the user's turn
        if data['user_id'] != game.players[game.turn]:
            raise ValidationError(f"User {data['user_id']} cannot move when it is not their turn.")

        # Validate 'move'
        try:
            # Check move is valid SAN and applicable to the board
            game.move(data['move'])
        except ValueError:
            raise ValidationError(f"Invalid move {data['move']} in current context.")
        except RuntimeError:
            # NOTE: This RuntimeError occurs if the game is over. There is another RuntimeError generated
            #   from game.move that can occur when the current side to play doesn't have an assigned player.
            #   But if this is the case, then the validation previously done for 'user_id' would have caught it.
            #   It might be worth creating our own error subclasses to clearly distinguish errors though.
            raise ValidationError(f"Game {data['game_id']} is over.")

class CreateGameInput(Schema):
    # ID of the user that creates the game
    creator_id = fields.String(required=True)
    # ID of the first player, or AI or open slot
    player1_id = fields.String(required=True)
    # ID of the second player, or AI or open slot
    player2_id = fields.String(required=True)
    # Time each player is given
    time_per_player = fields.Integer(required=True)
    # ID of the robot/board to play on. Reserved for future use
    board_id = fields.String(required=True)

    def __init__(self, db):
        super().__init__()
        self.db = db

    @validates('time_per_player')
    def validate_time(self, value):
        if value < 0:
            raise ValidationError('Cannot have negative time')

    @validates('player1_id')
    @validates('player2_id')
    def player_valid(self, value):
        if value == OPEN_SLOT or value == AI:
            return

        user_ref = self.db.collection(USER_COLLECTION).document(value).get()
        if not user_ref.exists:
            raise ValidationError(f'User {value} doesn\'t exist!')

    @validates('creator_id')
    def creator_exists(self, value):
        user_ref = self.db.collection(USER_COLLECTION).document(value).get()
        if not user_ref.exists:
            raise ValidationError('Creator doesn\'t exist!')
