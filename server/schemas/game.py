from marshmallow import Schema, fields, validates, ValidationError

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
