from marshmallow import Schema, fields, validates, validates_schema, ValidationError
from server.game import Game

OPEN_SLOT = "OPEN"
AI = "AI"
USER_COLLECTION = "users"
GAME_COLLECTION = "games"

def assert_player_exists(player, db):
    """Helper function that checks if a given player id exists in db"""
    user_ref = db.collection(USER_COLLECTION).document(player).get()
    if not user_ref.exists:
        raise ValidationError(f'User {player} doesn\'t exist!')

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

        # Check that game is not over
        if not game.in_progress:
            raise ValidationError(f"Game {data['game_id']} is over.")

        # Validate 'move'
        try:
            # Check move is valid SAN and applicable to the board
            game.move(data['move'])
        except ValueError:
            raise ValidationError(f"Invalid move {data['move']} in current context.")

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

        assert_player_exists(value, self.db)

    @validates('creator_id')
    def creator_exists(self, value):
        assert_player_exists(value, self.db)

class JoinGameInput(Schema):
    # ID of the game to join
    game_id = fields.String(required=True)
    # ID of the player to add
    player_id = fields.String(required=True)
    # side to join
    side = fields.String(required=False)

    def __init__(self, db):
        super().__init__()
        self.db = db

    @validates('game_id')
    def game_exists(self, value):
        game_ref = self.db.collection(GAME_COLLECTION).document(value).get()
        if not game_ref.exists:
            raise ValidationError('Game doesn\'t exist!')

    @validates('player_id')
    def player_exists(self, value):
        assert_player_exists(value, self.db)

    @validates('side')
    def validate_side(self, value):
        if value != 'w' and value != 'b':
            raise ValidationError('Expected side to be one of "w", "b".')

class DrawOfferInput(Schema):
    # The user making the draw offer
    user_id = fields.String(required=True)
    # Identifier for the game to make the move on
    game_id = fields.String(required=True)

    def __init__(self, db):
        super().__init__()
        self.db = db

    @validates_schema
    def validate_draw_offer(self, data):
        # Check if game exists
        game_ref = self.db.collection(GAME_COLLECTION).document(data['game_id']).get()
        if not game_ref.exists:
            raise ValidationError('Game doesn\'t exist!')

        # Create a game object for validation
        game = Game.from_dict(game_ref.to_dict())

        # Check if user exists
        assert_player_exists(data['user_id'], self.db)

        # Check if user is one of the players of the game
        if data['user_id'] not in game.players.values():
            raise ValidationError(f"User {data['user_id']} is not a player in this game.")

class RespondOfferInput(Schema):
    # The user making the draw offer
    user_id = fields.String(required=True)
    # Identifier for the game to make the move on
    game_id = fields.String(required=True)
    # Response to the draw offer
    # Accept -> True
    # Decline -> False
    response = fields.Boolean(required=True)

    def __init__(self, db):
        super().__init__()
        self.db = db

    @validates_schema
    def validate_offer_response(self, data):
        # Check if game exists
        game_ref = self.db.collection(GAME_COLLECTION).document(data['game_id']).get()
        if not game_ref.exists:
            raise ValidationError('Game doesn\'t exist!')

        # Create a game object for validation
        game = Game.from_dict(game_ref.to_dict())

        # Check if user exists
        assert_player_exists(data['user_id'], self.db)

        # Check if user is one of the players of the game
        if data['user_id'] not in game.players.values():
            raise ValidationError(f"User {data['user_id']} is not a player in this game.")