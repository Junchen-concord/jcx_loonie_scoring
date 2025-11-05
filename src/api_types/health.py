from marshmallow import Schema, fields


class HealthCheckResponse(Schema):
    status = fields.Int(description="HTTP status code")
    message = fields.Str(description="Health check message")
    modelVersion = fields.Str(description="Current model version")
