from marshmallow import Schema, fields, validates, ValidationError

OPEN_SLOT = "OPEN"
AI = "AI"
USER_COLLECTION = "users"
GAMES_COLLECTION = "games"

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

    @validates('move')
    def validate_move(self, value):
        # TODO: Check move decodes properly
        # TODO: Check move is applicable to the board
        pass

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
        game_ref = self.db.collection(GAMES_COLLECTION).document(value).get()
        if not game_ref.exists:
            raise ValidationError('Game doesn\'t exist!')

    @validates('player_id')
    def player_exists(self, value):
        assert_player_exists(value, self.db)

    @validates('side')
    def validate_side(self, value):
        if value != 'w' and value != 'b':
            raise ValidationError('Expected side to be one of "w", "b".')
