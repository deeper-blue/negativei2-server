from marshmallow import Schema, fields, validates, ValidationError

class ControllerRegisterInput(Schema):
    board_version = fields.String(required=True)
