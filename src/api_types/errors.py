from marshmallow import Schema, fields


class HTTPErrorSchema(Schema):
    code = fields.Int(required=True, description="HTTP status code")
    name = fields.Str(required=True, description="Error name")
    description = fields.Str(required=True, description="Error description")


class BadRequestSchema(Schema):
    error = fields.Str(required=True, example="Bad Request")
    message = fields.Str(required=True, description="Exception message")
    detail = fields.Str(required=True, example="The request payload is not valid JSON or is missing required fields")


class GenericErrorSchema(Schema):
    error = fields.Str(required=True, example="Internal Server Error")
    message = fields.Str(required=True, description="Exception message")
