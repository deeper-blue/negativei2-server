from marshmallow import Schema, fields, validates, ValidationError

OPEN_SLOT = "OPEN"
AI = "AI"
USER_COLLECTION = "users"

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

        user_ref = self.db.collection(USER_COLLECTION).document(value).get()
        if not user_ref.exists:
            raise ValidationError(f'User {value} doesn\'t exist!')

    @validates('creator_id')
    def creator_exists(self, value):
        user_ref = self.db.collection(USER_COLLECTION).document(value).get()
        if not user_ref.exists:
            raise ValidationError('Creator doesn\'t exist!')
