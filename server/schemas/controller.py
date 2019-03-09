import time
from marshmallow import Schema, fields, validates, ValidationError

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
