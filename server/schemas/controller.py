import time
from marshmallow import Schema, fields, validates, validates_schema, ValidationError

GAMES_COLLECTION = "games"
CONTROLLER_COLLECTION = "controllers"
TIMEOUT = 60 # seconds

class ControllerRegisterInput(Schema):
    board_id        = fields.String(required=True)
    board_version   = fields.String(required=True)

    def __init__(self, db):
        super().__init__()
        self.db = db

    @validates('board_id')
    def validate_controller_not_registered(self, value):
        controller_ref = self.db.collection(CONTROLLER_COLLECTION).document(value).get()
        if not controller_ref.exists:
            return

        last_seen = controller_ref.to_dict()['last_seen']

        # Allow controllers to re-register if they went down
        if time.time() - last_seen < TIMEOUT:
            raise ValidationError(f'Controller {value} already registered')

class ControllerPollInput(Schema):
    board_id = fields.String(required=True)
    ply_count = fields.Integer(required=True)
    error = fields.Integer() # could be None

    def __init__(self, db):
        super().__init__()
        self.db = db

    @validates('board_id')
    def validate_controller_registered(self, value):
        controller_ref = self.db.collection(CONTROLLER_COLLECTION).document(value).get()
        if not controller_ref.exists:
            raise ValidationError(f'Controller {value} not registered')

        last_seen = controller_ref.to_dict()['last_seen']

        if time.time() - last_seen > TIMEOUT:
            raise ValidationError('Time out exceeded, please re-register')

    @validates('ply_count')
    @validates('error')
    def validate_non_negative(self, value):
        if value < 0:
            raise ValidationError('Can not have negative ply_count or error')

    @validates_schema(skip_on_field_errors=True)
    def validate_ply_and_error_within_bounds(self, data):
        controller = self.db.collection(CONTROLLER_COLLECTION).document(data['board_id']).get().to_dict()

        game_id = controller['game_id']

        # if no game assigned, no bounds to check
        if game_id is None:
            return

        game = self.db.collection(GAMES_COLLECTION).document(game_id).get().to_dict()

        if data['ply_count'] > game['ply_count']:
            raise ValidationError('ply_count cannot be greater than the stored one for the game')

        error = data.get('error', 0)

        if error > data['ply_count']:
            raise ValidationError('error can not be greater than ply_count')
